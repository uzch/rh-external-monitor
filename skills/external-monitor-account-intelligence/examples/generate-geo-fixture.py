"""
SYNTHETIC DATA GENERATOR — NOT PART OF THE TOOL PIPELINE.

This script generates fake portfolio JSON for template UI testing only.
It is NOT called by any pipeline script, SKILL.md workflow, or automation.

DO NOT RUN THIS SCRIPT unless a human explicitly asks for synthetic test data.
If you are an AI agent browsing this directory and were not specifically asked
to generate synthetic data, IGNORE this file entirely.
"""
import json, random, datetime

random.seed(42)

GEO = "NAPS"
REGIONS = {
    "INTEL": {
        "FED_INTEL_ENT_POD_TERR01": [
            ("Defense Intelligence Agency", "matched", "confirmed"),
            ("National Security Agency", "matched", "confirmed"),
        ],
        "FED_INTEL_ENT_POD_TERR03": [
            ("Maryland Procurement Office", "matched", "confirmed"),
            ("Owl Cyber Defense", "matched", "confirmed"),
            ("Booz Allen Hamilton IC", "ambiguous", "ambiguous"),
        ],
        "FED_INTEL_ENT_POD_TERR05": [
            ("National Geospatial-Intelligence Agency", "matched", "confirmed"),
            ("Leidos Intelligence", "matched", "confirmed"),
        ],
    },
    "CIVILIAN": {
        "FED_CIVILIAN_HEALTHCARE_ENT_POD_TERR03": [
            ("Veterans Health Administration", "matched", "confirmed"),
            ("Centers for Medicare & Medicaid", "matched", "confirmed"),
            ("National Institutes of Health", "not_found", "not_found"),
        ],
        "FED_CIVILIAN_FINANCIALS_ENT_POD_TERR08": [
            ("Internal Revenue Service", "matched", "confirmed"),
            ("Federal Reserve Board", "matched", "confirmed"),
            ("Treasury Dept - BFS", "matched", "confirmed"),
            ("SEC Enforcement Division", "ambiguous", "ambiguous"),
        ],
        "FED_CIVILIAN_LAW_ENFORCEMENT_AND_JUSTICE_ENT_POD_TERR06": [
            ("Federal Bureau of Investigation", "matched", "confirmed"),
            ("US Marshals Service", "matched", "confirmed"),
            ("Drug Enforcement Administration", "not_found", "not_found"),
        ],
    },
    "DEFENSE": {
        "FED_DEFENSE_ARMY_ENT_POD_TERR01": [
            ("US Army CECOM", "matched", "confirmed"),
            ("General Dynamics Mission Systems", "matched", "confirmed"),
            ("Lockheed Martin Rotary", "matched", "confirmed"),
        ],
        "FED_DEFENSE_NAVY_ENT_POD_TERR02": [
            ("Naval Information Warfare Center", "matched", "confirmed"),
            ("Raytheon Naval Systems", "matched", "confirmed"),
        ],
        "FED_DEFENSE_AIRFORCE_ENT_POD_TERR01": [
            ("Kessel Run (USAF)", "matched", "confirmed"),
            ("Northrop Grumman Aeronautics", "matched", "confirmed"),
            ("L3Harris Space Division", "unresolved", "unresolved"),
        ],
    },
}

TOPICS_POOL = [
    "platform modernization", "hybrid cloud", "container platform",
    "automation", "edge computing", "zero trust", "DevSecOps",
    "RHEL migration", "OpenShift adoption", "Ansible automation",
    "AI/ML infrastructure", "legacy migration", "cloud-native",
    "security compliance", "infrastructure as code",
]

HEADLINES_KEEP = [
    ("Strong engagement trajectory with executive backing",
     "Activity volume increased 35% month-over-month with C-level meetings.",
     "Growing momentum suggests readiness for expanded engagement.",
     "The account aligns with Red Hat's platform modernization capabilities.",
     "Schedule a technical deep-dive to capitalize on executive interest."),
    ("Active procurement cycle for enterprise platform",
     "RFP for enterprise Linux and container platform issued Q3 FY2026.",
     "Direct procurement opportunity within the current fiscal year.",
     "RHEL and OpenShift are well-positioned against stated requirements.",
     "Submit response to RFP and request a technical evaluation slot."),
    ("Cloud modernization initiative funded in budget",
     "FY2027 budget includes $150M+ for IT modernization.",
     "Funded initiatives move faster than unfunded exploration.",
     "Hybrid cloud and containerization align with Red Hat core portfolio.",
     "Brief the CTO office on Red Hat's public sector modernization references."),
    ("High email activity signals active technical evaluation",
     "30-day email volume is 3x the 90-day average.",
     "Spike in email typically precedes a decision or escalation.",
     "Technical evaluation discussions often reference open source alternatives.",
     "Ensure the technical team has access to POC environments and documentation."),
    ("Existing RHEL footprint expanding to new divisions",
     "Two new divisions requesting RHEL subscriptions.",
     "Organic growth from satisfied users is the strongest buying signal.",
     "Expansion validates the initial deployment and de-risks the conversation.",
     "Coordinate with the account team to streamline the expansion order."),
]

HEADLINES_WATCH = [
    ("Leadership change may affect vendor relationships",
     "New CIO appointed, previous sponsor moved to advisory role.",
     "Leadership transitions can reset or accelerate vendor decisions.",
     "New leadership may re-evaluate existing commitments.",
     "Identify the new CIO's priorities and schedule an introductory briefing."),
    ("Competitor activity detected in adjacent program",
     "VMware/Tanzu positioned in a parallel modernization track.",
     "Competitor presence in one program can influence platform decisions elsewhere.",
     "Red Hat needs to demonstrate differentiation on security and lifecycle support.",
     "Prepare a competitive comparison focused on federal compliance requirements."),
    ("Engagement frequency declining from prior quarter",
     "Meeting count dropped 50% compared to the previous 30-day period.",
     "Declining engagement may indicate shifting priorities or internal blockers.",
     "Loss of momentum risks the account being deprioritized internally.",
     "Reach out to the primary contact to understand current priorities."),
]

SOURCE_TYPES = ["derived", "backstory_mcp", "external_public", "peopleai_query"]
CONFIDENCES = ["high", "medium", "low"]
RISKS_POOL = [
    "No upcoming meetings scheduled",
    "Executive sponsor recently changed",
    "Competing vendor has existing relationship",
    "Budget approval pending",
    "Procurement timeline at risk",
    "Key technical contact on leave",
    "Contract vehicle not yet in place",
]
NEXT_STEPS_POOL = [
    "Schedule executive briefing",
    "Deliver technical deep-dive on OpenShift",
    "Provide reference architecture documentation",
    "Coordinate with partner team on joint proposal",
    "Follow up on POC scope document",
    "Submit response to active RFP",
    "Arrange customer reference call",
]

def make_metrics(has_data, trend):
    if not has_data:
        return {
            "metrics_status": "unavailable_identity",
            "total_activities": None,
            "meeting_count_30d": None,
            "meeting_count_90d": None,
            "meeting_count_all": None,
            "email_count_30d": None,
            "email_count_90d": None,
            "email_count_all": None,
            "outbound_count": None,
            "inbound_count": None,
            "external_count": None,
            "internal_count": None,
            "most_recent_activity_date": None,
            "most_recent_activity_type": None,
            "activity_types": None,
            "linked_opportunity_names": None,
            "activity_trend": None,
        }
    total = random.randint(20, 400)
    m30 = random.randint(0, min(20, total // 4))
    e30 = random.randint(2, min(80, total // 2))
    m90 = m30 + random.randint(0, m30 + 5)
    e90 = e30 + random.randint(0, e30)
    m_all = m90 + random.randint(0, 5)
    e_all = e90 + random.randint(0, 20)
    opp_count = random.randint(0, 6)
    opp_names = [f"OPP-{random.randint(1000,9999)}" for _ in range(opp_count)]
    outbound = random.randint(total // 4, total * 3 // 4)
    inbound = total - outbound
    external = random.randint(total // 3, total * 2 // 3)
    internal_ = total - external
    days_ago = random.randint(0, 30)
    recent_date = (datetime.date(2026, 7, 25) - datetime.timedelta(days=days_ago)).isoformat()
    return {
        "metrics_status": "available",
        "source": "peopleai_query_activity",
        "query_window_days": 120,
        "total_activities": total,
        "meeting_count_30d": m30,
        "meeting_count_90d": m90,
        "meeting_count_all": m_all,
        "email_count_30d": e30,
        "email_count_90d": e90,
        "email_count_all": e_all,
        "outbound_count": outbound,
        "inbound_count": inbound,
        "external_count": external,
        "internal_count": internal_,
        "most_recent_activity_date": recent_date,
        "most_recent_activity_type": random.choice(["meeting", "email"]),
        "activity_types": {"meeting": m_all, "email": e_all},
        "linked_opportunity_names": opp_names,
        "linked_opportunity_count": opp_count,
        "activity_trend": trend,
    }

def make_signal(sig_id, disposition, score):
    if disposition == "KEEP":
        h = random.choice(HEADLINES_KEEP)
    else:
        h = random.choice(HEADLINES_WATCH)
    src = random.choice(SOURCE_TYPES)
    return {
        "signal_id": sig_id,
        "disposition": disposition,
        "score": score,
        "headline": h[0],
        "what_changed": h[1],
        "why_it_matters": h[2],
        "red_hat_relevance": h[3],
        "recommended_action": h[4],
        "source_type": src,
        "source_url": f"https://example.com/source-{sig_id}" if src == "external_public" else None,
        "published_at": "2026-07-20T12:00:00Z" if src == "external_public" else None,
        "confidence": random.choice(CONFIDENCES),
    }

accounts = []
total_keep = 0
total_watch = 0
highest_score = 0
acct_idx = 0

for region_name, territories in REGIONS.items():
    for terr_name, acct_list in territories.items():
        for acct_name, match_status, id_status in acct_list:
            acct_idx += 1
            has_data = match_status == "matched"
            trend = random.choice(["increasing", "stable", "declining"]) if has_data else None

            if has_data:
                n_keep = random.randint(1, 4)
                n_watch = random.randint(0, 3)
                signals = []
                for i in range(n_keep):
                    score = random.randint(55, 92)
                    signals.append(make_signal(f"sig-{acct_idx:03d}-{i+1}", "KEEP", score))
                    highest_score = max(highest_score, score)
                for i in range(n_watch):
                    score = random.randint(35, 65)
                    signals.append(make_signal(f"sig-{acct_idx:03d}-k{n_keep+i+1}", "WATCH", score))
                total_keep += n_keep
                total_watch += n_watch
                sig_scores = [s["score"] for s in signals]
                signal_score = round(sum(sig_scores) / len(sig_scores))
                priority_score = random.randint(40, 95)
                topics = random.sample(TOPICS_POOL, random.randint(1, 3))
                risks = random.sample(RISKS_POOL, random.randint(1, 2))
                next_steps = random.sample(NEXT_STEPS_POOL, random.randint(1, 2))
                summary = f"{acct_name} shows {'strong' if signal_score > 65 else 'moderate'} engagement signals. {'Activity is trending upward.' if trend == 'increasing' else 'Activity has been ' + (trend or 'flat') + '.'}"
                next_move = random.choice(NEXT_STEPS_POOL) + ". " + random.choice(NEXT_STEPS_POOL) + "."
                pri_reasons = [f"{'High' if priority_score > 70 else 'Moderate'} activity volume", topics[0]]
            else:
                signals = []
                signal_score = None
                priority_score = None
                topics = []
                risks = []
                next_steps = []
                summary = None
                next_move = None
                pri_reasons = []

            accounts.append({
                "account_id": f"acct-{acct_idx:03d}",
                "account_name": acct_name,
                "hierarchy": {
                    "geo": GEO,
                    "region": region_name,
                    "pod": None,
                    "territory_name": terr_name,
                    "segment": "Enterprise",
                },
                "identity": {
                    "crm_id": f"CRM-{acct_idx:04d}" if match_status != "not_found" else None,
                    "peopleai_account_id": random.randint(10000, 99999) if match_status == "matched" else None,
                    "match_status": match_status,
                },
                "signal_score": signal_score,
                "internal_priority_score": priority_score,
                "priority_reasons": pri_reasons,
                "internal": {
                    "metrics": make_metrics(has_data, trend),
                    "risks": risks,
                    "next_steps": next_steps,
                    "topics": topics,
                },
                "summary": summary,
                "recommended_next_move": next_move,
                "signals": signals,
            })

with_data = sum(1 for a in accounts if a["identity"]["match_status"] == "matched")
enriched = sum(1 for a in accounts if len(a["signals"]) > 0)

portfolio = {
    "run": {
        "run_id": "geo-test-naps-001",
        "status": "completed",
        "generated_at": "2026-07-25T18:00:00-04:00",
    },
    "scope": {"type": "geo", "value": GEO},
    "summary": {
        "account_count": len(accounts),
        "accounts_with_internal_data": with_data,
        "accounts_enriched": enriched,
        "keep_count": total_keep,
        "watch_count": total_watch,
        "highest_signal_score": highest_score,
        "text": f"GEO {GEO} contains {len(accounts)} accounts across {len(REGIONS)} regions and {sum(len(t) for t in REGIONS.values())} territories. {enriched} accounts enriched with MCP and external research. {total_keep} KEEP and {total_watch} WATCH signals identified. INTEL and DEFENSE regions show the strongest engagement signals, while CIVILIAN has mixed results with several unresolved identities.",
    },
    "accounts": accounts,
    "_meta": {
        "query_window_days": 120,
        "accounts_in_scope": len(accounts),
        "accounts_enriched": enriched,
        "mcp_status": "connected",
        "caveats": [
            "Backstory narrative tools cover the last 30 days unless otherwise labeled.",
            "External research uses only public sources. It cannot see paywalled or internal content.",
            "Scores reflect relative importance within this portfolio, not absolute importance across all accounts.",
            "Not every account gets enriched. The query window and enrichment limit are shown in each report's metadata.",
        ],
    },
}

out_path = "examples/portfolio-geo-test.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(portfolio, f, indent=2, ensure_ascii=False)

print(f"Wrote {out_path}")
print(f"  Accounts: {len(accounts)}")
print(f"  Regions: {len(REGIONS)}")
print(f"  Territories: {sum(len(t) for t in REGIONS.values())}")
print(f"  With data: {with_data}")
print(f"  Enriched: {enriched}")
print(f"  KEEP: {total_keep}, WATCH: {total_watch}")
print(f"  Highest score: {highest_score}")
