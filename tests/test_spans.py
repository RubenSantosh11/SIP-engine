from sip.spans import span_in_text

SRC = "I stopped my  SIP in March\nbecause the market CRASHED."


def test_exact_match():
    assert span_in_text("stopped my SIP", SRC)


def test_whitespace_and_case_normalised():
    assert span_in_text("in march because the market crashed", SRC)


def test_paraphrase_rejected():
    assert not span_in_text("I paused my SIP", SRC)


def test_empty_rejected():
    assert not span_in_text("", SRC)
    assert not span_in_text(None, SRC)
