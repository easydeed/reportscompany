from api.routes.branding_tools import build_test_email


def test_closed_branding_sample_has_transaction_prices():
    _, html = build_test_email({}, "closed", unsubscribe_url="#")
    assert "1532 N Niagara St" in html
    assert html.count("$1.4M") >= 2
    assert "Price N/A" not in html
