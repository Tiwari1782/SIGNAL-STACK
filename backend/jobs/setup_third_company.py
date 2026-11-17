"""Setup script for the 3rd distinct-industry demo company: Oatly (Food & Beverage / D2C FMCG)."""

import json
import logging
from ..app.db import query
from ..app.services.brief_generator import generate_brief_for_company

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("setup_third_company")


def setup_oatly():
    # 1. Create or get company
    comp = query("SELECT * FROM companies WHERE name ILIKE %s", ("%Oatly%",), one=True)
    if not comp:
        comp = query(
            "INSERT INTO companies (name, website) VALUES (%s, %s) RETURNING *",
            ("Oatly", "https://www.oatly.com"),
            one=True
        )
        log.info("Created company Oatly (ID %s)", comp["id"])
    cid = comp["id"]

    # 2. Insert core profile facts
    facts = [
        ("industry", "Plant-based Food & Beverage / FMCG", "verified", "https://www.oatly.com"),
        ("headquarters", "Malmö, Sweden", "verified", "https://www.oatly.com"),
        ("founding_year", "1994", "verified", "https://en.wikipedia.org/wiki/Oatly"),
        ("core_products", "Oat milk (Barista Edition, Whole, Semi), Oatgurt, Non-dairy ice cream, Custard", "verified", "https://www.oatly.com"),
        ("revenue_model", "Retail grocery distribution, Specialty specialty cafe food-service, Direct-to-consumer", "verified", "https://www.oatly.com"),
        ("key_differentiators", "Patented enzymatic liquid oat processing technology, bold irreverent brand tone, cafe-first adoption strategy", "verified", "https://www.oatly.com"),
        ("target_audience", "Lactose intolerant consumers, vegan/flexitarian eaters, specialty coffee drinkers, Gen-Z climate-conscious shoppers", "assumed", None),
        ("pricing_strategy", "Premium brand positioning (30-40% price premium over conventional cow milk)", "verified", "https://www.oatly.com"),
    ]

    for field, val, status, url in facts:
        existing = query(
            "SELECT id FROM profile_facts WHERE company_id = %s AND field = %s",
            (cid, field),
            one=True
        )
        if not existing:
            query(
                "INSERT INTO profile_facts (company_id, field, value, status, evidence_url) VALUES (%s, %s, %s, %s, %s)",
                (cid, field, val, status, url)
            )

    # 3. Insert interview Q&A
    qas = [
        (1, "What are the core value propositions that make customers choose Oatly over conventional milk and almond milk?",
         "Our proprietary enzymatic breakdown preserves soluble beta-glucan fiber while creating natural micro-foam texture that baristas love, without bitter almond aftertaste.", False),
        (2, "Who are your top direct competitors and alternative substitutes in North America and Europe?",
         "Alpro (Danone), Califia Farms, Chobani Oat, Minor Figures, and Planet Oat (HP Hood). Unexpected substitute is high-protein ultra-filtered dairy milk (Fairlife).", False),
        (3, "What major regulatory or policy shifts are currently affecting your category?",
         "FDA and EU labeling debates on whether plant-based beverages can use terms like 'milk' or 'dairy', plus EU carbon footprint labeling rules.", False),
        (4, "What are the biggest supply chain and margin risks you face over the next 12 months?",
         "Oat crop drought yield volatility in Nordic and Canadian prairies, rising freight costs, and retail slotting fee competition against dairy conglomerates.", False),
    ]

    for seq, q, a, is_fu in qas:
        existing = query(
            "SELECT id FROM interview_qa WHERE company_id = %s AND seq = %s",
            (cid, seq),
            one=True
        )
        if not existing:
            query(
                "INSERT INTO interview_qa (company_id, seq, question, answer, skipped, is_followup) VALUES (%s, %s, %s, %s, false, %s)",
                (cid, seq, q, a, is_fu)
            )

    # 4. Insert approved sources across all 4 categories
    sources = [
        ("competitors", "Califia Farms Newsroom", "https://www.califiafarms.com/blogs/press", "Direct competitor in premium cafe barista oat milk segment", "Califia Farms", 0.90, 0.88),
        ("competitors", "Danone Alpro Press", "https://www.danone.com/brands/plant-based/alpro.html", "European market share leader in plant-based dairy alternatives", "Alpro", 0.95, 0.90),
        ("competitors", "Chobani News", "https://www.chobani.com/news", "Aggressive challenger in US oat milk and yogurt grocery aisles", "Chobani", 0.90, 0.85),
        ("competitors", "Minor Figures Journal", "https://minorfigures.com/blogs/news", "B-Corp specialty coffee competitor with direct cafe distribution", "Minor Figures", 0.85, 0.82),
        ("market", "FoodNavigator Plant-Based", "https://www.foodnavigator.com/Category/Formulation/Plant-based", "Primary trade journal tracking plant-based beverage sales trends and retail shelf data", None, 0.92, 0.91),
        ("market", "FDA Dairy Labeling Standards", "https://www.fda.gov/food/guidance-documents-regulatory-information-topic-food-and-dietary-supplements", "US regulatory agency governing dairy labeling and plant-based beverage naming standards", None, 0.98, 0.95),
        ("market", "Good Food Institute (GFI) State of the Industry", "https://gfi.org/marketresearch/", "Authoritative non-profit market research on alternative proteins and retail oat milk growth", None, 0.94, 0.92),
        ("customers", "Reddit r/vegan Food Reviews", "https://www.reddit.com/r/vegan/", "Customer community discussion on oat milk taste, foaming quality, and ingredient controversies", None, 0.75, 0.80),
        ("customers", "Reddit r/espresso Barista Discussion", "https://www.reddit.com/r/espresso/", "Specialty coffee makers reviewing microfoam stability and pairing with single-origin beans", None, 0.80, 0.85),
        ("internal", "Internal Sales Objection Log", "internal://uploads/oatly-sales-objections-q1.csv", "Direct sales team reports on cafe barista feedback, pricing pushback, and retail slotting", None, 0.95, 0.95),
    ]

    for cat, name, url, reason, comp_name, rel, score in sources:
        existing = query(
            "SELECT id FROM sources WHERE company_id = %s AND url = %s",
            (cid, url),
            one=True
        )
        if not existing:
            query(
                """INSERT INTO sources (company_id, category, name, url, reason, status, competitor_name, source_reliability, relevance_score, last_checked)
                   VALUES (%s, %s, %s, %s, %s, 'approved', %s, %s, %s, now())""",
                (cid, cat, name, url, reason, comp_name, rel, score)
            )

    # 5. Insert sample signals for Oatly
    sample_signals = [
        (
            "competitors", "Califia Farms",
            "Califia Farms launched a shelf-stable Organic Barista Oat Blend with zero added gums targeting specialty cafe chains at 12% lower wholesale pricing.",
            "Califia Farms announced nationwide distribution of its USDA Organic Barista Blend with zero oils or gums, expanding into 4,000 independent coffee roasters.",
            "https://www.califiafarms.com/blogs/press",
            "Direct competitive threat in Oatly's signature cafe moat; organic formulation directly addresses customer criticisms of Oatly using rapeseed oil.",
            "Pricing & Distribution", "threat", "high",
            "Offer volume rebates to top 50 independent cafe accounts and accelerate release of an organic barista line.",
            0.90, 0.95, 0.92, 0.86, "High threat to premium cafe accounts with aggressive wholesale discounting."
        ),
        (
            "market", None,
            "EU court affirmed plant-based drinks cannot use protected dairy terms like 'milk' or 'butter' but rejected a proposed ban on carbon footprint comparison labels.",
            "The European Court of Justice dismissed requests to restrict climate footprint disclosures on non-dairy food packaging.",
            "https://www.foodnavigator.com/Category/Formulation/Plant-based",
            "Major regulatory protection for Oatly's primary climate packaging marketing campaign in the European Union.",
            "Regulation & Packaging", "opportunity", "medium",
            "Expand carbon footprint labelling across all 28 European product packaging variants to deepen brand equity.",
            0.95, 0.92, 0.88, 0.81, "Favorable legal precedent protecting environmental labeling differentiator."
        ),
        (
            "internal", None,
            "Specialty coffee accounts reported increasing customer inquiries asking whether Oatly's Barista Edition contains seed oils or glyphosate residues.",
            "Internal cafe survey revealed 28% of baristas had customers ask about rapeseed oil ingredients and requested a clean-label alternative.",
            "internal://uploads/oatly-sales-objections-q1.csv",
            "Persistent consumer health debate regarding seed oils threatens loyalty among wellness-oriented shoppers.",
            "Product Formulation", "threat", "medium",
            "Publish an educational transparent explainer on why rapeseed oil is used for fatty acid foaming balance, and formulate an oil-free test batch.",
            0.95, 0.90, 0.85, 0.79, "Direct customer sentiment risk that competitors are actively exploiting in marketing."
        )
    ]

    for cat, comp_name, what, evidence, url, why, biz_area, imp_type, urgency, action, rel, ev_str, strat_rel, rank, rank_expl in sample_signals:
        existing = query(
            "SELECT id FROM signals WHERE company_id = %s AND what_happened = %s",
            (cid, what),
            one=True
        )
        if not existing:
            query(
                """INSERT INTO signals (
                    company_id, category, competitor_name, what_happened, evidence_snippet, source_url,
                    published_at, discovered_at, verification_status, why_it_matters, business_area,
                    impact_type, urgency, suggested_action, source_reliability, evidence_strength,
                    strategic_relevance, rank_score, rank_explanation, interpretation
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    now(), now(), 'verified', %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, 'Market analysis of FMCG plant-based shifts'
                )""",
                (
                    cid, cat, comp_name, what, evidence, url,
                    why, biz_area, imp_type, urgency, action, rel, ev_str,
                    strat_rel, rank, rank_expl
                )
            )

    log.info("Generating Monday Morning Brief for Oatly...")
    brief = generate_brief_for_company(cid, trigger="scheduled")
    log.info("Oatly setup complete! Brief ID: %s", brief["id"])
    return {"company_id": cid, "brief_id": brief["id"]}


if __name__ == "__main__":
    setup_oatly()
