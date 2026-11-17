import os
import json
from ..app.db import query
from ..app.services.brief_generator import generate_brief_for_company

os.makedirs("docs/sample-briefs", exist_ok=True)

companies = query("SELECT id, name, website FROM companies ORDER BY id")
print(f"Found {len(companies)} companies.")

for c in companies:
    cid = c["id"]
    cname = c["name"].lower().replace(" ", "_")
    
    # Check if brief exists, else generate one
    b = query("SELECT * FROM briefs WHERE company_id = %s ORDER BY id DESC LIMIT 1", (cid,), one=True)
    if not b:
        print(f"Generating brief for {c['name']} (ID {cid})...")
        b = generate_brief_for_company(cid, trigger="scheduled")
    
    # Save JSON
    json_path = f"docs/sample-briefs/{cname}_brief.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(b["content"], f, indent=2, default=str)
        
    # Save HTML
    html_path = f"docs/sample-briefs/{cname}_brief.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(b.get("html") or "")
        
    # Generate clean Markdown version
    md_path = f"docs/sample-briefs/{cname}_brief.md"
    content = b.get("content") or {}
    
    md_lines = [
        f"# Monday Morning Executive Brief: {c['name']}",
        f"**Period:** {b.get('period_start')} to {b.get('period_end')} | **Trigger:** {b.get('trigger', 'scheduled')} | **Generated:** {b.get('created_at')}",
        "",
        "## 1. Executive Summary: Top 5 Things That Happened",
    ]
    for item in content.get("executive_summary", []):
        if isinstance(item, dict):
            md_lines.append(f"- **{item.get('title', 'Development')}:** {item.get('description', '')}")
            if item.get("implication"):
                md_lines.append(f"  *Implication:* {item.get('implication')}")
        else:
            md_lines.append(f"- {item}")
            
    md_lines.extend([
        "",
        "## 2. Customer Intelligence",
        f"{content.get('customer_intelligence', {}).get('summary', 'No customer shifts reported.') if isinstance(content.get('customer_intelligence'), dict) else str(content.get('customer_intelligence', ''))}",
        "",
        "## 3. Competitor Moves",
        f"{content.get('competitor_intelligence', {}).get('summary', 'No material competitor moves reported.') if isinstance(content.get('competitor_intelligence'), dict) else str(content.get('competitor_intelligence', ''))}",
    ])
    moves = content.get("competitor_intelligence", {}).get("moves", []) if isinstance(content.get("competitor_intelligence"), dict) else []
    for m in moves:
        if isinstance(m, dict):
            md_lines.append(f"- **{m.get('competitor', 'Competitor')}**: {m.get('move', '')} *(Impact: {m.get('impact', '')})*")
        else:
            md_lines.append(f"- {m}")
        
    md_lines.extend([
        "",
        "## 4. Market & Regulatory Shifts",
        f"{content.get('market_intelligence', {}).get('summary', 'No major regulatory changes reported.') if isinstance(content.get('market_intelligence'), dict) else str(content.get('market_intelligence', ''))}",
        "",
        "## 5. Internal Business Intelligence",
        f"{content.get('internal_intelligence', {}).get('summary', 'No internal uploads recorded.') if isinstance(content.get('internal_intelligence'), dict) else str(content.get('internal_intelligence', ''))}",
        "",
        "## 6. Strategic Opportunities",
    ])
    for opp in content.get("opportunities", []):
        if isinstance(opp, dict):
            md_lines.append(f"- **{opp.get('title', 'Opportunity')}**: {opp.get('description', '')}")
            if opp.get("suggested_action"):
                md_lines.append(f"  *Action:* {opp.get('suggested_action')}")
        else:
            md_lines.append(f"- {opp}")
            
    md_lines.extend([
        "",
        "## 7. Risks & Threats",
    ])
    for r in content.get("risks_and_threats", []):
        if isinstance(r, dict):
            md_lines.append(f"- **{r.get('title', 'Risk')}** ({r.get('severity', 'medium').upper()}): {r.get('description', '')}")
            if r.get("mitigation"):
                md_lines.append(f"  *Mitigation:* {r.get('mitigation')}")
        else:
            md_lines.append(f"- {r}")
            
    md_lines.extend([
        "",
        "## 8. Recommended Actions This Week",
    ])
    for a in content.get("recommended_actions", []):
        if isinstance(a, dict):
            md_lines.append(f"- [ ] **[{a.get('priority', 'P1')}] {a.get('title', 'Action')}** (Owner: {a.get('owner', 'Founder')}) — *{a.get('reason', '')}*")
        else:
            md_lines.append(f"- [ ] {a}")
        
    md_lines.extend([
        "",
        "## 9. Watchlist",
    ])
    for w in content.get("watchlist", []):
        if isinstance(w, dict):
            md_lines.append(f"- **{w.get('item', 'Watch item')}**: {w.get('signal_to_look_for', '')}")
        else:
            md_lines.append(f"- {w}")
        
    md_lines.extend([
        "",
        "## 10. Source Appendix & Verification Auditing",
    ])
    for s in content.get("source_appendix", []):
        if isinstance(s, dict):
            md_lines.append(f"- **{s.get('source_name', 'Source')}** ({s.get('verification_level', 'verified')}): [{s.get('source_url', '')}]({s.get('source_url', '')})")
            if s.get("evidence_snippet"):
                md_lines.append(f"  > \"{s.get('evidence_snippet')}\"")
        else:
            md_lines.append(f"- {s}")
            
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
        
    print(f"Exported {cname}: JSON, HTML, and Markdown.")

print("All briefs exported to docs/sample-briefs/ successfully!")
