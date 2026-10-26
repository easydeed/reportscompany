"""Root conftest.

`pytest_addoption` must live in the INITIAL conftest — the one at the rootdir
that `pytest.ini` establishes — so this cannot sit next to the test that uses
it. pytest rejects the hook in a non-initial conftest with "is not allowed in
non-initial conftest", which is a clear enough error, but the reason the file
is here rather than in apps/worker/tests is worth stating once.
"""


def pytest_addoption(parser):
    """--regen-contrast-baseline: rewrite pdf_contrast_baseline.txt after a fix.

    A flag rather than an environment variable, so it cannot be exported once
    in a shell and then quietly clear a real failure later in the session.
    """
    parser.addoption("--regen-contrast-baseline", action="store_true",
                     default=False,
                     help="rewrite apps/worker/tests/pdf_contrast_baseline.txt "
                          "from a fresh measurement (only after fixing something)")


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _no_live_market_fetch_in_property_renders(monkeypatch):
    """A property render in a test does not call SimplyRETS.

    Every theme defaults to the six-page set, which includes `market_trends`,
    so every render that did not pre-inject `market_trends_data` called the
    vendor's public demo API: about 1.2s each, which doubled the suite to
    thirteen minutes once harbor and linen joined atlas on that set — and a
    page whose content depends on whether a third party answered is not a
    fixture. Without this the dropped-page path is what most renders take
    anyway (no credentials), so stubbing it to None changes no outcome.

    Replaces only `PropertyReportBuilder._fetch_market_trends`. The
    computation in `worker.compute.market_trends` is untouched and its own
    tests call it directly. A test that wants the page passes
    `market_trends_data`, which skips the fetch entirely.
    """
    try:
        from worker.property_builder import PropertyReportBuilder
    except Exception:
        yield
        return
    monkeypatch.setattr(PropertyReportBuilder, "_fetch_market_trends", lambda self: None)
    yield
