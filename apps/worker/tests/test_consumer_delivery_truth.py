"""
The consumer delivery path must not record a delivery it did not make.

THE FAMILY (D-031, D-032, D-069, D-033)
---------------------------------------
This is D-061 / D-064 / D-065 again — "the record says delivered and it wasn't"
— on the path where the recipient is a stranger who typed their address into a
landing page. Four branches of one dispatch wrote `status='sent'`:

    RESEND_API_KEY unset        never attempted          D-031
    provider rejected it        attempted and refused     not filed — found here
    no usable delivery method   could not be attempted    D-032
    genuine success             actually sent             correct

Three of the four also wrote `consumer_email_sent_at`, a timestamp asserting
when an email that does not exist was sent. All three then fell through to
`if delivered:` and SMSed the AGENT that they had a new lead — so the agent
chased someone who had received nothing, and no row anywhere contradicted it.

WHY `failed` AND NOT A NEW STATUS
---------------------------------
#56 added `sending` to `email_log` because it needed to express a state that
did not exist: an attempt in flight. Here the state exists and the adjacent
path already uses it. A new value would only be a status no UI has seen —
which is the note both #56 and #61 had to write about themselves. What was
missing was never the vocabulary; it was the reason, which is now stored on
the row rather than left in a log line that rotates (D-064).

D-033 IS IN THIS BRANCH ON PURPOSE
----------------------------------
The same missing `RESEND_API_KEY` that causes D-031 also disables the alert
that would report it. Fixing the cause without the reporting leaves the fix
unverifiable in production: you cannot tell whether it worked, because the
thing that would tell you is the thing that is off.
"""
import ast
import re
from pathlib import Path

import pytest

WORKER = Path(__file__).resolve().parents[1] / "src" / "worker"
TASKS = (WORKER / "tasks.py").read_text()
TREE = ast.parse(TASKS)


def _fn(name):
    matches = [n for n in ast.walk(TREE)
               if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(matches) == 1, f"expected exactly one {name}(), found {len(matches)}"
    return matches[0]


def _src(name):
    return ast.get_source_segment(TASKS, _fn(name)) or ""


def _code_only(src: str) -> str:
    """
    The source with comments and docstrings removed.

    THIS HELPER EXISTS BECAUSE THE SAME MISTAKE HAPPENED THREE TIMES TODAY.
    When a fix documents the defect in place — which everything in this
    repository does — the comment explaining the bug contains the symptom
    string. A text search over that region then matches the explanation and
    reports the defect as present.

    It happened to the vendor-idiom test (matched three files' comments about
    comma-packed statuses), and twice in this file: "logger.warning" in the
    docstring that says the warning was all that used to survive, and
    "sms_result" in the comment explaining the NameError.

    The rule is narrow and general: **assert against the code, not the file.**
    `ast.unparse` drops comments; the docstring is the first statement of each
    function definition and is dropped explicitly.
    """
    tree = ast.parse(src.strip())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef, ast.Module)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return ast.unparse(tree)


CONSUMER = _src("process_consumer_report")


def _sent_writes(src):
    """Every statement in `src` that claims a consumer report was delivered."""
    return [
        " ".join(stmt.split())
        for node in ast.walk(ast.parse(src.strip()))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        for stmt in [node.value]
        if "consumer_reports" in stmt and "status = 'sent'" in stmt
    ]


# ── nothing claims a delivery it did not make ───────────────────────────────

def test_the_only_sent_writes_are_on_paths_that_actually_sent():
    """
    THE HEADLINE. Four branches wrote 'sent'; one of them had sent something.

    Asserted by counting the claims rather than by naming the branches that
    were wrong — a test keyed to "the RESEND_API_KEY branch" would not have
    noticed the provider-rejected branch, which is exactly what the original
    survey missed.
    """
    claims = _sent_writes(CONSUMER)
    assert len(claims) == 2, (
        f"expected exactly two 'sent' writes in process_consumer_report — the "
        f"SMS success path and the email success path — found {len(claims)}:\n"
        + "\n".join(f"  {c[:100]}" for c in claims)
    )


@pytest.mark.parametrize("marker,defect", [
    ("RESEND_API_KEY is not configured", "D-031"),
    ("the email provider did not accept", "the unfiled provider-rejected branch"),
    ("no usable delivery method", "D-032"),
])
def test_each_non_delivery_records_a_failure_with_its_own_reason(marker, defect):
    """
    "failed" alone sends whoever investigates back to the logs. The reason is
    the part that answers "why did this lead never get their report?", and it
    has to be on the row — D-064: a log line is not a record.
    """
    assert marker in CONSUMER, f"{defect}: no specific reason recorded"
    assert "_record_consumer_delivery_failure" in CONSUMER


def test_the_failure_recorder_writes_failed_and_keeps_the_reason():
    src = _src("_record_consumer_delivery_failure")
    assert "status = 'failed'" in src
    assert "error = %s" in src, "the reason is not persisted"
    assert "logger.error" in src, "a non-delivery is not surfaced in the logs either"


def test_no_branch_stamps_a_sent_timestamp_without_sending():
    """
    `consumer_email_sent_at` is evidence, not decoration: it asserts WHEN an
    email was sent. Three branches stamped it for emails that did not exist.
    """
    stamps = [
        " ".join(n.value.split())
        for n in ast.walk(ast.parse(CONSUMER.strip()))
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and "consumer_email_sent_at = NOW()" in n.value
    ]
    assert len(stamps) == 1, (
        f"expected one email-sent timestamp write (the success path), found "
        f"{len(stamps)}"
    )
    assert "status = 'sent'" in stamps[0], (
        "the email timestamp is written on a path that is not recording a send"
    )


# ── the redelivery guard (D-069) ────────────────────────────────────────────

def test_redelivery_is_refused_before_any_provider_is_called():
    """
    `acks_late` is worker-wide. Everything past this point is irreversible: a
    text to a member of the public, a credit spent, an agent told they have a
    lead. The guard has to precede all three or it is decoration.
    """
    fn = _fn("process_consumer_report")
    lines = {}
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if name in ("_consumer_already_delivered", "send_report_sms",
                        "send_agent_notification_sms"):
                lines.setdefault(name, []).append(node.lineno)

    assert "_consumer_already_delivered" in lines, "the redelivery guard is never consulted"
    guard = min(lines["_consumer_already_delivered"])
    for provider in ("send_report_sms", "send_agent_notification_sms"):
        assert provider in lines, f"{provider} is no longer called at all"
        assert guard < min(lines[provider]), (
            f"the guard (line {guard}) runs after {provider} "
            f"(line {min(lines[provider])})"
        )


def test_the_guard_reads_the_timestamps_not_only_the_status():
    """
    The timestamps are the columns that record an irreversible act. A row whose
    status was later changed but which carries `consumer_sms_sent_at` has still
    had a text sent to a real phone.
    """
    src = _src("_consumer_already_delivered")
    for column in ("consumer_sms_sent_at", "consumer_email_sent_at"):
        assert column in src, f"the guard ignores {column}"


def test_the_guard_does_not_block_a_retry_after_failure():
    """
    §0.6: a guard that refuses input is a guard that can refuse legitimate
    input. `failed` is the state a retry exists for — blocking on it would
    strand every lead whose first attempt broke.
    """
    src = _src("_consumer_already_delivered")
    assert "'failed'" not in src, (
        "the redelivery guard blocks on 'failed', so a report that failed once "
        "could never be retried"
    )


def test_a_refused_redelivery_does_not_report_failure():
    """
    From the caller's point of view the report HAS been delivered. Returning
    failure would record a failure for something already in someone's hands —
    the false negative this whole branch exists to remove.
    """
    head = CONSUMER[:CONSUMER.index("delivered = False")]
    assert "refusing redelivery" in head
    assert '"ok": True' in head, "a refused redelivery reports failure"


# ── D-033: the alert that reports the cause is disabled by the cause ────────

def test_a_suppressed_failure_notification_leaves_a_durable_record():
    """
    Returning early is the right shape — it never claimed to have sent. What
    was missing is that nothing survived the skip. This is the ONLY mechanism
    that tells an owner a scheduled report failed.
    """
    src = _src("_send_failure_notification")
    head = src[:src.index("resend_key")] + src[src.index("resend_key"):src.index("try:", src.index("resend_key"))]
    assert "INSERT INTO email_log" in src, (
        "a suppressed failure notification leaves nothing in email_log"
    )
    assert "'suppressed'" in src, "the suppression is not distinguishable by status"
    assert "RESEND_API_KEY not configured" in src, "the record does not say why"


def test_the_suppression_record_is_committed_independently():
    """D-065's reasoning: a record inside someone else's transaction can be
    rolled back, and then the suppression never happened as far as the table
    is concerned."""
    src = _src("_send_failure_notification")
    assert "_open_log_connection" in src


def test_the_suppression_is_logged_at_error_not_warning():
    """
    It was a `logger.warning` among many. The account owner has not been told
    their report failed — that is not a warning, and log levels are how anyone
    filtering production output decides what to look at.
    """
    code = _code_only(_src("_send_failure_notification"))
    suppression = code[:code.index("try:")]
    assert "logger.error" in suppression
    assert "logger.warning" not in suppression


def test_recording_the_suppression_cannot_itself_raise():
    """
    D-071, one file over: this runs inside `generate_report`'s failure handler.
    An exception escaping here used to reach the retry decorator and re-send
    the report.
    """
    code = _code_only(_src("_send_failure_notification"))
    suppression = code[:code.index("return\n", code.index("RESEND_API_KEY"))]
    assert "except Exception" in suppression, (
        "the suppression record is unguarded — it runs inside a failure handler"
    )


# ── the second bug hiding behind the first ──────────────────────────────────

def test_the_failure_return_does_not_reference_a_variable_from_another_branch():
    """
    `sms_result` is bound only inside the SMS branch. On the email and
    no-method paths the failure return raised NameError, which the outer
    handler caught and rewrote as a generic error — so a second, unrelated bug
    was hiding the reason for the first.
    """
    code = _code_only(CONSUMER)
    tail = code[code.index("if self.request.retries < self.max_retries"):]
    assert "sms_result" not in tail, (
        "the failure return still reads sms_result, which is unbound on the "
        "email and no-method paths"
    )


def test_the_generic_message_does_not_overwrite_a_specific_one():
    """
    The branches above record exactly why. This tail used to replace all of
    them with 'Delivery failed' — the one fact everyone already had.
    """
    assert "COALESCE(NULLIF(error, ''), %s)" in CONSUMER, (
        "the generic failure message overwrites the specific reason recorded "
        "by the branch that knew it"
    )
