import math

from sip.scoring import risk_ratio, score_themes, wilson

CB = {"addressability_scores": {"high": 1.0, "medium": 0.6, "low": 0.3},
      "themes": [{"id": "pay", "name": "Payment", "question": "stop", "addressability": "high"},
                 {"id": "switch", "name": "Switch", "question": "stop", "addressability": "high", "exclude_from_droppers": True},
                 {"id": "goal", "name": "Goal", "question": "start", "addressability": "low"}]}


def rec(i, status, themes, source="playstore"):
    return {"record_id": f"r{i}", "source": source, "sip_status": status, "sip_status_verified": True,
            "themes": [{"theme_id": t, "severity": 2, "confidence": 0.9, "verified": v} for t, v in themes]}


def test_wilson_known_value():
    p, lo, hi = wilson(5, 10)
    assert p == 0.5 and math.isclose(lo, 0.2366, abs_tol=1e-3) and math.isclose(hi, 0.7634, abs_tol=1e-3)
    assert wilson(0, 0) == (0.0, 0.0, 0.0)


def test_risk_ratio_and_zero_cell():
    rr, lo, hi = risk_ratio(10, 20, 5, 20)
    assert math.isclose(rr, 2.0) and lo < 2.0 < hi
    rr0, lo0, hi0 = risk_ratio(4, 10, 0, 10)  # zero cell -> continuity correction, finite
    assert math.isfinite(rr0) and rr0 > 1 and lo0 > 0


def fixture():
    rs = []
    for i in range(12):   # 12 droppers, 8 mention pay
        rs.append(rec(i, "stopped", [("pay", True)] if i < 8 else [], "playstore" if i % 2 else "youtube"))
    for i in range(12, 24):  # 12 continuers, 2 mention pay
        rs.append(rec(i, "continuing", [("pay", True)] if i < 14 else [("goal", True)]))
    rs.append(rec(24, "stopped", [("switch", True)]))   # switcher: not a dropper
    rs.append(rec(25, "stopped", [("pay", False)]))     # unverified span: not counted as a mention
    rs.append(rec(26, "unclear", [("pay", True)]))      # no status: counts as a mention, not in reach base
    return rs


def test_scoring_counts_and_groups():
    rows = {r["theme_id"]: r for r in score_themes(fixture(), CB, {"stopped", "paused"}, {"continuing"}, 5, 2)}
    pay = rows["pay"]
    assert pay["n_droppers"] == 13 and pay["n_continuers"] == 12     # switcher excluded, unverified-pay record kept as dropper
    assert pay["dropper_mentions"] == 8 and pay["continuer_mentions"] == 2
    assert pay["n_records"] == 11                                    # 8 + 2 + 1 unclear; unverified excluded
    assert math.isclose(pay["reach"], 10 / 25)
    assert math.isclose(pay["stop_lift"], (8 / 13) / (2 / 12))
    assert pay["eligible"] and pay["severity"] == 2


def test_eligibility_and_guard():
    rows = {r["theme_id"]: r for r in score_themes(fixture(), CB, {"stopped"}, {"continuing"}, 5, 2)}
    assert not rows["switch"]["eligible"] and "outcome" in rows["switch"]["excluded_reason"]
    assert not rows["goal"]["eligible"]                               # 10 records but one source
    assert "source" in rows["goal"]["excluded_reason"]
    small = score_themes(fixture()[:5] + fixture()[12:15], CB, {"stopped"}, {"continuing"}, 1, 1)
    assert all(r["lift_guarded"] and r["stop_lift"] == 1.0 for r in small)


def test_ranked_by_lower_bound():
    rows = score_themes(fixture(), CB, {"stopped"}, {"continuing"}, 1, 1)
    elig = [r for r in rows if r["eligible"]]
    assert elig == sorted(elig, key=lambda r: -r["priority_low"])


def test_contrast_only_never_ranked():
    cb = {**CB, "themes": CB["themes"] + [{"id": "disc", "name": "Discipline", "question": "behaviour",
                                             "addressability": "medium", "contrast_only": True}]}
    rs = fixture() + [rec(100 + i, "continuing", [("disc", True)], "youtube" if i % 2 else "playstore") for i in range(10)]
    row = {r["theme_id"]: r for r in score_themes(rs, cb, {"stopped"}, {"continuing"}, 1, 1)}["disc"]
    assert not row["eligible"] and row["contrast_only"] and "contrast" in row["excluded_reason"]
    assert row["continuer_mentions"] == 10
