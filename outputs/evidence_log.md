# AI Evidence Log: SIP Discovery Engine

## 1. Sources and volume analysed

| Source | Raw records | Relevant | Notes |
|---|---|---|---|
| Google Play | 22,004 | 411 | groww 3,974, fundsindia 3,241, etmoney 3,235, coin 2,942, upstox 2,519, indmoney 2,300, paytmmoney 1,970, angelone 1,823 |
| Apple App Store | 3,165 | 48 | kuvera 500, paytmmoney 499, angelone 489, indmoney 482, upstox 476, groww 469, etmoney 250 |
| YouTube comments | 1,873 | 120 |  |
| TradingQ&A forum | 465 | 40 |  |
| ValuePickr forum | 238 | 7 |  |
| **Total** | **27,745** | **626** | |

Pipeline: collect (public data, usernames stored only as hashes) -> keyword filter -> relevance check in batches of 10 -> open coding of 100 records -> codebook curated by the PM -> structured extraction of every relevant record with verbatim evidence -> scoring in Python.

## 2. Golden set

20 records drawn at random before extraction (fixed seed), stratified across sources and apps, excluding any record whose engine output the PM had already seen. The PM labelled them by hand without seeing engine output.

Evidence-span check: 1182 coded values, 0 failures, pass rate 100%.

Agreement with the PM's hand labels on 20 records:

| Field | Pipeline engine (Claude, session) | Deployed model (Gemini Flash) |
|---|---|---|
| SIP status | 11/20 (55%) | 12/20 (60%) |
| First-time investor | 11/20 (55%) | 11/20 (55%) |
| Time since starting | 2/7 (29%) | 2/7 (29%) |
| Severity within ±1 | 12/12 (100%) | 12/14 (86%) |
| Theme precision (engine themes the PM also chose) | 55% | 56% |
| Theme recall (PM themes the engine also chose) | 52% | 61% |
| Records whose theme sets overlap | 11/20 | 12/20 |

Where the pipeline engine disagreed, by likely cause:

| Likely cause | Disagreements |
|---|---|
| engine stricter: only codes what the text states | 9 |
| engine stricter: status implied, not stated | 7 |
| codebook boundary: payment failure vs app processing error | 6 |
| codebook boundary: early confusion vs advice / expectations | 5 |
| engine missed or did not infer a stated period | 4 |
| engine missed it | 3 |
| codebook boundary: support vs app error | 2 |
| codebook boundary: switching vs platform-initiated | 2 |
| engine over-coded | 2 |
| label outside the scheme | 1 |
| different reading of status | 1 |
| different period from the same text | 1 |

Every disagreement:

| Record | Field | PM label | Engine | Likely cause |
|---|---|---|---|---|
| playstore_dac9d146993c | sip_status | stopped | unclear | engine stricter: status implied, not stated |
| playstore_dac9d146993c | theme:app_reliability_errors | True | False | engine missed it |
| playstore_3fa49f13b810 | sip_status | stopped | unclear | engine stricter: status implied, not stated |
| playstore_3fa49f13b810 | theme:payment_autopay_failure | True | False | codebook boundary: payment failure vs app processing error |
| playstore_3fa49f13b810 | theme:app_reliability_errors | False | True | codebook boundary: payment failure vs app processing error |
| playstore_521ffa4138b8 | sip_status | stopped | unclear | engine stricter: status implied, not stated |
| playstore_3018feafae4f | sip_status | continuing | unclear | engine stricter: status implied, not stated |
| playstore_3018feafae4f | first_time_investor | no | unclear | engine stricter: only codes what the text states |
| playstore_3018feafae4f | time_since_start | >12m | unclear | engine missed or did not infer a stated period |
| playstore_98377bef9d3d | first_time_investor | no | unclear | engine stricter: only codes what the text states |
| playstore_98377bef9d3d | time_since_start | 1-6m | unclear | engine missed or did not infer a stated period |
| playstore_98377bef9d3d | theme:app_reliability_errors | False | True | codebook boundary: support vs app error |
| playstore_98377bef9d3d | theme:support_trust_breakdown | True | False | codebook boundary: support vs app error |
| playstore_45ddb6e83981 | theme:payment_autopay_failure | True | False | codebook boundary: payment failure vs app processing error |
| playstore_45ddb6e83981 | theme:app_reliability_errors | False | True | codebook boundary: payment failure vs app processing error |
| appstore_b36952b0e8cd | first_time_investor | no | unclear | engine stricter: only codes what the text states |
| appstore_b36952b0e8cd | time_since_start | <1m | unclear | engine missed or did not infer a stated period |
| appstore_b36952b0e8cd | theme:payment_autopay_failure | True | False | codebook boundary: payment failure vs app processing error |
| appstore_b36952b0e8cd | theme:app_reliability_errors | False | True | codebook boundary: payment failure vs app processing error |
| appstore_5c863a2d7879 | sip_status | paused | unclear | engine stricter: status implied, not stated |
| youtube_ea59eafe4316 | theme:early_confusion_first_months | True | False | codebook boundary: early confusion vs advice / expectations |
| youtube_ea59eafe4316 | theme:conflicting_advice | False | True | codebook boundary: early confusion vs advice / expectations |
| youtube_dda8c52fbbc4 | first_time_investor | no | unclear | engine stricter: only codes what the text states |
| youtube_dda8c52fbbc4 | time_since_start | >12m | unclear | engine missed or did not infer a stated period |
| youtube_dda8c52fbbc4 | theme:early_confusion_first_months | True | False | engine missed it |
| youtube_3be707d4fe44 | sip_status | starting | unclear | label outside the scheme |
| youtube_3be707d4fe44 | first_time_investor | yes | unclear | engine stricter: only codes what the text states |
| youtube_3be707d4fe44 | theme:early_confusion_first_months | True | False | codebook boundary: early confusion vs advice / expectations |
| youtube_3be707d4fe44 | theme:return_expectations | False | True | codebook boundary: early confusion vs advice / expectations |
| youtube_2de4d2bdeab0 | sip_status | paused | unclear | engine stricter: status implied, not stated |
| youtube_2de4d2bdeab0 | first_time_investor | yes | unclear | engine stricter: only codes what the text states |
| youtube_2de4d2bdeab0 | theme:early_confusion_first_months | True | False | codebook boundary: early confusion vs advice / expectations |
| youtube_843555b54ba8 | first_time_investor | no | unclear | engine stricter: only codes what the text states |
| tradingqna_4e72cc7b3d19 | first_time_investor | no | unclear | engine stricter: only codes what the text states |
| tradingqna_4e72cc7b3d19 | theme:platform_or_fund_initiated | False | True | codebook boundary: switching vs platform-initiated |
| tradingqna_4e72cc7b3d19 | theme:switching_plan_or_platform | True | False | codebook boundary: switching vs platform-initiated |
| tradingqna_ae3ce10612b0 | sip_status | unclear | stopped | different reading of status |
| tradingqna_ae3ce10612b0 | theme:platform_or_fund_initiated | False | True | engine over-coded |
| tradingqna_a6b91692c576 | sip_status | continuing | unclear | engine stricter: status implied, not stated |
| tradingqna_a6b91692c576 | first_time_investor | no | unclear | engine stricter: only codes what the text states |
| valuepickr_ab8c8ea6814d | time_since_start | 1-6m | 6-12m | different period from the same text |
| valuepickr_ab8c8ea6814d | theme:conflicting_advice | True | False | engine missed it |
| valuepickr_ab8c8ea6814d | theme:long_term_discipline | False | True | engine over-coded |

## 3. Where AI output was rejected or corrected

| Date | Stage | What the AI said | What changed | Why |
|---|---|---|---|---|
| 2026-11-02 | 3 (codebook) | Example quote for `missing_sip_controls` was "no option to stop a sip without redeeming" | Replaced with "Cannot pause the sip in the App" (FundsIndia, Play Store) | The original quote was cut out of context. Without explaining that 'stopping' means ending future instalments while 'redeeming' means selling units, it read as nonsensical. An example has to be clear without the full review. |
| 2026-11-02 | 3 (codebook) | Theme `setup_onboarding_friction` mixed barriers to starting (initial investment, KYC, minimum amounts) with early confusion after starting; example was "Concept of initial investment is totally unacceptable" | Renamed to `early_confusion_first_months`; pre-start barriers moved out of scope; example replaced with a first-time investor confused about the next instalment who then cancelled (TradingQ&A) | The study is about first-time investors who have already started and then stop within ~12 months. An initial-investment complaint is about starting, not stopping. |
| 2026-11-02 | 3 (codebook) | `long_term_discipline` was proposed as a theme to be scored and ranked with the drop-off themes | Kept only as a contrast (protective) theme: shown in the dropper-vs-continuer table, excluded from the ranked opportunity list | The goal is to find what causes drop-off; a protective factor ranked as a "priority" would be misleading. |

## 4. Limitations

- Reddit was not used: its API needs approval and scraping is barred by its terms. X, Instagram and Quora were also not used (no permitted access).
- Reviews and forum posts are not a random sample of investors. App-store reviews skew towards complaints, so product friction is over-represented relative to behavioural reasons such as returns or cash needs.
- Droppers come mostly from app-store reviews and continuers mostly from YouTube, so stop-lift partly reflects which source a theme appears in, not only stopping behaviour. Read stop-lift as directional.
- SIP status, first-time status and time since starting are self-reported. Only 7 records say the writer is a first-time investor and 84 state how long they have invested, so the 12-month view is descriptive only.
- 'Stopped' includes stopping SIPs on a platform; people who only moved to another app are excluded from the dropper group where switching was their only stop reason.
- Coding was done by Claude (Opus) inside a Claude Code session, not via an API, because the Gemini key had no credits. The same model designed the prompts and did the coding; the golden set is the independent check.
- Evidence-span checks were run by the coder before submitting answers, so the 100% span pass rate reflects that self-check; the pipeline still verifies every span in code.
- The second pass (what people check, worries, help outside the app, segment) only coded records containing a cue word; signals phrased without one are missed. Segment signals (age, income stability, source of money, influencer) are rarely stated in public posts: at most 9 records per value, so segment differences must come from interviews.
- The golden set is small (20 records), so per-field agreement has wide uncertainty.
- Most store reviews come from apps other than Groww (Coin, ET Money, FundsIndia, Paytm Money and others). Findings describe first-time SIP investing in India generally, not Groww specifically.
