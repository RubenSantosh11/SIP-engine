# SIP-engine: notes for Claude

- Read `PROJECT_BRIEF.md` first: it is the full graduation-project brief (Parts 1-8 and deliverables). This repo is Part 1 (the discovery engine).
- Hard constraints everywhere: no specific fund/stock recommendations; no fear, FOMO or urgency nudges; nothing presented as investment advice.
- Never print, log or commit API keys. Reddit is out of scope (access policy).
- LLM work currently runs in "session" mode (Claude answers queued prompts; see README). All counting and scoring is plain Python.
- Keep `corrections_log.md` updated whenever the PM overrules AI output.
