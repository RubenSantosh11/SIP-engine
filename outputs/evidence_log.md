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

Golden-set agreement: pending. The PM is labelling `outputs/golden_set_blank.csv`.

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
