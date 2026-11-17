# Signal Stack — Video Demo Script (3 to 5 Minutes)

**Title:** Signal Stack: Autonomous Competitive & Market Intelligence Engine  
**Project:** EDXSO AI Engineer Intern Assignment 1  
**Target Demo Company:** MeetUniversity (`https://www.meetuniversity.com`)  
**Presenter / Narrator:** AI Engineer Intern Candidate  

---

## Video Timeline Overview

| Section | Timestamp | Key Screen / Visual Cue | Core Message |
| :--- | :--- | :--- | :--- |
| **1. Hook & Overview** | 0:00 - 0:35 | Setup Page / Brand Header | The problem with info overload; intro to Signal Stack |
| **2. Setup & Autonomous Research** | 0:35 - 1:05 | Company Setup -> Profile Page | 1-click URL crawl -> verified vs. assumed profile facts |
| **3. Adaptive AI Interview** | 1:05 - 1:45 | Interview Page (Interactive Chat) | 10 questions, single-turn, memory, follow-ups, editing |
| **4. Signal Stack & Source Manager** | 1:45 - 2:20 | Signal Stack & Sources Pages | 4 quadrants, 31 sources, polite crawling, SHA-256 dedupe |
| **5. Anti-Fabrication & Ranking** | 2:20 - 2:55 | Intelligence Feed | Verbatim quotes, 6-factor ranking formula, filters |
| **6. Internal CRM Intelligence** | 2:55 - 3:25 | Internal Upload Modal | Drag-and-drop CSV -> customer objections & requests |
| **7. Monday Morning Brief** | 3:25 - 4:10 | Monday Brief Page | 10 structured sections, action tracking, email dispatch |
| **8. Settings, Scheduler & Audit** | 4:10 - 4:40 | Settings & Scheduler Page | GitHub Actions cron, live monthly audit, dead URL detection |
| **9. Multi-Industry & Pivot Demo** | 4:40 - 5:00 | Oatly & Claude Setup / Context Pivot | Zero hardcoded rules, proven on 3 distinct industries |

---

## Detailed Script & Teleprompter

### 1. Hook & Overview (0:00 – 0:35)
**[VISUAL]:** Screen opens on the clean, skeuomorphic Signal Stack dashboard. Header shows MeetUniversity branding (`#0073D1` primary, `#243855` navy slate).
> **NARRATOR:**  
> "Every Monday morning, founders and executives drown in raw news, competitor noise, and siloed sales notes.  
> Welcome to **Signal Stack** — an autonomous intelligence engine built for the EDXSO AI Engineer assignment.  
> Signal Stack takes just a company name and URL, autonomously discovers and monitors real web sources, analyzes signals against organizational context, and delivers a rigorous, actionable **Monday Morning Brief**.  
> Every piece of data is backed by verified ground truth — zero hallucinations, zero fabricated data, and 100% free tier."

---

### 2. Setup & Autonomous Initial Research (0:35 – 1:05)
**[VISUAL]:** Click on `/setup`. The registered companies grid shows MeetUniversity, Claude, and Oatly with tactile selection checkboxes. Click **Run AI Research** on MeetUniversity.
> **NARRATOR:**  
> "Setup is effortless. Enter `MeetUniversity` and their URL: `meetuniversity.com`.  
> When we run AI Research, the polite crawler visits the site, parses landing page copy and metadata, and extracts structured facts into our Neon PostgreSQL database.  
> On the Profile page, notice the critical architectural separation: **Verified facts** extracted directly from their website, versus **Assumed hypotheses** flagged for review. Founders can edit or add context at any time."

---

### 3. Adaptive AI Founder Interview (1:05 – 1:45)
**[VISUAL]:** Navigate to `/interview`. Show question 1 rendered with the tactile skeuomorphic input box, progress bar at 10%, and conversation history.
> **NARRATOR:**  
> "Next is the Adaptive 10-Question Interview.  
> Notice that questions are **never hardcoded**. They are dynamically generated based on the company's profile facts.  
> It asks **one question at a time**, remembers previous responses, and triggers intelligent follow-ups when an answer needs clarification.  
> The founder can skip questions, view answered history, and inline-edit any previous answer to steer the intelligence model."

---

### 4. Signal Stack & Source Manager (1:45 – 2:20)
**[VISUAL]:** Navigate to `/signal-stack` and then `/sources`. Display the 4 quadrants: Customers, Competitors, Market, and Internal.
> **NARRATOR:**  
> "Once calibrated, Signal Stack synthesizes the 4-quadrant **Signal Stack**: Customers, Competitors, Market Regulators, and Internal Data.  
> For MeetUniversity, our search engine autonomously discovered **31 real sources**, including competitors like IDP, LeapScholar, and Yocket, plus market bodies like the UK Home Office and DAAD.  
> In the Source Manager, each source displays its discovery rationale, `source_reliability` score, and `strategic_relevance` score.  
> Our crawler checks `robots.txt`, enforces a polite 2.0-second delay, hashes document content with `SHA-256` to prevent duplicate crawls, and logs every request into `crawl_runs`."

---

### 5. Anti-Fabrication Analysis & Feed Ranking (2:20 – 2:55)
**[VISUAL]:** Navigate to `/feed`. Highlight the verbatim evidence snippet card, the confidence breakdown, and filter pills.
> **NARRATOR:**  
> "Here is our Intelligence Feed.  
> To guarantee **zero fabrication**, our analysis pipeline runs an automated anti-hallucination verification: the extracted `evidence_snippet` must exist **verbatim** inside the raw crawled document. If an LLM hallucinates, it's discarded.  
> Signals are ranked using our deterministic 6-factor formula combining relevance, impact, urgency, credibility, recency, and novelty.  
> Users can filter instantly by category, impact, and verification status."

---

### 6. First-Party Internal Intelligence (2:55 – 3:25)
**[VISUAL]:** Click **Upload Internal Data**. Drag and drop `docs/sample-internal-crm.csv`. Show toast notification and the newly extracted signals appearing in the Feed under `INTERNAL`.
> **NARRATOR:**  
> "Competitive intelligence is incomplete without internal ground truth.  
> Users can upload CRM dumps, call transcripts, or lost-deal logs in CSV, Excel, PDF, or text format.  
> Our local parser extracts customer objections, competitor mentions, and product requests — instantly tagging them as verified internal intelligence with a high credibility weighting."

---

### 7. Monday Morning Brief & Action Tracking (3:25 – 4:10)
**[VISUAL]:** Navigate to `/brief`. Show the 10 required sections: Executive Summary, Customer Signals, Competitor Moves, Market & Regulatory, Internal Signals, Opportunities, Risks, Actions This Week, Watchlist, and Source Appendix.
> **NARRATOR:**  
> "Every Monday at 8:00 AM, the engine synthesizes the **Monday Morning Brief**.  
> It contains all 10 required sections from Section 7 of the specification:  
> Top 5 executive bullets, granular sector signals, at least 3 concrete business opportunities, immediate risks, and an assigned **Actions This Week** matrix with owners and deadlines.  
> Executives can update action statuses inline (`Open`, `In Progress`, `Done`), export the brief to Markdown or JSON, and dispatch a beautifully styled HTML brief via Gmail SMTP."

---

### 8. Settings, Scheduler & Stack Health Audit (4:10 – 4:40)
**[VISUAL]:** Navigate to `/settings`. Show briefing schedule controls, manual trigger buttons, the Stack Health dial (`10/100 Needs Maintenance`), and real-time dead URL alerts.
> **NARRATOR:**  
> "The Settings page gives full operational control.  
> You can configure briefing cadence, crawl intervals, and trigger manual pipeline runs on demand.  
> Our **Monthly Signal Stack Audit** automatically tests monitored URLs for 404s, flags duplicate domains, and recommends new high-authority candidate sources.  
> All executions are backed by real GitHub Actions cron workflows (`weekly_brief.yml` and `monthly_audit.yml`) with audit logs tracked in PostgreSQL."

---

### 9. Multi-Industry Reusability & Context Shift (4:40 – 5:00)
**[VISUAL]:** Quick switch to `Oatly` and `Claude` in the setup selector, showing completely distinct sources and signals.
> **NARRATOR:**  
> "Signal Stack is completely domain-agnostic. We tested it on **Claude** in AI/SaaS, and **Oatly** in FMCG food & beverage.  
> Furthermore, when MeetUniversity's strategic context shifted toward European public universities, our context-change engine reassessed all 45 sources, deactivated declining ones, and onboarded European portals like DAAD.de automatically.  
> Thank you — Signal Stack delivers true executive intelligence with zero fluff, zero hallucinations, and zero infrastructure cost."
