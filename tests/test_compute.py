from kuartal.pipeline import compute

FINANCIALS: list[compute.QuarterFinancial] = [
    {"q": "Q1'24", "revenue": 100, "earnings": 30, "margin": 30.0},
    {"q": "Q2'24", "revenue": 105, "earnings": 31, "margin": 29.5},
    {"q": "Q3'24", "revenue": 108, "earnings": 33, "margin": 30.5},
    {"q": "Q4'24", "revenue": 112, "earnings": 35, "margin": 31.2},
    {"q": "Q1'25", "revenue": 115, "earnings": 36, "margin": 31.3},
    {"q": "Q2'25", "revenue": 118, "earnings": 37, "margin": 31.4},
]

def test_yoy_growth():
    # Q2'25 (118) vs Q2'24 (105)
    assert compute.yoy_growth(FINANCIALS) == round((118 - 105) / 105, 4)

def test_own_avg_growth_4q_returns_none_without_enough_history():
    assert compute.own_avg_growth_4q(FINANCIALS[:3]) is None

def test_sector_percentile_ranks_correctly():
    percentile, peer_count = compute.sector_percentile(0.10, [0.05, 0.08, 0.12, 0.02])
    assert peer_count == 4
    assert 0 <= percentile <= 100

def test_sector_percentile_no_peers():
    percentile, peer_count = compute.sector_percentile(0.10, [])
    assert percentile == 50
    assert peer_count == 0

def test_direction_above_below_inline():
    assert compute.direction(0.20, 0.10) == "above"
    assert compute.direction(0.01, 0.10) == "below"
    assert compute.direction(0.10, 0.11) == "inline"

def test_own_trend_trims_to_n_quarters():
    trend = compute.own_trend(FINANCIALS, n_quarters=3)
    assert len(trend) == 3
    assert trend[0]["q"] == "Q4'24"
