# AGENTS.md — Signal Stack (EDXSO AI Engineer Intern Assignment 1)

You are building **Signal Stack**: enter a company name + URL -> research -> adaptive 10-question
interview -> Signal Stack (Customers / Competitors / Market / Internal) -> crawl sources ->
analyse -> **Monday Morning Brief**. Demo company: MeetUniversity (https://www.meetuniversity.com).

READ FIRST: `docs/ASSIGNMENT.md` (the original assignment, source of truth), `docs/SPEC.md` (pipeline, API, ranking),
`DESIGN.md` (UI), `backend/schema.sql` (DB).

## Stack (fixed, do not change)
- DB: PostgreSQL (Neon, free). Schema in `backend/schema.sql`
- Backend: Python 3.11 + FastAPI
- Frontend: React (Vite) — follow `DESIGN.md` strictly (tokens in `frontend/src/styles/tokens.css`)
- LLM: Gemini free tier (primary), Groq free tier (fallback). Model names come from env vars.
- Email: Gmail SMTP with App Password
- Scheduler: GitHub Actions cron running `python -m backend.jobs.weekly_brief` / `monthly_audit`
- Everything must be free. No paid APIs or scraping platforms.

## HARD RULES (violating any = automatic fail in grading)
1. NO hard-coded competitors, sources, or interview questions. Generate per company via search + LLM.
2. NO fabricated data. Every signal needs: source URL, evidence snippet, published date (if known), discovery date.
   If nothing is found, say so explicitly ("No meaningful development this week").
3. Real crawling only. Respect robots.txt (urllib.robotparser), rate limits, never bypass login/paywalls.
4. Keep `source_reliability`, `evidence_strength`, `strategic_relevance` as SEPARATE fields.
   An LLM confidence score is never proof an event is true. Separate "verified fact" from "interpretation".
5. Brief must explain business implications, not just summarise articles.
6. Scheduler must really work; failures logged in `job_runs` and shown in dashboard.
7. No mock UI. Every screen is wired to the backend.

## Features to build (see README for order)
- Company Setup, Company Profile (verified vs assumed, editable)
- AI Interview: 10 questions, ONE at a time, remembers answers, follow-ups, skip allowed, editable later
- Signal Stack with `reason` per source; 5-10 competitors; >=20 approved sources for MeetUniversity
- Source Manager: add/remove, approve discovered, health, history, duplicates
- Monitoring: crawl, hash-dedupe, change detection, store evidence + history
- Analysis: what/when/source/verified/why it matters/business area/opportunity-threat-neutral/urgency/action
- Ranking: relevance, impact, urgency, credibility, recency, novelty (+ explanation)
- Intelligence Feed with filters (category, competitor, date, relevance, impact, verification)
- Monday Brief: 10 sections (Exec Summary top 5, Customer, Competitor, Market, Internal, Opportunities >=3,
  Risks, Actions this week w/ owner, Watchlist, Source Appendix), history, action tracking, export/email
- Internal intelligence: CSV / Excel / PDF / text upload -> objections, lost-deal reasons, requests
- Settings: briefing time, timezone, monitor frequency, refresh frequency, monthly audit, profile updates
- Manual "Generate brief now" button
- Monthly Signal Stack Audit: dead URLs, duplicates, inactive, declining relevance, new sources, report
- Context-change flow: edit business context -> reassess sources, drop/add, explain what changed
- Must work for ANY company (final test uses an unseen one). Test with 2 other industries.

## Deliverables checklist
Repo, README + setup, demo video script, 3 sample briefs (`docs/`), tech doc (<=5 pages),
cost statement, test evidence screenshots, live URL (Vercel + HF Space/Koyeb) or local setup.

## Conventions
- Type hints, small modules, `.env` for secrets (never commit). Log every crawl to `crawl_runs`.
- Wrap every external call in try/except; one bad source must not fail a whole job.
