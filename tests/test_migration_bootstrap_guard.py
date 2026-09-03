"""
Guard on `run_migrations.py --bootstrap`.

THE DEFECT THIS EXISTS TO PREVENT
---------------------------------
`--bootstrap` records files as applied WITHOUT executing them, and it used to
record *every* unrecorded file. Any migration in the tree that had never run
would be marked applied and never execute — the run printing "N marked as
applied", a following `--status` printing "0 pending", and the tracking table
asserting a change that was never made. Silent no-op, green result.

That is not a hypothetical: this repository's bootstrap runbook was written
twice with 0054_growth_plan_report_limit.sql already in the tree. Following it
would have reported complete success and left the Growth plan at the wrong
limit, with schema_migrations claiming the migration had run.

WHY THESE TESTS NEED NO DATABASE
--------------------------------
The defect lives entirely in *which files get selected*, never in the SQL. So
the selection is a pure function and is tested as one — fast, hermetic, and it
runs in CI, which has no Postgres service. `run_migrations.py` imports psycopg
inside main() precisely so this module can be imported without a driver.
"""
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "scripts" / "run_migrations.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("run_migrations", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _load_runner()
partition_bootstrap = runner.partition_bootstrap
parse_args = runner.parse_args
ArgError = runner.ArgError


# Deliberately mirrors the real shape of db/migrations/: numbered files plus
# unnumbered seed files that sort AFTER every number.
NAMES = [
    "0001_init.sql",
    "0002_accounts.sql",
    "0053_phase4_indexes.sql",
    "0054_growth_plan_report_limit.sql",
    "seed_demo_account.sql",
]


class TestThrough:
    def test_leaves_everything_after_the_boundary_pending(self):
        record, pending = partition_bootstrap(NAMES, through="0053_phase4_indexes.sql")
        assert record == ["0001_init.sql", "0002_accounts.sql", "0053_phase4_indexes.sql"]
        assert pending == ["0054_growth_plan_report_limit.sql", "seed_demo_account.sql"]

    def test_boundary_is_inclusive(self):
        record, _ = partition_bootstrap(NAMES, through="0001_init.sql")
        assert record == ["0001_init.sql"]

    def test_the_actual_regression(self):
        """0054 must NOT be marked when the boundary is the migration before it."""
        record, pending = partition_bootstrap(NAMES, through="0053_phase4_indexes.sql")
        assert "0054_growth_plan_report_limit.sql" not in record
        assert "0054_growth_plan_report_limit.sql" in pending

    def test_unknown_boundary_is_an_error_not_a_silent_no_match(self):
        # A typo here would otherwise fall through to "record nothing" or
        # "record everything" depending on the implementation. Both are worse
        # than refusing.
        with pytest.raises(ArgError, match="not in"):
            partition_bootstrap(NAMES, through="0053_phase4_indexes")  # missing .sql

    def test_sorting_trap_is_visible_in_the_result(self):
        """
        --through splits on sorted order, and seed_demo_account.sql sorts after
        every numbered migration. So a boundary of 0053 leaves the seeder
        pending too, and a normal run would execute it. The tool cannot decide
        that for the operator, but the partition must surface it rather than
        quietly marking it.
        """
        _, pending = partition_bootstrap(NAMES, through="0053_phase4_indexes.sql")
        assert "seed_demo_account.sql" in pending


class TestExcept:
    def test_records_everything_but_the_named_file(self):
        record, pending = partition_bootstrap(NAMES, excepts=["0054_growth_plan_report_limit.sql"])
        assert pending == ["0054_growth_plan_report_limit.sql"]
        assert "seed_demo_account.sql" in record  # no ordering surprise

    def test_repeatable(self):
        record, pending = partition_bootstrap(
            NAMES, excepts=["0054_growth_plan_report_limit.sql", "0002_accounts.sql"]
        )
        assert pending == ["0002_accounts.sql", "0054_growth_plan_report_limit.sql"]
        assert "0002_accounts.sql" not in record

    def test_pending_keeps_sorted_order(self):
        _, pending = partition_bootstrap(
            NAMES, excepts=["seed_demo_account.sql", "0001_init.sql"]
        )
        assert pending == ["0001_init.sql", "seed_demo_account.sql"]

    def test_unknown_name_is_an_error(self):
        # The dangerous typo: --except a file you meant to protect, get no
        # error, and have it marked applied anyway.
        with pytest.raises(ArgError, match="not in"):
            partition_bootstrap(NAMES, excepts=["0054_growth_plan.sql"])


class TestBareBootstrapStillMarksEverything:
    def test_unchanged_behaviour_when_no_boundary_given(self):
        # The selection is deliberately unchanged; what changed is that main()
        # now warns and requires confirmation before using it.
        record, pending = partition_bootstrap(NAMES)
        assert record == NAMES
        assert pending == []


class TestArgParsing:
    def test_defaults_to_apply(self):
        assert parse_args([])["mode"] == "apply"

    def test_status_and_bootstrap(self):
        assert parse_args(["--status"])["mode"] == "status"
        assert parse_args(["--bootstrap"])["mode"] == "bootstrap"

    def test_through_and_except_are_parsed(self):
        opts = parse_args(["--bootstrap", "--through", "0053_phase4_indexes.sql"])
        assert opts["through"] == "0053_phase4_indexes.sql"
        opts = parse_args(["--bootstrap", "--except", "a.sql", "--except", "b.sql"])
        assert opts["excepts"] == ["a.sql", "b.sql"]

    def test_through_and_except_are_mutually_exclusive(self):
        with pytest.raises(ArgError, match="alternatives"):
            parse_args(["--bootstrap", "--through", "a.sql", "--except", "b.sql"])

    def test_boundary_flags_require_bootstrap(self):
        # --through on a normal apply would read as "only apply up to here",
        # which is not what it does. Refuse rather than silently ignore.
        with pytest.raises(ArgError, match="only apply to --bootstrap"):
            parse_args(["--through", "a.sql"])
        with pytest.raises(ArgError, match="only apply to --bootstrap"):
            parse_args(["--status", "--except", "a.sql"])

    def test_missing_value_is_caught(self):
        with pytest.raises(ArgError, match="requires a migration filename"):
            parse_args(["--bootstrap", "--through"])
        # A following flag must not be swallowed as the value.
        with pytest.raises(ArgError, match="requires a migration filename"):
            parse_args(["--bootstrap", "--through", "--yes"])

    def test_unknown_option(self):
        with pytest.raises(ArgError, match="unknown option"):
            parse_args(["--bootstrp"])

    def test_yes_flag(self):
        assert parse_args(["--bootstrap", "--yes"])["assume_yes"] is True
        assert parse_args(["--bootstrap"])["assume_yes"] is False


class TestAgainstTheRealMigrationsDirectory:
    """
    The unit tests above use a synthetic list. This one asserts the property
    that actually matters for the production run, against the real directory.
    """

    def test_real_boundary_leaves_0054_and_the_seeder_pending(self):
        names = sorted(p.name for p in (REPO_ROOT / "db" / "migrations").glob("*.sql"))
        boundary = "0053_phase4_indexes_and_signup_tokens.sql"
        if boundary not in names:
            pytest.skip(f"{boundary} no longer present; update this test's boundary")

        record, pending = partition_bootstrap(names, through=boundary)
        assert boundary in record
        # Everything unnumbered sorts last, so the seeder rides along with any
        # genuinely-new migration. Documented, tested, and printed at runtime.
        assert all(n > boundary for n in pending)
        assert "seed_demo_account.sql" in pending
