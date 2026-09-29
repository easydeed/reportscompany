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
