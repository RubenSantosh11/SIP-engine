"""The evidence-span rule: retry once on a bad quote, then mark the value unverified."""
import s4_extract

CB = {"status": "seed", "themes": [{"id": "cash_flow", "name": "n", "definition": "d", "include": "i", "exclude": "e"}]}
REC = {"record_id": "r1", "source": "youtube", "context": None, "text": "I stopped my SIP after losing my job."}


def answer(span):
    return {"record_id": "r1", "source": "youtube", "sip_status": "stopped", "sip_status_evidence": "stopped my SIP",
            "first_time_investor": "unclear", "first_time_evidence": None,
            "themes": [{"theme_id": "cash_flow", "evidence_span": span, "severity": 3, "confidence": 0.9}],
            "one_line_reason": "Job loss."}


def run(monkeypatch, answers):
    calls = []

    def fake(model, prompt, system=None, key=None):
        calls.append(prompt)
        return answers[len(calls) - 1]
    monkeypatch.setattr(s4_extract, "llm_call", fake)
    return s4_extract.extract(REC, CB), calls


def test_good_span_single_call(monkeypatch):
    out, calls = run(monkeypatch, [answer("losing my job")])
    assert len(calls) == 1 and out["themes"][0]["verified"]


def test_bad_span_retried_then_fixed(monkeypatch):
    out, calls = run(monkeypatch, [answer("I lost my job"), answer("losing my job")])
    assert len(calls) == 2 and "not exact substrings" in calls[1]
    assert out["themes"][0]["verified"] and out["attempts"] == 2


def test_bad_span_twice_marked_unverified(monkeypatch):
    out, calls = run(monkeypatch, [answer("I lost my job"), answer("job was lost")])
    assert len(calls) == 2 and out["themes"][0]["verified"] is False


def test_unknown_theme_is_malformed(monkeypatch):
    bad = answer("losing my job")
    bad["themes"][0]["theme_id"] = "made_up"
    out, _ = run(monkeypatch, [bad, bad])
    assert out["status"] == "malformed"
