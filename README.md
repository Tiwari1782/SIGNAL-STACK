# Signal Stack — Autonomous Company Intelligence & Executive Briefing Engine

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon_Free-336791.svg?style=flat&logo=postgresql)](https://neon.tech)
[![Groq](https://img.shields.io/badge/Groq-Free_Developer_Tier-F55036.svg?style=flat)](https://groq.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash_Fallback-4285F4.svg?style=flat&logo=google)](https://deepmind.google/technologies/gemini/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **EDXSO AI Engineer Intern Assignment 1 Solution**  
> Primary Demo Organization: **MeetUniversity** ([https://www.meetuniversity.com](https://www.meetuniversity.com))  
> Multi-Industry Test Cases: **Claude (Anthropic)** (AI/SaaS) & **Oatly** (FMCG / Food & Beverage).

---

## Executive Overview

Signal Stack is an autonomous executive intelligence engine. Given only a company name and public URL, it:
1. **Autonomously researches** the company website, separating verified ground truth from assumed hypotheses.
2. Conducts an **adaptive 10-question AI interview** that remembers previous answers and asks single-turn, context-sensitive follow-ups.
3. Synthesizes a **4-quadrant Signal Stack** (Customers, Competitors, Market Regulators, Internal Data) with autonomous search discovery (finding 30+ authoritative sources).
4. Executes **polite, rate-limited web crawling** adhering strictly to `robots.txt` with cryptographic `SHA-256` content hashing to eliminate duplicate crawls.
5. Employs a **strict anti-hallucination engine** that verifies every extracted evidence snippet exists **verbatim** in raw crawl text.
6. Computes a **6-factor strategic ranking** score for every signal (`relevance`, `impact`, `urgency`, `credibility`, `recency`, `novelty`).
7. Ingests first-party internal data via **CSV, XLSX, PDF, and TXT uploads** to capture customer objections, lost-deal reasons, and feature requests.
8. Automatically compiles and delivers a structured **10-Section Monday Morning Brief** via web dashboard and Gmail SMTP.
9. Conducts an **automated Monthly Signal Stack Audit** to identify dead URLs (404s), duplicate domains, and recommend new candidate sources.
10. Operates at **$0.00 / month** on 100% free-tier infrastructure.

---

## Architecture & Technology Stack

```
   ┌─────────────────────────────────────────────────────────────┐
   │                       Signal Stack UI                       │
   │  React 18 + Vite + DM Sans / Koulen + Skeuomorphic Tactility│
   └──────────────────────────────┬──────────────────────────────┘
                                  │ REST API (JSON)
   ┌──────────────────────────────▼──────────────────────────────┐
   │                      FastAPI Backend                        │
   │            Python 3.11 + psycopg_pool Connection Pool       │
   ├──────────────────────────────┬──────────────────────────────┤
   │ • Company Setup & Research   │ • Anti-Fabrication Engine    │
   │ • 10-Question AI Interview   │ • 6-Factor Signal Ranking    │
   │ • Autonomous Multi-Engine    │ • 10-Section Brief Generator │
   │ • Polite Crawler (robots.txt)│ • Monthly Health Audit       │
   │ • Internal Document Parser   │ • Context Pivot Engine       │
   └──────────────┬───────────────┴──────────────┬───────────────┘
                  │                              │
     ┌────────────▼───────────┐     ┌────────────▼───────────┐
     │      LLM Pipeline      │     │  Neon PostgreSQL (Free)│
     │  Groq (Primary)        │     │  Pooled Connection     │
     │  Gemini Flash (Backup) │     │  12 Relational Tables  │
     └────────────────────────┘     └────────────────────────┘
```

- **Frontend**: React 18, Vite, React Router 6, DM Sans, Koulen display font, `react-icons`, tactile skeuomorphic styling (`DESIGN.md`).
- **Backend**: Python 3.11, FastAPI, Pydantic v2, `psycopg_pool` (Neon pooled client).
- **Database**: PostgreSQL (Neon Serverless Free Tier, hosted on AWS `us-east-2`).
- **LLM Pipeline**: Dual-provider failover:
  - *Primary*: Groq Free Tier (`openai/gpt-oss-120b` or `llama-3.3-70b-versatile`).
  - *Fallback*: Google Gemini Free Tier (`gemini-2.5-flash`) via `google-genai`.
- **Search & Discovery**: Polite querying of DuckDuckGo, Yahoo, and Wikipedia without paid SERP APIs.
- **Scheduler**: GitHub Actions cron workflows (`weekly_brief.yml` & `monthly_audit.yml`) + manual dashboard triggers.
- **Email Delivery**: Gmail SMTP with App Password authentication.

---

## Hard Rules Compliance Checklist

| Rule | Requirement | Implementation in Signal Stack |
| :--- | :--- | :--- |
| **1. No Hardcoding** | Competitors, sources, and questions must never be hard-coded. | Discovered dynamically via LLM extraction and live web search. Tested across 3 distinct industries. |
| **2. Zero Fabrication** | Every signal needs URL, verbatim evidence, published date, discovery date. | `analysis.py` checks `snippet.lower() in raw_text.lower()`. Hallucinated snippets are discarded. |
| **3. Polite Crawling** | Respect `robots.txt`, rate limits, no paywall bypass. | Uses `urllib.robotparser`, enforces `CRAWL_DELAY = 2.0s`, hashes content with `SHA-256`. |
| **4. Separate Metrics** | Separate `reliability`, `evidence_strength`, `strategic_relevance`. | Stored in independent DB columns; LLM confidence is never equated to verified fact. |
| **5. Business Impact** | Brief must explain business implications, not just summarize. | Brief generator synthesizes "Why it matters", sector implications, opportunities, and risks. |
| **6. Real Scheduler** | Jobs must actually work; failures logged in `job_runs`. | GitHub Actions cron + `runner.py` logs start, end, status, duration, and error tracebacks. |
| **7. No Mock UI** | Every screen wired to backend endpoints. | All 8 pages (`/setup`, `/profile`, `/interview`, `/signal-stack`, `/sources`, `/feed`, `/brief`, `/settings`) make live API calls. |

---

## Local Development Setup

### 1. Database Configuration
1. Create a free PostgreSQL instance on [Neon.tech](https://neon.tech).
2. Copy your pooled connection string into `.env`:
   ```bash
   DATABASE_URL="postgresql://neondb_owner:YOUR_PASSWORD@ep-YOUR-PROJECT-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
   ```
3. Initialize the schema:
   ```bash
   # Schema applies 12 relational tables, triggers, and indices
   psql "$DATABASE_URL" -f backend/schema.sql
   ```

### 2. Backend Setup (FastAPI)
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt

# Start the development server
uvicorn backend.app.main:app --reload --port 8000
```
API Documentation will be live at `http://localhost:8000/docs`.

### 3. Frontend Setup (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Environment Variables (`.env`)

Create a `.env` file in the root directory:
```ini
# PostgreSQL (Neon Pooled Endpoint)
DATABASE_URL=postgresql://user:password@ep-name-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require

# Primary LLM (Groq Developer Free Tier)
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b

# Fallback LLM (Google Gemini Free Tier)
GEMINI_API_KEY=AIzaSy_your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# Email Delivery (Gmail SMTP)
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password

# Frontend URL for CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## Pipeline & Key Algorithms

### 1. Polite Crawler & Content Deduplication
- **Robots.txt Parser**: `urllib.robotparser.RobotFileParser` checks crawl authorization prior to fetching any target URL.
- **Polite Delay**: Enforces `CRAWL_DELAY = 2.0s` between requests with randomized jitter to respect server loads.
- **SHA-256 Hashing**: Calculates the hash of raw document text. If identical to an existing document hash, the crawl is recorded as duplicate and LLM analysis is skipped.

### 2. Anti-Fabrication & Ground-Truth Verification
```python
# Verifies that extracted snippet is verbatim in document text
raw_lower = doc["raw_text"].lower()
snippet_lower = signal_data["evidence_snippet"].lower().strip()

if snippet_lower not in raw_lower:
    # LLM hallucinated the quote -> mark unverified or reject
    signal_data["verification_status"] = "unverified"
    signal_data["evidence_strength"] = 0.20
```

### 3. Multi-Factor Strategic Ranking Formula
Each signal is evaluated using a calibrated, weighted formula:
$$\text{Rank Score} = 0.25 \times R + 0.20 \times I + 0.15 \times U + 0.15 \times C + 0.15 \times \text{Recency} + 0.10 \times \text{Novelty}$$
- **Relevance ($R$)**: Alignment with verified profile facts and interview answers.
- **Impact ($I$)**: Magnitude of market or competitive disruption (0.0 – 1.0).
- **Urgency ($U$)**: Immediate time-sensitivity of required organizational response.
- **Credibility ($C$)**: Source reliability weighted by domain authority.
- **Recency**: Exponential decay based on days elapsed since publication.
- **Novelty**: Similarity penalty against previously surfaced signals.

---

## Monday Morning Brief — 10 Required Sections

Every generated brief satisfies the complete specification in Section 7 of the assignment:
1. **Executive Summary**: Top 5 critical intelligence developments this week.
2. **Customer Signals**: Inquiries, objections, review trends, and lost-deal insights.
3. **Competitor Moves**: Feature launches, pricing shifts, leadership changes, expansions.
4. **Market & Regulatory**: Policy changes, visa regulations, funding rounds, macroeconomic trends.
5. **Internal Signals**: CRM uploads, customer complaints, feature requests.
6. **Opportunities**: At least 3 concrete, revenue-generating or strategic opportunities.
7. **Risks & Threats**: Immediate competitive and operational vulnerabilities.
8. **Actions This Week**: Ownership matrix with assigned owners, actions, and target deadlines.
9. **Watchlist**: Emerging trends, competitors, or topics to monitor next week.
10. **Source Appendix**: Full list of citations, source names, URLs, and reliability ratings.

*(If no signals exist in a category for a given week, the engine explicitly outputs: "No meaningful development this week.")*

---

## Automated Background Jobs & Scheduler

Signal Stack features two background jobs that can run via GitHub Actions or manual UI trigger:

### 1. Weekly Brief Generation (`backend/jobs/weekly_brief.py`)
- Scheduled via `.github/workflows/weekly_brief.yml` every Monday at `06:00 UTC` (`0 6 * * 1`).
- Crawls all approved sources, extracts and verifies signals, ranks intelligence, generates the 10-section brief, creates action items, and sends email notifications.

### 2. Monthly Signal Stack Health Audit (`backend/jobs/monthly_audit.py`)
- Scheduled via `.github/workflows/monthly_audit.yml` on the 1st of every month at `00:00 UTC` (`0 0 1 * *`).
- Tests monitored URLs for dead links (404/500 errors), identifies duplicate tracking domains, computes the overall **Stack Health Score (0-100)**, discovers new candidate sources, and saves an audit report to PostgreSQL.

---

## Reusability & Multi-Industry Verification

Signal Stack was verified across 3 completely distinct industries with zero hardcoded code changes:
1. **MeetUniversity** ([https://www.meetuniversity.com](https://www.meetuniversity.com)) — *International EdTech & Study Abroad Recruitment*.
   - Discovered 31 real sources (IDP, LeapScholar, Yocket, UK Home Office, DAAD).
2. **Claude (Anthropic)** ([https://claude.com/product/overview](https://claude.com/product/overview)) — *Generative AI & Enterprise LLM SaaS*.
   - Discovered competitors (OpenAI, Gemini, Mistral) and technical documentation sources.
3. **Oatly** ([https://www.oatly.com](https://www.oatly.com)) — *Plant-based Food & Beverage / D2C FMCG*.
   - Discovered competitors (Alpro, Danone, Califia Farms) and agricultural commodity sources.

### Dynamic Context-Change Engine
When MeetUniversity pivoted its strategic business focus toward **European public universities (Germany, Netherlands, STEM, and APS certification)**, the engine:
- Evaluated all 45 existing sources.
- Deactivated 5 non-relevant sources (e.g., US SAT prep blogs).
- Retained 35 core sources.
- Discovered 5 new European candidate sources (e.g., DAAD, Study in Germany, Dutch IND).
- Recorded the strategic pivot in `profile_facts`.

---

## Documentation & Deliverables

- 📄 **[Technical Documentation (`docs/TECH_DOC.md`)](file:///c:/MERN%20STACK/9%20-%20COURSE%20PROJECTS/AI-Intern/SIGNAL-STACK/docs/TECH_DOC.md)**: Deep dive into schema, crawler architecture, anti-fabrication pipeline, and ranking math.
- 💰 **[Cost Statement (`docs/COST_STATEMENT.md`)](file:///c:/MERN%20STACK/9%20-%20COURSE%20PROJECTS/AI-Intern/SIGNAL-STACK/docs/COST_STATEMENT.md)**: Proves $0.00 / month across all services.
- 🎬 **[Demo Video Script (`docs/DEMO_SCRIPT.md`)](file:///c:/MERN%20STACK/9%20-%20COURSE%20PROJECTS/AI-Intern/SIGNAL-STACK/docs/DEMO_SCRIPT.md)**: 3-5 minute presentation teleprompter with timestamps and visual cues.
- 📊 **Sample Briefs**:
  - [MeetUniversity Monday Brief (`.md`)](file:///c:/MERN%20STACK/9%20-%20COURSE%20PROJECTS/AI-Intern/SIGNAL-STACK/docs/sample-briefs/meetuniversity_brief.md) | [HTML](file:///c:/MERN%20STACK/9%20-%20COURSE%20PROJECTS/AI-Intern/SIGNAL-STACK/docs/sample-briefs/meetuniversity_brief.html) | [JSON](file:///c:/MERN%20STACK/9%20-%20COURSE%20PROJECTS/AI-Intern/SIGNAL-STACK/docs/sample-briefs/meetuniversity_brief.json)
  - [Claude Monday Brief (`.md`)](file:///c:/MERN%20STACK/9%20-%20COURSE%20PROJECTS/AI-Intern/SIGNAL-STACK/docs/sample-briefs/claude_brief.md) | [HTML](file:///c:/MERN%20STACK/9%20-%20COURSE%20PROJECTS/AI-Intern/SIGNAL-STACK/docs/sample-briefs/claude_brief.html) | [JSON](file:///c:/MERN%20STACK/9%20-%20COURSE%20PROJECTS/AI-Intern/SIGNAL-STACK/docs/sample-briefs/claude_brief.json)
  - [Oatly Monday Brief (`.md`)](file:///c:/MERN%20STACK/9%20-%20COURSE%20PROJECTS/AI-Intern/SIGNAL-STACK/docs/sample-briefs/oatly_brief.md) | [HTML](file:///c:/MERN%20STACK/9%20-%20COURSE%20PROJECTS/AI-Intern/SIGNAL-STACK/docs/sample-briefs/oatly_brief.html) | [JSON](file:///c:/MERN%20STACK/9%20-%20COURSE%20PROJECTS/AI-Intern/SIGNAL-STACK/docs/sample-briefs/oatly_brief.json)
