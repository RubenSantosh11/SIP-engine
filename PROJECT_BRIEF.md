# Project brief (Nextleap PM graduation project) — verbatim from the PM, 2026-11-02

Choose any ONE product: Groww, Zerodha Coin, INDmoney.

You are a Product Manager on the Growth Team at the product you have chosen.
Starting a SIP is easy. A few taps, a small monthly amount, and a quiet promise to your future self.
Staying with it is a different matter. Months pass, life gets busier, the first few statements look underwhelming, and the SIP that felt like a good decision in month one becomes something users stop thinking about, pause, or let lapse.

**Strategic goal:** Increase the percentage of first-time mutual fund investors who still have an active SIP 12 months after starting their first one.
An active SIP means at least one successful instalment in the last 30 days. Investors who stay invested longer are worth more to the platform and, more importantly, are the ones who actually benefit from investing.
You are not given the underlying user problem; discover it.
**Solution constraints:** CANNOT recommend specific funds or stocks. CANNOT use fear, FOMO or urgency-based nudges.

## Part 1: Build an AI-Powered Discovery Engine
Analyse user feedback at scale (any AI-native stack). Sources: App Store and Play Store reviews, Reddit (Indian investing communities), forums such as TradingQ&A, social media, YouTube comments on personal finance videos, other public conversations about SIPs and first-time investing in India.
Questions the engine should help answer:
- Why do people start a SIP, and what do they expect to happen?
- What changes in their behaviour in the months after starting?
- What leads investors to pause, reduce or stop a SIP?
- What do investors check, and how often, once they have started?
- What confuses or worries them inside the app?
- What do they do outside the app when they feel unsure?
- What separates investors who continue from those who quietly drop off?
- How do these patterns differ across user segments (income stability, age, source of money, who influenced them)?
- What unmet needs emerge consistently across conversations?
Go beyond summarising or sentiment: identify, quantify where possible, and compare opportunity areas that could influence the metric. Show how data is gathered and analysed, how themes are identified, how insights are generated, and how insight quality was validated (AI Evidence Log).

## Part 2: Break Down the Business Metric
Decompose "12-month SIP continuation for first-time investors" into product outcomes and user behaviours. Use it with the discovery output to find the highest-potential opportunities.

## Part 3: Validate Through User Research
Choose a target segment and opportunity area. Conduct 5-6 user interviews in that segment. Understand: why they started and what they expected; the experience since; whether they paused/reduced/considered stopping and why; what they check and when and how they feel about it; what they do outside the app when unsure; what would make them more likely to continue. Do NOT collect account numbers, PAN or portfolio screenshots.

## Part 4: Define the Problem
Target segment; the moment/scenario in the first 12 months; product outcome to influence; root cause; existing workarounds; user value; business sense. Show the evolution Business Metric -> Product Outcomes -> AI Discovery -> Primary Research -> Problem Definition, and how primary research validated or challenged the engine. Do NOT frame it simply as "investors stop SIPs when markets fall"; explain why continuation breaks down despite good intent.

## Part 5: Build and Deploy an AI-Native MVP
A feature, AI workflow, agent or standalone experience. Must be built around an eval-gated AI feature with a visible quality check or safe fallback (decline, express uncertainty, point to an official source); measure output quality against the golden set from the Evidence Log. Explain where AI earns its place and what a non-AI version would miss. Must not present anything as investment advice and must say so. Deploy to production so another person can attempt a real task; mentors will test it.

## Part 6: Test the MVP With Users
At least 3 users from the segment on a real task; document learnings and next-iteration changes.

## Part 7: Define Success
Start from the business metric; leading indicators, guardrails, definitions and rationale; how to measure the AI feature's output quality.

## Part 8: Risks & Mitigation

## Deliverables
- [Link] AI Discovery Engine: link where the workflow can be tested + 1 slide in the deck on how it works.
- [PDF] 10-slide deck: metric decomposition, discovery findings, user research, target segment, root cause and problem definition, solution rationale, MVP and user testing, success metrics, risks and limitations.
- [Link] Deployed AI-native MVP, publicly testable.
- [Link] AI Evidence Log (one document, view access for anyone with the link): sources and volume; golden set of ~20 hand-labelled items, agreement and failures; 2-3 places AI output was rejected or corrected, and why.
