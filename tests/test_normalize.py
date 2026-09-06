from kuartal.sectors import normalize


def test_normalize_ticker_strips_suffix_and_uppercases():
    assert normalize.normalize_ticker("bbri.jk") == "BBRI"
    assert normalize.normalize_ticker(" BBCA ") == "BBCA"


def test_normalize_quarter_label_variants():
    assert normalize.normalize_quarter_label("2025Q1") == "Q1'25"
    assert normalize.normalize_quarter_label("Q1 2025") == "Q1'25"
    assert normalize.normalize_quarter_label("Q1'25") == "Q1'25"


def test_normalize_financial_entry_maps_alternate_field_names():
    entry = {"period": "2025Q1", "total_revenue": "1,250.5", "net_income": 300, "net_margin": "24.0"}
    normalized = normalize.normalize_financial_entry(entry)

    assert normalized == {"q": "Q1'25", "revenue": 1250.5, "earnings": 300.0, "margin": 24.0}


def test_normalize_financial_entry_handles_missing_margin():
    entry = {"q": "Q2'25", "revenue": 100, "earnings": 20}
    normalized = normalize.normalize_financial_entry(entry)

    assert normalized["margin"] is None


def test_normalize_financials_is_order_preserving():
    entries = [{"q": "Q1'25", "revenue": 1, "earnings": 1}, {"q": "Q2'25", "revenue": 2, "earnings": 2}]
    normalized = normalize.normalize_financials(entries)

    assert [e["q"] for e in normalized] == ["Q1'25", "Q2'25"]


def test_normalize_growth_entry_maps_alternate_field_names():
    entry = {"symbol": "bbca.jk", "revenue_growth": "0.12"}
    normalized = normalize.normalize_growth_entry(entry)

    assert normalized == {"ticker": "BBCA", "growth": 0.12}


def test_normalize_growth_rankings_list():
    entries = [{"ticker": "BBRI", "growth": 0.1}, {"ticker": "bbtn", "growth": 0.05}]
    normalized = normalize.normalize_growth_rankings(entries)

    assert [e["ticker"] for e in normalized] == ["BBRI", "BBTN"]


def test_normalize_price_entry_maps_alternate_field_names():
    entry = {"day": "2025-01-02", "closing_price": "4,520.5"}
    normalized = normalize.normalize_price_entry(entry)

    assert normalized == {"date": "2025-01-02", "close": 4520.5}


def test_normalize_daily_prices_is_order_preserving():
    entries = [{"date": "2025-01-01", "close": 100}, {"date": "2025-01-02", "close": 101}]
    normalized = normalize.normalize_daily_prices(entries)

    assert [e["date"] for e in normalized] == ["2025-01-01", "2025-01-02"]
