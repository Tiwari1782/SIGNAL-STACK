# Signal Stack — Technical Documentation

**System:** Executive Intelligence & Automated Briefing Engine  
**Author:** AI Engineer Intern Candidate  
**Target Demo Company:** MeetUniversity (`https://www.meetuniversity.com`)  
**Stack:** PostgreSQL (Neon) • Python 3.11/FastAPI • React (Vite) • Groq (Primary) + Gemini (Fallback)

---

## 1. System Architecture & High-Level Flow

Signal Stack transforms unstructured external web intelligence and internal CRM data into decision-grade Monday Morning Briefings for leadership teams:

```
+-----------------------------------------------------------------------------------+
| 1. COMPANY SETUP & ONBOARDING                                                     |
| - URL + Name Input -> Polite Crawler -> LLM Fact Extraction (Verified vs Assumed) |
| - 10-Question Adaptive Interview -> Deep Strategic Context (Follow-up detection) |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 2. SIGNAL STACK DISCOVERY & SENSORS                                               |
| - Multi-Engine Search (DuckDuckGo, Yahoo, Wikipedia, Startpage)                   |
| - 4 Sensor Categories: Customers, Competitors (5-10 direct), Market, Internal     |
| - Dual Scoring: Strategic Relevance (0-1.0) & Source Reliability (0-1.0)          |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 3. POLITE CRAWLING & CHANGE DETECTION ENGINE                                      |
| - robots.txt verification via urllib.robotparser                                  |
| - Rate limiting (CRAWL_DELAY = 2.0s) & Polite User-Agent identification           |
| - SHA-256 Content Hashing -> Exact change detection & duplicate rejection         |
| - Full audit logging to crawl_runs table                                          |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 4. ANALYSIS & MULTI-FACTOR RANKING ENGINE                                         |
| - Strict Anti-Fabrication: Verbatim substring check against raw document text     |
| - Multi-Factor Ranking Formula:                                                   |
|     rank_score = 0.25*relevance + 0.20*impact + 0.15*urgency                      |
|                + 0.15*credibility + 0.15*recency + 0.10*novelty                   |
| - Independent scores for Reliability, Evidence Strength, Strategic Relevance     |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 5. MONDAY MORNING BRIEF GENERATOR & ACTION TRACKING                               |
| - 10 Standardized Sections (Exec Summary, Customer, Competitor, Market, Internal, |
|   Opportunities, Risks, Actions w/ Owners & Priority, Watchlist, Source Appendix) |
| - Interactive Task Checklist with state persistence (open / in_progress / done)   |
| - Automated Gmail SMTP delivery + Branded HTML rendering                          |
| - GitHub Actions Cron Scheduler (Weekly Brief + Monthly Health Audit)             |
+-----------------------------------------------------------------------------------+
```

---

## 2. Database Schema (PostgreSQL on Neon)

The system relies on 12 relational tables optimized with indices and connection pooling:

1. **`companies`**: Target organizations (`id`, `name`, `website`, `settings` JSONB, `created_at`).
2. **`profile_facts`**: Core company model facts (`field`, `value`, `status` IN `('verified', 'assumed', 'founder_provided')`, `evidence_url`).
3. **`interview_qa`**: Adaptive interview progression (`seq`, `question`, `answer`, `skipped`, `is_followup`).
4. **`sources`**: Sensor network records (`category`, `name`, `url`, `reason`, `status`, `competitor_name`, `source_reliability`, `relevance_score`, `last_checked`, `last_status_code`).
5. **`crawl_runs`**: Crawling telemetry and health log (`source_id`, `status`, `http_status`, `new_docs`, `error`).
6. **`documents`**: Ingested articles and web pages (`source_id`, `url`, `title`, `content`, `content_hash` SHA-256, `published_at`).
7. **`signals`**: Ranked business developments (`category`, `competitor_name`, `what_happened`, `evidence_snippet`, `source_url`, `verification_status`, `why_it_matters`, `business_area`, `impact_type`, `urgency`, `suggested_action`, `source_reliability`, `evidence_strength`, `strategic_relevance`, `rank_score`, `rank_explanation`, `interpretation`).
8. **`briefs`**: Persisted Monday intelligence reports (`period_start`, `period_end`, `content` JSONB, `html`, `trigger`).
9. **`actions`**: Operationalized recommendations (`brief_id`, `title`, `reason`, `owner`, `priority`, `status`).
10. **`uploads`**: First-party internal documents (`filename`, `kind`, `extracted_text`, `uploaded_at`).
11. **`job_runs`**: Background execution telemetry (`job_name`, `company_id`, `status`, `started_at`, `finished_at`, `error`, `summary` JSONB).
12. **`audit_reports`**: Monthly stack health evaluations (`company_id`, `content` JSONB, `created_at`).

---

## 3. Crawling, Deduplication & Anti-Fabrication

### Polite Crawling Protocol
- Every external URL fetch checks `robots.txt` via `urllib.robotparser.RobotFileParser`.
- Enforces an automated `CRAWL_DELAY = 2.0` seconds between successive requests to the same domain.
- Transparent identification header: `User-Agent: SignalStackBot/1.0 (+https://github.com/signalstack; polite research crawler)`.
- Dual extraction: RSS feeds (`feedparser`) where available; fallback to structured article extraction (`trafilatura`).

### Change Detection & Deduplication
- Computes `SHA-256(content.strip().encode("utf-8"))`.
- `UNIQUE (source_id, content_hash)` constraint guarantees zero duplicate documents or redundant LLM processing.
- Duplicate crawls record `new_docs = 0` in `crawl_runs` and terminate without token spend.

### Anti-Fabrication Guarantee
- To prevent LLM hallucinations, every extracted signal's `evidence_snippet` is verified verbatim against the raw scraped document text:
  ```python
  clean_doc_text = re.sub(r"\s+", " ", doc["content"]).lower()
  clean_evidence = re.sub(r"\s+", " ", evidence).lower()
  if clean_evidence not in clean_doc_text:
      # Check first 40 chars; fallback to verbatim sentence excerpt or reject
  ```
- Any ungrounded claims are rejected. When no developments occurred, the system explicitly outputs: *"No meaningful development this week"*.

---

## 4. Multi-Factor Signal Ranking Algorithm

Signals are prioritized using a weighted composite formula:

$$\text{Rank Score} = 0.25 R + 0.20 I + 0.15 U + 0.15 C + 0.15 T + 0.10 N$$

- **Strategic Relevance ($R \in [0, 1]$)**: Relevance to core company goals, audience, and revenue model.
- **Business Impact ($I \in [0, 1]$)**: Magnitude of commercial opportunity, risk, or competitive shift.
- **Urgency ($U \in \{0.3, 0.6, 0.9\}$)**: Low / Medium / High action requirement.
- **Source Credibility ($C \in [0, 1]$)**: Historical reliability of the publication/regulator.
- **Recency ($T \in [0, 1]$)**: Exponential decay based on days elapsed since published date ($e^{-0.05 \cdot \text{days}}$).
- **Novelty ($N \in [0, 1]$)**: 0.85 for newly discovered events vs. 0.35 for repeated themes.

---

## 5. Scheduler, Monthly Audit & Resilience

1. **Automated Weekly Brief**:
   - Executes every Monday at 06:00 UTC via GitHub Actions (`.github/workflows/weekly_brief.yml`).
   - Crawls approved sources -> extracts signals -> ranks -> generates 10-section brief -> saves actions -> sends Gmail SMTP email.
2. **Monthly Signal Stack Audit**:
   - Executes on the 1st of every month via GitHub Actions (`.github/workflows/monthly_audit.yml`).
   - Runs HTTP HEAD/GET reachability checks (marks dead links as `'dead'`).
   - Detects duplicate domains and inactive sources (no docs in 60+ days).
   - Computes a Stack Health Score (0–100) and discovers candidate sources to fill coverage gaps.
3. **Dual LLM Provider Failover**:
   - Primary: Groq free tier (`openai/gpt-oss-120b`).
   - Fallback: Google Gemini free tier (`gemini-2.5-flash`).
   - If Groq returns 413, 429, or timeout, the request seamlessly routes to Gemini with zero user interruption.
