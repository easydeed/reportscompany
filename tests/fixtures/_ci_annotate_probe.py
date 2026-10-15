"""A test that fails on purpose, for the positive control in
`tests/test_ci_annotate_failures.py`.

NOT COLLECTED BY THE SUITE: the filename starts with `_`, so
`pytest.ini`'s `python_files = test_*.py` does not match it. It is run by
explicit path from that one test, which is the only way a deliberately failing
test can live in a repository whose suite must be green.
"""


def test_this_fails():
    assert 1 == 2, "this test exists to fail"
