"""`email_log.status`'s COMMENT names every value the code writes (D-083).

0027's comment listed four values; the code had come to write seven, and the
undocumented ones were non-deliveries — the distinction the comment exists to
answer. 0062 replaces it. This keeps the two in step: a status written in an
`email_log` statement that the newest COMMENT does not name fails here.
"""
import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MIGRATIONS = REPO / "db/migrations"

#: What the code writes today, each with its writer named in 0062's header.
WRITTEN = {"sending", "sent", "failed", "suppressed", "duplicate_suppressed",
           "blocked_unverified", "queued"}
#: Literals in those statements that are not statuses.
NOT_STATUSES = {"resend", "sendgrid"}


def _latest_comment() -> str:
    found = None
    for path in sorted(MIGRATIONS.glob("[0-9]*.sql")):
        for m in re.finditer(r"COMMENT ON COLUMN email_log\.status IS\s+((?:'[^']*'\s*)+);",
                             path.read_text(encoding="utf-8")):
            found = "".join(re.findall(r"'([^']*)'", m.group(1)))
    assert found, "no COMMENT on email_log.status in any migration"
    return found


def _literals_written_in_email_log_sql():
    seen = set()
    for root in ("apps/api/src", "apps/worker/src"):
        for path in (REPO / root).rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    sql = node.value
                    if re.search(r"(INSERT INTO|UPDATE)\s+email_log", sql):
                        seen |= set(re.findall(r"'([a-z_]+)'", sql))
    return seen - NOT_STATUSES


def test_the_newest_comment_names_every_status_written():
    comment = _latest_comment()
    missing = [s for s in sorted(WRITTEN) if not re.search(rf"\b{s}\b", comment)]
    assert not missing, f"email_log.status's COMMENT does not name {missing}"


def test_no_status_is_written_that_the_list_does_not_know():
    unknown = _literals_written_in_email_log_sql() - WRITTEN
    assert not unknown, (
        f"an email_log statement writes {sorted(unknown)}, which neither WRITTEN nor the "
        f"COMMENT names. Add it to both (a new migration for the COMMENT).")


def test_the_unverified_constant_is_the_documented_value():
    for path in ("apps/api/src/api/verification.py", "apps/worker/src/worker/schedules_tick.py"):
        assert 'BLOCKED_STATUS = "blocked_unverified"' in (REPO / path).read_text(encoding="utf-8"), path
