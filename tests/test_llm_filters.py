from kuartal.llm import filters

def test_contains_advice_language_detects_buy_sell_hold():
    assert filters.contains_advice_language("Investors should buy this stock now.")
    assert filters.contains_advice_language("Analysts recommend holding the position.")
    assert filters.contains_advice_language("The target price was raised to 5000.")

def test_contains_advice_language_false_on_clean_text():
    text = (
        "BBRI's revenue grew 9% this quarter, below its own 15% average over "
        "the last four quarters, and around the 65th percentile of the "
        "banking sector this period."
    )
    assert not filters.contains_advice_language(text)

def test_contains_advice_language_is_word_bounded():
    # "household" should not trip the "hold" pattern
    assert not filters.contains_advice_language("Household spending rose this quarter.")

def test_sentence_count_basic():
    assert filters.sentence_count("One sentence.") == 1
    assert filters.sentence_count("One. Two! Three?") == 3
    assert filters.sentence_count("") == 0

def test_within_length_enforces_ceiling():
    long_text = "One. Two. Three. Four."
    assert not filters.within_length(long_text, max_sentences=3)
    assert filters.within_length("One. Two.", max_sentences=3)

def test_passes_all_checks_requires_both():
    assert filters.passes_all_checks("Revenue grew 9% this quarter, in line with its trend.")
    assert not filters.passes_all_checks("You should buy this stock, it grew 9% this quarter.")
    assert not filters.passes_all_checks("One. Two. Three. Four. Five sentences here to fail length.")
