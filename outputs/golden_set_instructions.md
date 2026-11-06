# Golden set: how to label (about 20 minutes)

Open `outputs/golden_set_blank.csv` in Excel or Google Sheets. For each of the 20 rows, read `text` (and `context` for YouTube and forum posts) and fill in:

| Column | Allowed values |
|---|---|
| `sip_status` | `stopped` (cancelled or ended future instalments, or clearly says 'I want to stop my SIP'), `paused` (paused, skipped or missed but keeping it), `reduced` (lowered the amount), `continuing`, `unclear` |
| `first_time_investor` | `yes` / `no` only if the text says so, else `unclear` |
| `time_since_start` | `<1m`, `1-6m`, `6-12m`, `>12m`, `unclear` |
| `themes` | `theme_id:severity` pairs separated by `;` (severity 1 = minor mention, 2 = clear reason or friction, 3 = decisive or strong distress). Leave empty if none apply. |
| `notes` | anything odd |

Stopping means ending future instalments. Redeeming (selling units) on its own is not a stop.

Don't look at any engine output before you finish. Save the file as `outputs/golden_set_labelled.csv` and tell me.

## Theme ids

| theme_id | Name | Use when |
|---|---|---|
| `payment_autopay_failure` | Autopay / mandate / payment failures | Instalments are missed, fail or are debited wrongly because of autopay, mandate, bank or payment problems, or because there is no auto-debit and the investor must pay manually each month. |
| `missing_sip_controls` | Can't pause, skip, reduce or cancel easily | The investor wants to pause, skip, change the amount or date, or cancel, but the option is missing, broken or deliberately hard, so they cancel outright or feel trapped. |
| `app_reliability_errors` | App bugs, slow processing and confusing status | SIP orders stay in processing, units are allotted late, the app crashes or an update breaks flows, or the investor cannot tell whether a SIP is active or where money went after cancelling. |
| `fees_paywall` | New fees, paywalls and upselling | The platform starts charging for basics, locks features behind subscriptions or pushes paid plans, and the investor stops or moves SIPs. |
| `support_trust_breakdown` | Unresponsive support and loss of trust | Problems go unresolved because support or the agent does not respond, and the investor loses trust in the platform. |
| `returns_disappointment` | Disappointing returns or market fear | Flat, negative or below-expectation returns over months or years, or fear during market falls, lead the investor to stop or consider stopping. |
| `cash_need_affordability` | Cash need or amount too high | The investor needs the money elsewhere, or the SIP amount (or step-up) becomes hard to sustain. |
| `platform_or_fund_initiated` | Stopped or changed by the platform or fund | The SIP was paused, deleted or cancelled by the fund house or platform rather than by the investor. |
| `switching_plan_or_platform` | Switching plan, fund or platform (not a real drop) | The investor stops a SIP only to restart it elsewhere, e.g. regular to direct, a different fund or another app. |
| `early_confusion_first_months` | Early confusion after the first instalment | In the first weeks or months after starting, the investor misunderstands how the SIP works (when instalments are taken, where the money is, what cancelling or redeeming does) and stops or cancels as a result. |
| `return_expectations` | Specific return expectations at the start | Starts with a concrete expectation of returns or a corpus (e.g. 12% a year, 1 crore in 10 years), often set by ads or creators. |
| `missed_reminders_forgetting` | No reminders, so instalments are forgotten | Instalments are missed because the app sends no reminder or due-date notification, and the investor forgets to pay or place the order. |
| `disruptive_app_updates` | App updates that break or hide SIP flows | A redesign or update removes or hides SIP features (pay button, SIP list, modify, tracking), so the investor misses payments, cannot manage SIPs or decides to leave. |
| `charges_lockin_surprise` | Surprise charges, lock-ins or tax at exit | The investor is surprised by exit loads, lock-in periods, tax or other charges when stopping or redeeming, and feels misled. |
| `conflicting_advice` | Conflicting or misleading advice | The investor is confused or loses confidence because creators, agents or ads give conflicting or misleading messages about SIPs, or they were mis-sold (e.g. a regular plan without understanding it). |
| `long_term_discipline` | Long-term discipline (protective) (contrast only) | Investor keeps going because of a long horizon, a family goal, discipline or experience of holding through falls. |
