"""Stage 5 scoring: pure, deterministic functions (no LLM). See README "Scoring" for the method.

Intervals:
- reach (a proportion): Wilson score interval, which behaves well for small n and proportions near 0.
- stop-lift (risk ratio P(theme | dropper) / P(theme | continuer)): Katz log interval, with a 0.5
  continuity correction when any cell is 0.
Ranking uses a conservative lower bound: reach_low x mean severity x lift_low x addressability.
"""
import math

Z = 1.96  # 95%


def wilson(k: int, n: int, z: float = Z) -> tuple[float, float, float]:
    """Proportion k/n with its Wilson interval -> (p, low, high)."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def risk_ratio(a: int, n1: int, c: int, n2: int, z: float = Z) -> tuple[float, float, float]:
    """RR = (a/n1)/(c/n2) with Katz log interval -> (rr, low, high). 0.5 added to cells if any is 0."""
    b, d = n1 - a, n2 - c
    if min(a, b, c, d) == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
        n1, n2 = a + b, c + d
    rr = (a / n1) / (c / n2)
    se = math.sqrt(1 / a - 1 / n1 + 1 / c - 1 / n2)
    return rr, math.exp(math.log(rr) - z * se), math.exp(math.log(rr) + z * se)


def score_themes(records: list[dict], codebook: dict, droppers: set, continuers: set,
                 min_records: int, min_sources: int, min_group: int = 10, min_mentions: int = 5) -> list[dict]:
    """records: extraction dicts with status 'ok'. Returns one row per codebook theme.

    - A record "mentions" a theme only through a VERIFIED evidence span.
    - Dropper / continuer groups come from sip_status. Records whose only stop-theme is marked
      exclude_from_droppers (e.g. switching to a direct plan) are left out of the dropper group.
    - reach = share of records with a dropper or continuer status that mention the theme.
    - Themes marked contrast_only (protective factors) are scored for the contrast table but never ranked.
    - Small-sample guard for stop-lift: if either group has < min_group records or the theme has
      < min_mentions mentions across the two groups, lift is set to 1.0 (neutral) and flagged.
    """
    themes = {t["id"]: t for t in codebook["themes"]}
    addr_map = codebook["addressability_scores"]
    excluded = {t["id"] for t in codebook["themes"] if t.get("exclude_from_droppers")}
    stop_ids = {t["id"] for t in codebook["themes"] if t.get("question") == "stop"}

    def hits(r):
        return {t["theme_id"] for t in r["themes"] if t.get("verified")}

    def group(r):
        if r["sip_status"] in droppers and r.get("sip_status_verified", True):
            stops = hits(r) & stop_ids
            if stops and stops <= excluded:
                return None  # a switcher, not a real dropper
            return "dropper"
        if r["sip_status"] in continuers and r.get("sip_status_verified", True):
            return "continuer"
        return None

    grouped = [(r, group(r)) for r in records]
    n_drop = sum(g == "dropper" for _, g in grouped)
    n_cont = sum(g == "continuer" for _, g in grouped)
    base = [(r, g) for r, g in grouped if g]

    rows = []
    for tid, t in themes.items():
        mentioning = [r for r in records if tid in hits(r)]
        sev = [h["severity"] for r in mentioning for h in r["themes"] if h["theme_id"] == tid and h.get("verified")]
        k = sum(tid in hits(r) for r, _ in base)
        reach, reach_lo, reach_hi = wilson(k, len(base))
        a = sum(tid in hits(r) for r, g in base if g == "dropper")
        c = sum(tid in hits(r) for r, g in base if g == "continuer")
        guarded = n_drop < min_group or n_cont < min_group or (a + c) < min_mentions
        lift, lift_lo, lift_hi = (1.0, 1.0, 1.0) if guarded else risk_ratio(a, n_drop, c, n_cont)
        severity = sum(sev) / len(sev) if sev else 0.0
        addr = addr_map[t["addressability"]]
        sources = sorted({r["source"] for r in mentioning})
        contrast_only = bool(t.get("contrast_only"))
        eligible = not contrast_only and len(mentioning) >= min_records and len(sources) >= min_sources
        if contrast_only:
            reason = "contrast only (protective factor, not an opportunity)"
        elif len(mentioning) < min_records:
            reason = f"only {len(mentioning)} records (< {min_records})"
        elif len(sources) < min_sources:
            reason = f"only {len(sources)} source(s) (< {min_sources})"
        else:
            reason = None
        rows.append({
            "theme_id": tid, "name": t["name"], "question": t.get("question"),
            "n_records": len(mentioning), "sources": sources,
            "reach": reach, "reach_low": reach_lo, "reach_high": reach_hi,
            "severity": severity,
            "dropper_mentions": a, "n_droppers": n_drop, "continuer_mentions": c, "n_continuers": n_cont,
            "stop_lift": lift, "stop_lift_low": lift_lo, "stop_lift_high": lift_hi, "lift_guarded": guarded,
            "addressability": t["addressability"], "addressability_score": addr,
            "priority": reach * severity * lift * addr,
            "priority_low": reach_lo * severity * lift_lo * addr,
            "eligible": eligible, "excluded_reason": reason, "contrast_only": contrast_only,
        })
    rows.sort(key=lambda r: (not r["eligible"], -r["priority_low"], -r["n_records"]))
    return rows
