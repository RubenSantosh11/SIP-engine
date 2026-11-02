# SIP Discovery Engine: results

Why first-time SIP investors in India pause, reduce or stop. Public feedback, coded one record at a time; all counting and scoring in Python.

## Sources and volume

| Source | Raw | Passed keyword filter | Relevant | Extracted |
|---|---|---|---|---|
| Google Play | 22,004 | 900 | 411 | 411 |
| Apple App Store | 3,165 | 106 | 48 | 48 |
| YouTube comments | 1,873 | 593 | 120 | 120 |
| TradingQ&A forum | 465 | 211 | 40 | 40 |
| ValuePickr forum | 238 | 50 | 7 | 7 |
| **Total** | **27,745** | **1,860** | **626** | **626** |

SIP status of extracted records: unclear 382, stopped 122, paused 61, continuing 60, reduced 1. Dropper group: 175 records; continuer group: 60.

## Ranked opportunity areas

Ranked by the lower confidence bound of priority = reach x severity x stop-lift x addressability. A theme is ranked only with at least 30 records from at least 2 sources.

| # | Theme | Records | Reach (95% CI) | Severity | Stop-lift (95% CI) | Addressability | Priority (low bound) |
|---|---|---|---|---|---|---|---|
| 1 | App bugs, slow processing and confusing status | 154 | 22% (17%-28%) | 2.1 | 5.6 (1.8-17.3) | high | 0.645 |
| 2 | Autopay / mandate / payment failures | 134 | 19% (14%-24%) | 2.1 | 3.4 (1.3-9.2) | high | 0.384 |
| 3 | Unresponsive support and loss of trust | 76 | 12% (8%-17%) | 2.0 | 19.8 (1.2-318.7) | high | 0.205 |
| 4 | New fees, paywalls and upselling | 48 | 11% (8%-16%) | 2.5 | 2.7 (0.9-8.8) | high | 0.172 |
| 5 | App updates that break or hide SIP flows | 51 | 8% (5%-12%) | 2.0 | 2.9 (0.7-12.2) | high | 0.073 |
| 6 | Can't pause, skip, reduce or cancel easily | 109 | 9% (6%-13%) | 2.1 | 1.9 (0.6-6.4) | high | 0.070 |
| 7 | Disappointing returns or market fear | 38 | 5% (3%-9%) | 2.3 | 0.3 (0.1-1.0) | medium | 0.005 |

**Not ranked**

| Theme | Records | Reason |
|---|---|---|
| Switching plan, fund or platform (not a real drop) | 62 | switching is an outcome, not a cause (its causes are coded in other themes) |
| Early confusion after the first instalment | 26 | only 26 records (< 30) |
| Stopped or changed by the platform or fund | 15 | only 15 records (< 30) |
| No reminders, so instalments are forgotten | 20 | only 20 records (< 30) |
| Surprise charges, lock-ins or tax at exit | 8 | only 8 records (< 30) |
| Cash need or amount too high | 14 | only 14 records (< 30) |
| Conflicting or misleading advice | 22 | only 22 records (< 30) |
| Specific return expectations at the start | 13 | only 13 records (< 30) |
| Long-term discipline (protective) | 39 | contrast only (protective factor, not an opportunity) |

## Droppers vs continuers

| Theme | Droppers mentioning | Continuers mentioning | Stop-lift |
|---|---|---|---|
| App bugs, slow processing and confusing status | 49/175 (28%) | 3/60 (5%) | 5.6 |
| Autopay / mandate / payment failures | 40/175 (23%) | 4/60 (7%) | 3.43 |
| Unresponsive support and loss of trust | 28/175 (16%) | 0/60 (0%) | 19.76 |
| New fees, paywalls and upselling | 24/175 (14%) | 3/60 (5%) | 2.74 |
| App updates that break or hide SIP flows | 17/175 (10%) | 2/60 (3%) | 2.91 |
| Can't pause, skip, reduce or cancel easily | 17/175 (10%) | 3/60 (5%) | 1.94 |
| Disappointing returns or market fear | 6/175 (3%) | 6/60 (10%) | 0.34 |
| Switching plan, fund or platform (not a real drop) | 28/175 (16%) | 0/60 (0%) | 19.76 |
| Early confusion after the first instalment | 16/175 (9%) | 0/60 (0%) | 11.44 |
| Stopped or changed by the platform or fund | 11/175 (6%) | 2/60 (3%) | 1.89 |
| No reminders, so instalments are forgotten | 6/175 (3%) | 0/60 (0%) | 4.51 |
| Surprise charges, lock-ins or tax at exit | 2/175 (1%) | 0/60 (0%) | guarded |
| Cash need or amount too high | 3/175 (2%) | 4/60 (7%) | 0.26 |
| Conflicting or misleading advice | 2/175 (1%) | 4/60 (7%) | 0.17 |
| Specific return expectations at the start | 1/175 (1%) | 4/60 (7%) | 0.09 |
| Long-term discipline (protective) | 0/175 (0%) | 24/60 (40%) | 0.01 |

## Quotes for each ranked theme

**App bugs, slow processing and confusing status**
- "their app did not show the transaction, i did not receive mutual fund unit neither my money was returned ever" (Google Play, coin)
- "The manage SIP segment is mostly not showing which caused missing multiple SIPs" (Apple App Store, paytmmoney)
- "jisko mene cancel kiya dikha nhi yani mere paise chale gaye" (YouTube comments)

**Autopay / mandate / payment failures**
- "I have been trying to make AMP SIPs for last 3months but it never executes. I have to do it manual each time" (Google Play, coin)
- "updating the bank account for SIP auto-debit usually force you to cancel the existing SIP and create a new one" (Apple App Store, upstox)
- "ek bhi kist miss hui, 150 se750 tk account se cut jayega bank panelty ke naam se" (YouTube comments)

**Unresponsive support and loss of trust**
- "they gave tentative deadline of refund every time but it has never been refunded" (Google Play, coin)
- "raised the issue with customer support and they have refused to help" (Apple App Store, paytmmoney)
- "vo abhi phone nahi uthata" (YouTube comments)

**New fees, paywalls and upselling**
- "u are continuously forcing us to subscribe for ur paid service by disabling one by one features" (Google Play, etmoney)
- "each time I have to pay Zerodha/payment gateway Rs 9" (TradingQ&A forum)
- "they are forcing people to Genius then only will allow to use basic functionalities" (Google Play, etmoney)

**App updates that break or hide SIP flows**
- "with the update they seemed to have removed the functions where one could easily stop or pause his SIP's" (Google Play, fundsindia)
- "I am not able to pay my SIP instalment since the update" (Apple App Store, paytmmoney)
- "in the latest update i am not able to see manual payment option for monthly SIPs" (Google Play, upstox)

**Can't pause, skip, reduce or cancel easily**
- "the App still doesn't offer an option to cancel or discontinue the SIP despite the lock-in period having expired" (Google Play, fundsindia)
- "The cancellation process goes through and their is confirmation on the app but the cancellation doesn’t happen" (Apple App Store, paytmmoney)
- "having to send a physical request letter to the AMC and having to wait for a month to stop" (TradingQ&A forum)

**Disappointing returns or market fear**
- "Some investors who monitor their portfolio panic in such continuous market fall & stop SIPs" (TradingQ&A forum)
- "मेरे को 25 हजार का फटका लग गया है 2 साल से अभी भी वही वैल्यू है" (YouTube comments)
- "ET money has given me a return of negative 3 percent returns" (Google Play, etmoney)

## Within the first 12 months (descriptive)

31 records state that the writer started less than 12 months ago; 7 say they are first-time investors. Too few to score; most frequent themes among them:

- App bugs, slow processing and confusing status: 10
- Early confusion after the first instalment: 8
- Disappointing returns or market fear: 4
- Unresponsive support and loss of trust: 3
- Conflicting or misleading advice: 2
- Autopay / mandate / payment failures: 2

## What investors check, worry about, and where they turn

Second extraction pass. Only records containing a cue word were coded (the rest were set empty by rule), so counts are a floor. Records counted once per value.

| Question | Value | Records | Stopped/paused | Still investing |
|---|---|---|---|---|
| check | instalment_status | 14 | 7 | 0 |
| check | nav_or_units | 5 | 0 | 0 |
| check | portfolio_overall | 16 | 3 | 8 |
| check | returns_or_value | 27 | 4 | 9 |
| outside_help | advisor_agent_bank | 3 | 1 | 0 |
| outside_help | customer_support | 27 | 8 | 0 |
| outside_help | other | 3 | 1 | 1 |
| outside_help | search_web | 3 | 1 | 0 |
| outside_help | social_or_forum | 7 | 2 | 2 |
| outside_help | youtube_creator | 20 | 4 | 6 |
| segment_age_band | 25-34 | 1 | 0 | 0 |
| segment_age_band | 35-44 | 3 | 0 | 2 |
| segment_age_band | <25 | 4 | 0 | 4 |
| segment_income_stability | homemaker | 2 | 0 | 0 |
| segment_income_stability | irregular_or_business | 1 | 0 | 1 |
| segment_income_stability | salaried | 9 | 1 | 2 |
| segment_income_stability | student_no_income | 1 | 0 | 1 |
| segment_influencer | ads_or_app | 2 | 0 | 0 |
| segment_influencer | advisor_agent_bank | 5 | 0 | 0 |
| segment_influencer | self | 5 | 0 | 4 |
| segment_influencer | youtube_creator | 3 | 0 | 1 |
| segment_money_source | salary_savings | 6 | 1 | 4 |
| worry | app_status_or_error | 12 | 7 | 1 |
| worry | charges_or_tax | 2 | 2 | 0 |
| worry | how_sip_works | 17 | 5 | 1 |
| worry | losing_money | 13 | 2 | 2 |
| worry | other | 11 | 1 | 1 |
| worry | where_is_my_money | 15 | 4 | 0 |
| worry | whether_to_continue | 8 | 2 | 1 |

## Validation

Evidence-span check: 1182 coded values, 0 failures, pass rate 100%.

Golden-set agreement: pending. The PM is labelling `outputs/golden_set_blank.csv`.

## Limitations

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
