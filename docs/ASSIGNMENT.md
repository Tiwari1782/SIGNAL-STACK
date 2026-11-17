**EDXSO AI ENGINEER INTERN**

Assignment 1 — Signal Stack

**Company Intelligence & Executive Briefing Engine**

| **Assignment Level**    | Easy — relative screening level within this assignment set                                           |
|-------------------------|------------------------------------------------------------------------------------------------------|
| **Submission Deadline** | 48–72 hours from the time the assignment is received                                                 |
| **Submission Format**   | Working application + GitHub repository + screen-recorded demo + documentation                       |
| **Deployment**          | Deployed/live URL preferred; if deployment is not feasible, provide a clearly documented local setup |

# 1. The Problem

Businesses operate in an environment that changes continuously.
Customers discuss problems in different communities, competitors launch
products and change pricing, markets evolve, regulations change, and new
technologies create opportunities and threats. Internal customer
conversations can also reveal problems and opportunities that are not
visible externally.

Most founders monitor these developments manually through newsletters,
LinkedIn, competitor websites, industry news and internal systems. There
is rarely a structured intelligence layer that connects all of this
information to business decisions.

**Your mission:** Build an AI-powered Signal Stack that turns a company
into an intelligent, continuously monitored business. A user should be
able to enter a company name and website, provide business context
through an adaptive interview, identify relevant intelligence sources,
monitor those sources and generate an executive-level Monday Morning
Brief.

# 2. Product Experience

The application should support the following end-to-end workflow:

**Company Setup:** Enter company name and website.

**Initial Research:** Research the company, its products/services,
customer segments, positioning and publicly available context. Clearly
distinguish verified facts from assumptions.

**AI Interview:** Conduct a structured 10-question interview generated
from the company's business and initial research. Questions should not
be identical for every company.

**Signal Stack:** Build relevant intelligence sources across Customers,
Competitors, Market and Internal intelligence. Each source must have a
reason for inclusion.

**Monitoring:** Collect information from selected sources and maintain
historical records.

**Intelligence Analysis:** Identify meaningful developments, assess
relevance and business impact, and distinguish evidence from
interpretation.

**Monday Morning Brief:** Generate an executive report containing
decision-relevant intelligence, opportunities, risks and recommended
actions.

# 3. Adaptive AI Interview

The interview is a critical component. The system must first understand
the company and then generate 10 relevant questions. The questions
should be based on the company's business, industry and initial
research.

The interview should explore areas such as:

- Primary business lines and revenue streams.

- Highest-value customer segments.

- Current customer problems and unmet needs.

- Reasons customers choose the company over alternatives.

- Important competitors or substitutes.

- Major industry and market changes.

- Developments that could materially affect the business.

- Growth priorities over the next 6–12 months.

- Internal business information that should influence decisions.

- Decisions the intelligence system should help the founder make.

These are examples, not a fixed questionnaire.

Interview requirements:

- Ask one question at a time.

- Remember previous answers.

- Avoid repeating questions.

- Generate relevant follow-up questions.

- Allow the user to skip confidential questions.

- Maintain a structured company intelligence profile.

- Allow the founder to edit or update answers later.

# 4. Build the Signal Stack

The system must build four intelligence categories.

**A. Customers**

- Identify where customers discuss the problems the company solves.

- Monitor recurring complaints, questions, unmet needs, alternatives
  considered, expectations and sentiment.

- Capture actual customer language where possible.

- Focus on customer problems rather than simply collecting company
  mentions.

**B. Competitors**

- Identify 5–10 relevant competitors or substitutes.

- Monitor product/service launches, pricing, partnerships, positioning,
  hiring, expansion, technology adoption, reviews and complaints.

- Explain why significant competitor activity matters to the company.

**C. Market**

- Monitor regulatory, industry, economic, technology and market
  developments.

- Examples include policy changes, admission or industry requirements,
  country-level developments, consolidation and major announcements.

- Distinguish general news from developments that materially affect the
  business.

**D. Internal Intelligence**

- Support future/internal inputs such as CRM exports, customer feedback,
  sales call transcripts, meeting transcripts, support conversations,
  internal reports and product feedback.

- Initially support CSV, Excel, PDF and text uploads.

- Identify recurring customer objections, lost-deal reasons, product
  requests, sales patterns and emerging risks.

# 5. Source Intelligence & Monitoring

The system should not blindly monitor large numbers of websites. Each
selected source should be justified.

- Specific: relevant to the company's actual problem space.

- Recent: regularly updated and useful for current intelligence.

- Credible: sufficiently reliable for the type of information being
  collected.

- Every source should have a clear reason for monitoring.

The monitoring layer should visit approved/public sources, collect new
information, identify newly published or changed content, remove
duplicates, classify developments, store evidence and source links, and
maintain historical information.

Respect website terms, robots.txt, rate limits and applicable access
restrictions. Do not bypass authentication or technical protections.

# 6. Intelligence Analysis Engine

Collecting information is not enough. The system must analyse what the
information means for the business.

For significant developments, assess:

- What happened?

- When did it happen?

- What is the source?

- Is it verified?

- Why does it matter?

- Which business area is affected?

- Is it an opportunity, threat or neutral development?

- How urgent is it?

- What should the company consider doing?

The system must clearly distinguish verified developments from its own
strategic interpretation.

# 7. Monday Morning Intelligence Brief

The final output should be a report that a founder or CEO would
genuinely want to read every Monday morning. It should prioritise
decision-relevant intelligence rather than generic news summaries.

Required report structure:

1.  Executive Summary — the five most important developments leadership
    should know.

2.  Customer Signals — emerging problems, recurring complaints, new
    expectations, sentiment and unmet needs.

3.  Competitor Intelligence — what changed, evidence, why it matters and
    potential implications.

4.  Market Intelligence — regulatory, industry, economic, technology and
    major opportunity/threat developments.

5.  Internal Business Intelligence — objections, sales patterns,
    lost-deal insights, product requests and operational issues.

6.  Opportunities Identified — at least three actionable opportunities
    with evidence, impact, next step and priority.

7.  Risks & Threats — important negative developments, possible impact
    and urgency.

8.  Recommended Actions for This Week — prioritised actions with reason
    and suggested owner.

9.  What We Should Watch — early developments that deserve continued
    monitoring.

10. Source Appendix — original source, direct link, publication date,
    discovery date, evidence snippet and verification/confidence status.

If no meaningful development occurred in a category, explicitly say so.
Do not manufacture news to fill the report.

# 8. Intelligence Ranking

Build a mechanism that ranks signals according to their importance.

- Relevance to the company.

- Business impact.

- Urgency.

- Source credibility.

- Recency.

- Novelty.

The system should explain why a signal is important. Maintain separate
measures for source reliability, evidence strength and strategic
relevance. Do not treat an AI confidence score as proof that an event is
true.

# 9. Dashboard

Build a functional web application. At minimum, it should provide:

- Company Setup — company name and URL.

- Company Intelligence Profile — view and edit information gathered
  during the interview.

- AI Interview — interactive 10-question interview with follow-ups.

- Signal Stack — Customers, Competitors, Market and Internal categories
  with source reasons.

- Source Manager — add/remove sources, approve discovered sources, view
  source health/history and duplicates.

- Intelligence Feed — chronological developments with filtering by
  category, competitor, date, relevance, impact and verification status.

- Monday Brief — final executive report, history, evidence links, action
  tracking and export/email-ready output.

- Settings — briefing time, time zone, monitoring frequency, source
  refresh frequency, monthly source-health check and company profile
  updates.

# 10. Automation Requirements

Support two independent automated processes:

**A. Weekly Intelligence Brief**

- Run approved source checks.

- Collect new information.

- Identify changes.

- Analyse significant developments.

- Generate and save the report.

- Make it available for delivery.

**B. Monthly Signal Stack Audit**

- Check dead URLs.

- Identify duplicate or inactive sources.

- Identify sources with declining relevance.

- Identify newly discovered sources.

- Recommend additions and removals.

- Generate a monthly source-health report.

- Log failed scheduled runs and make failures visible in the dashboard.

A user should also be able to trigger a brief manually.

# 11. Mandatory Demonstration

Your primary demonstration must use MeetUniversity
(https://www.meetuniversity.com). The application should demonstrate the
complete workflow:

11. Accept MeetUniversity as the company.

12. Research the website and public information.

13. Generate an initial company profile.

14. Conduct the adaptive 10-question founder interview.

15. Generate a customised Signal Stack.

16. Identify relevant competitors or substitutes.

17. Identify relevant customer, market and regulatory sources.

18. Explain why selected sources are included.

19. Crawl selected sources.

20. Extract and classify new developments.

21. Rank the most important signals.

22. Generate a complete Monday Morning Brief.

The final brief must contain real, traceable information. If live or
historical information is unavailable, state the limitation rather than
creating artificial developments.

# 12. Reusability / Stress Test

A working demonstration on one company is not sufficient. Test the
system with two additional companies from different industries.

Changing the company should result in different:

- Interview questions.

- Customer sources.

- Competitor lists.

- Market sources.

- Signal Stacks.

- Intelligence briefs.

Also change the business context for one company after initial setup.
The system should reassess source relevance, identify sources that are
no longer useful, recommend new sources, update the Signal Stack and
explain what changed.

# 13. Minimum Working Output

- One fully configured company: MeetUniversity.

- Two additional company configurations.

- A 10-question adaptive interview.

- Four functioning Signal Stack categories.

- At least 20 approved sources for MeetUniversity.

- 5–10 competitor profiles.

- At least 30 actual collected intelligence records across the
  demonstrations.

- Source evidence and links for every reported development.

- One complete generated Monday Morning Brief per company.

- Working weekly scheduling mechanism.

- Monthly source-health audit.

- Source addition/removal functionality.

- Historical crawl and brief records.

These are minimum demonstration targets. They are not permission to
populate the system with fabricated data.

# 14. Technical Constraints

- Use free/open-source technologies or genuinely free tiers.

- No paid APIs, paid scraping platforms or paid AI services.

- Use permitted public data sources and respect access restrictions.

- Clearly document any free-tier limitations.

- You may choose your own architecture where the requirements are
  satisfied and the choice is justified.

# 15. Evaluation Criteria

| **Evaluation Area**                              | **Weight** |
|--------------------------------------------------|------------|
| Company understanding and adaptive interview     | 10%        |
| Intelligent source discovery                     | 15%        |
| Quality of Signal Stack and source justification | 15%        |
| Working crawler and monitoring engine            | 15%        |
| Intelligence analysis and strategic relevance    | 20%        |
| Quality of Monday Morning Brief                  | 15%        |
| Automation and source health management          | 5%         |
| Product experience and engineering quality       | 5%         |
| Total                                            | 100%       |

**Automatic failure conditions**

- Static news aggregator presented as an intelligence system.

- Same interview questions for every company.

- Hard-coded competitor lists.

- No actual source crawling.

- No evidence links.

- Fabricated developments.

- Generic AI-generated business recommendations.

- Report only summarises articles without explaining business
  implications.

- No working scheduler.

- UI mockup without a functioning backend.

# 16. Expected Deliverables

23. Working application — deployed/live URL preferred. If deployment is
    not feasible, provide a clearly documented locally runnable version.

24. GitHub repository — complete source code, database/schema files,
    configuration guidance and README.

25. Screen-recorded demonstration — approximately 5–10 minutes, showing
    the end-to-end workflow from company setup to the final brief.

26. Three sample company reports — MeetUniversity plus two additional
    companies.

27. Technical documentation — maximum five pages covering architecture,
    source discovery, crawling, ranking, AI analysis, scheduling and
    reliability.

28. Cost statement — demonstrate use of free/open-source tools or
    genuinely free tiers and disclose service limitations.

29. Test evidence — screenshots, sample outputs or other evidence
    demonstrating the required workflows and minimum targets.

30. Setup instructions — clear steps for running the project and
    reproducing the demonstration.

# 17. Submission Instructions

- Submit the GitHub repository link.

- Submit the deployed/live application URL, if available.

- Submit the screen-recorded demo link/file.

- Include the technical documentation and cost statement in the
  repository or as part of the submission package.

- Ensure the submitted version is functional and matches the
  demonstrated version.

- Do not present mock screens, fabricated records or non-functional
  placeholders as completed functionality.

- Make sure all required links are accessible to the evaluation team.

# 18. Deadline

**48–72 hours from the time the assignment is received.**

Submissions received after the deadline may be considered late unless an
extension has been communicated in advance.

# Final Test

The final evaluation may use a company name and website that you have
not configured before. The system should be able to understand the
business, conduct the interview, build a relevant Signal Stack, discover
and justify sources, collect real intelligence, analyse what matters and
generate a meaningful executive brief without requiring manual
configuration of the competitors, sources or intelligence categories for
every new company.

**Build the product. Demonstrate the intelligence. Show the decisions it
helps a founder make.**
