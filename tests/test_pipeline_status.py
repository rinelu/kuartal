from kuartal.pipeline import status


def test_get_defaults_to_all_pending_for_unknown_ticker():
    result = status.get("UNKNOWN_TICKER_XYZ")
    assert result["ticker"] == "UNKNOWN_TICKER_XYZ"
    assert all(step["status"] == "pending" for step in result["steps"])
    assert [s["name"] for s in result["steps"]] == status.STEP_NAMES


def test_reset_then_mark_updates_individual_steps():
    status.reset("BBRI")
    status.mark("BBRI", "report detected", "done")
    status.mark("BBRI", "history read", "in_progress")

    result = status.get("BBRI")
    by_name = {s["name"]: s["status"] for s in result["steps"]}
    assert by_name["report detected"] == "done"
    assert by_name["history read"] == "in_progress"
    assert by_name["sector ranked"] == "pending"
    assert by_name["verdict generated"] == "pending"


def test_reset_clears_previous_run_state():
    status.mark("BBCA", "verdict generated", "done")
    status.reset("BBCA")

    result = status.get("BBCA")
    assert all(step["status"] == "pending" for step in result["steps"])


def test_mark_without_prior_reset_still_works():
    status.mark("BMRI", "sector ranked", "failed")
    result = status.get("BMRI")
    by_name = {s["name"]: s["status"] for s in result["steps"]}
    assert by_name["sector ranked"] == "failed"
