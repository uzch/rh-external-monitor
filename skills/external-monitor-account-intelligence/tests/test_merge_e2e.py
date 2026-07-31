"""End-to-end test for merge_external_signals.py"""
import json, sys, os, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from merge_external_signals import merge_signals, recompute_scores, update_envelope

portfolio = {
    "run": {"run_id": "test", "status": "completed", "generated_at": "2026-07-25T18:00:00Z"},
    "scope": {"type": "region", "value": "INTEL"},
    "summary": {
        "account_count": 3,
        "accounts_with_internal_data": 3,
        "accounts_enriched": 1,
        "act_count": 0,
        "watch_count": 0,
        "highest_signal_score": None,
        "text": "Region INTEL contains 3 accounts.",
    },
    "accounts": [
        {"account_name": "Alpha Corp", "account_id": "alpha", "hierarchy": {"geo": "NAPS", "region": "INTEL", "territory_name": "T1", "segment": "Ent"}, "identity": {"match_status": "matched"}, "signal_score": None, "internal_priority_score": 50, "priority_reasons": [], "internal": {"metrics": {}, "risks": [], "next_steps": [], "topics": []}, "summary": None, "recommended_next_move": None, "signals": []},
        {"account_name": "Beta Inc", "account_id": "beta", "hierarchy": {"geo": "NAPS", "region": "INTEL", "territory_name": "T1", "segment": "Ent"}, "identity": {"match_status": "matched"}, "signal_score": None, "internal_priority_score": 30, "priority_reasons": [], "internal": {"metrics": {}, "risks": [], "next_steps": [], "topics": []}, "summary": None, "recommended_next_move": None, "signals": []},
        {"account_name": "Gamma LLC", "account_id": "gamma", "hierarchy": {"geo": "NAPS", "region": "INTEL", "territory_name": "T2", "segment": "Ent"}, "identity": {"match_status": "not_found"}, "signal_score": None, "internal_priority_score": 0, "priority_reasons": [], "internal": {"metrics": {}, "risks": [], "next_steps": [], "topics": []}, "summary": None, "recommended_next_move": None, "signals": []},
    ],
    "_meta": {
        "query_window_days": 120,
        "accounts_in_scope": 3,
        "accounts_enriched": 1,
        "mcp_status": "connected",
        "caveats": ["Previous caveat."],
    },
}

batch = [
    {"account_name": "Alpha Corp", "signals": [
        {"headline": "Alpha acquires rival", "what_changed": "M&A deal", "why_it_matters": "Expansion", "red_hat_relevance": "Infra needs grow", "recommended_action": "Engage CTO", "score": 85, "disposition": "ACT", "source_type": "external_public", "source_url": "https://example.com/alpha", "confidence": "high", "published_at": "2026-07-20"},
        {"headline": "Alpha cloud migration", "what_changed": "Cloud shift", "why_it_matters": "RHEL opportunity", "red_hat_relevance": "OpenShift fit", "recommended_action": "Demo", "score": 72, "disposition": "WATCH", "source_type": "external_public", "source_url": "https://example.com/alpha2", "confidence": "medium", "published_at": "2026-07-18"},
    ]},
    {"account_name": "Beta Inc", "signals": [
        {"headline": "Beta expands APAC", "what_changed": "APAC expansion", "why_it_matters": "New markets", "red_hat_relevance": "Regional support", "recommended_action": "Partner", "score": 65, "disposition": "ACT", "source_type": "external_public", "source_url": "https://example.com/beta", "confidence": "medium", "published_at": "2026-07-15"},
    ]},
]



batches = [batch]
accounts_with_signals, total_signals = merge_signals(portfolio, batches)
recompute_scores(portfolio)
update_envelope(portfolio, accounts_with_signals, total_signals)
merged = portfolio

errors = []

def check(cond, msg):
    if not cond:
        errors.append(msg)
        print(f"  FAIL: {msg}")
    else:
        print(f"  OK: {msg}")

check(merged["summary"]["act_count"] == 2, f"act_count=2 (got {merged['summary']['act_count']})")
check(merged["summary"]["watch_count"] == 1, f"watch_count=1 (got {merged['summary']['watch_count']})")
check(merged["summary"]["total_signals"] == 3, f"total_signals=3 (got {merged['summary']['total_signals']})")
check(merged["summary"]["accounts_with_signals"] == 2, f"accounts_with_signals=2 (got {merged['summary']['accounts_with_signals']})")
check(merged["summary"]["accounts_enriched"] == 2, f"summary.accounts_enriched=2 (got {merged['summary']['accounts_enriched']})")
check(merged["_meta"]["accounts_enriched"] == 2, f"_meta.accounts_enriched=2 synced (got {merged['_meta']['accounts_enriched']})")
check(merged["_meta"]["external_research"] is True, f"external_research=True (got {merged['_meta']['external_research']})")

caveats = merged["_meta"]["caveats"]
research_caveats = [c for c in caveats if "research" in c.lower()]
check(any("2 of 3" in c for c in research_caveats), f"Caveat says 2 of 3 (got: {research_caveats})")
check(not any("all 3" in c.lower() for c in research_caveats), "Caveat does NOT say all accounts")

alpha = [a for a in merged["accounts"] if a["account_name"] == "Alpha Corp"][0]
check(len(alpha["signals"]) == 2, f"Alpha has 2 signals (got {len(alpha['signals'])})")
check(alpha["signal_score"] == 78, f"Alpha signal_score=78 (got {alpha['signal_score']})")

gamma = [a for a in merged["accounts"] if a["account_name"] == "Gamma LLC"][0]
check(len(gamma["signals"]) == 0, f"Gamma has 0 signals (got {len(gamma['signals'])})")
check(gamma["signal_score"] is None, f"Gamma signal_score=None (got {gamma['signal_score']})")


if errors:
    print(f"\n{len(errors)} FAILURES")
    sys.exit(1)
else:
    print("\nAll merge_external_signals checks passed")
