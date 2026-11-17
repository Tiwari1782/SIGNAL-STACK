# SPEC.md — implementation details for Signal Stack

## Pipeline (per company)
1. **Setup**: POST company {name, website}. Crawl homepage + key pages (about, products, pricing, blog). LLM extracts profile facts;
   each fact is stored with status `verified` (with evidence_url) or `assumed`.
2. **Interview**: LLM generates the NEXT question from (profile + all previous Q&A + uncovered topics). One at a time, 10 total,
   follow-ups allowed (`is_followup`). Skip allowed. Topics to cover are guidance only (business lines, customers, problems,
   differentiators, competitors, market changes, risks, 6-12 month priorities, internal data, decisions to support).
3. **Source discovery**: for each category, generate search queries from profile+answers, run `ddgs`, fetch candidates, LLM scores each
   for specificity / recency / credibility and writes a `reason`. Store as `suggested`; user approves. Competitors: 5-10, discovered, never hard-coded.
   - customers: forums, Reddit/Quora-style communities, review sites, student/parent communities (adapt per industry)
   - market: regulators, official policy pages, industry news/RSS
   - internal: upload endpoint only
4. **Monitoring**: for approved sources: robots.txt check -> fetch (RSS first, else page) -> extract text -> sha256 -> skip if hash seen
   -> store `documents` -> write `crawl_runs`. Failed sources are logged, never fatal.
5. **Analysis**: for each new document, LLM returns JSON {is_significant, what_happened, published_at, category, competitor_name,
   why_it_matters, business_area, impact_type, urgency, suggested_action, evidence_snippet (verbatim from text), interpretation}.
   Reject any signal whose evidence_snippet is not found in the document text (anti-fabrication check).
6. **Ranking**: rank_score = 0.25*relevance + 0.20*impact + 0.15*urgency + 0.15*credibility + 0.15*recency + 0.10*novelty (each 0-1).
   Store `source_reliability`, `evidence_strength`, `strategic_relevance` separately. Save a plain-language `rank_explanation`.
   `verification_status` = verified only if corroborated by 2+ independent sources or an official source.
7. **Brief**: top-N signals -> 10 sections (see ASSIGNMENT.md section 7). Empty category => "No meaningful development this week."
   Opportunities >= 3 only if evidence supports them; otherwise state the limitation. Source Appendix lists every cited signal.
8. **Context change**: PATCH profile/interview answers -> re-score all sources against the new context -> mark irrelevant as `inactive`,
   suggest new ones, return a diff ("what changed and why").
9. **Monthly audit**: HEAD/GET every source (dead URLs), duplicate domains/URLs, no new docs in 60 days => inactive, relevance trend,
   new discovery run, write `audit_reports`.

## API (FastAPI, prefix /api)
- POST /companies; GET /companies/{id}; GET/PATCH /companies/{id}/profile
- POST /companies/{id}/research
- GET /companies/{id}/interview/next; POST /companies/{id}/interview/answer {seq, answer|skip}; PATCH /interview/{qa_id}
- POST /companies/{id}/signal-stack/build; GET /companies/{id}/signal-stack
- GET/POST/DELETE /companies/{id}/sources; POST /sources/{id}/approve; GET /sources/{id}/history
- POST /companies/{id}/crawl
- GET /companies/{id}/feed?category&competitor&from&to&min_relevance&impact&verification
- POST /companies/{id}/briefs/generate; GET /companies/{id}/briefs; GET /briefs/{id}; PATCH /actions/{id}; POST /briefs/{id}/email
- POST /companies/{id}/uploads (csv, xlsx, pdf, txt)
- GET/PUT /companies/{id}/settings
- GET /job-runs; POST /jobs/{weekly_brief|monthly_audit}/run

## Frontend pages
Setup, Profile (editable, verified vs assumed badges), Interview (chat style, one question), Signal Stack (4 tabs with reasons),
Source Manager, Feed (filters), Brief (history, actions, export PDF/HTML, email), Settings, Job Runs (failures visible).

## Demo / test targets
MeetUniversity + 2 other-industry companies (e.g. a SaaS company and a D2C/food brand), >=20 approved MeetUniversity sources,
>=30 real collected records, context-change demo on one company, 1 brief per company saved to docs/sample-briefs/.
