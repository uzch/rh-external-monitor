#!/usr/bin/env bash
# Smoke test for the rh-external-monitor skill bundle.
# Validates that all Python scripts parse, the example portfolio validates
# against the schema, and the HTML renderer produces output.
#
# Usage: bash .claude/skills/run-rh-external-monitor/smoke.sh
# On Windows (Git Bash): bash .claude/skills/run-rh-external-monitor/smoke.sh
#
# Does NOT call any live APIs or MCP endpoints.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

PY=python
command -v "$PY" >/dev/null 2>&1 || { echo "FAIL: python not found"; exit 1; }

PASS=0
FAIL=0

check() {
    local label="$1"; shift
    if "$@" >/dev/null 2>&1; then
        echo "  OK  $label"
        PASS=$((PASS + 1))
    else
        echo "  FAIL $label"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== rh-external-monitor smoke test ==="
echo ""

echo "-- Python scripts compile --"
check "load_registry.py"      "$PY" -m py_compile skills/external-monitor-account-intelligence/scripts/load_registry.py
check "validate_portfolio.py" "$PY" -m py_compile skills/external-monitor-account-intelligence/scripts/validate_portfolio.py
check "render_portfolio.py"   "$PY" -m py_compile skills/external-monitor-account-intelligence/scripts/render_portfolio.py
check "pull_sales_data.py"    "$PY" -m py_compile skills/people-ai/sales-data-pull/scripts/pull_sales_data.py
check "run_query.py"          "$PY" -m py_compile skills/people-ai/sales-data-explorer/scripts/run_query.py
check "rest_query.py"         "$PY" -m py_compile skills/people-ai/sales-data-explorer/scripts/rest_query.py
check "aggregate_activity_metrics.py" "$PY" -m py_compile skills/external-monitor-account-intelligence/scripts/aggregate_activity_metrics.py
check "build_portfolio.py"            "$PY" -m py_compile skills/external-monitor-account-intelligence/scripts/build_portfolio.py
check "enrich_portfolio.py"           "$PY" -m py_compile skills/external-monitor-account-intelligence/scripts/enrich_portfolio.py
check "resolve_identities.py"        "$PY" -m py_compile skills/external-monitor-account-intelligence/scripts/resolve_identities.py
check "merge_external_signals.py"    "$PY" -m py_compile skills/external-monitor-account-intelligence/scripts/merge_external_signals.py
check "export_sheets.py"              "$PY" -m py_compile skills/external-monitor-account-intelligence/scripts/export_sheets.py
check "merge_signals.py"      "$PY" -m py_compile skills/people-ai/sales-insights/scripts/merge_signals.py

echo ""
echo "-- Python dependencies --"
check "jsonschema importable" "$PY" -c "import jsonschema"
check "openpyxl importable"   "$PY" -c "import openpyxl"

echo ""
echo "-- Portfolio validation --"
check "example validates" "$PY" skills/external-monitor-account-intelligence/scripts/validate_portfolio.py \
    skills/external-monitor-account-intelligence/examples/portfolio-output.example.json

echo ""
echo "-- Portfolio rendering --"
TMPOUT=$(mktemp -d)
trap "rm -rf $TMPOUT" EXIT
check "example renders" "$PY" skills/external-monitor-account-intelligence/scripts/render_portfolio.py \
    skills/external-monitor-account-intelligence/examples/portfolio-output.example.json \
    --out "$TMPOUT/portfolio-demo.html"
if [ -f "$TMPOUT/portfolio-demo.html" ]; then
    SIZE=$(wc -c < "$TMPOUT/portfolio-demo.html")
    echo "       rendered HTML: $SIZE bytes"
fi

echo ""
echo "-- Registry check --"
if [ -f "data/local/Enterprise Accounts.csv" ]; then
    check "registry loads" "$PY" skills/external-monitor-account-intelligence/scripts/load_registry.py --list-geos
else
    echo "  WARN Enterprise Accounts CSV not found at data/local/Enterprise Accounts.csv"
fi

echo ""
echo "-- Credential check --"
if [ -n "${PEOPLEAI_CLIENT_ID:-}" ] && [ -n "${PEOPLEAI_CLIENT_SECRET:-}" ]; then
    echo "  OK  PEOPLEAI_CLIENT_ID and PEOPLEAI_CLIENT_SECRET are set in environment"
    PASS=$((PASS + 1))
elif [ -f skills/people-ai/sales-data-pull/scripts/peopleai-key.local.json ]; then
    echo "  OK  peopleai-key.local.json found"
    PASS=$((PASS + 1))
else
    echo "  WARN No credentials configured yet (set env vars or create peopleai-key.local.json)"
fi

echo ""
echo "-- Skill discovery --"
for skill in external-monitor-account-intelligence sales-data-explorer sales-data-pull sales-insights; do
    check "/\$skill discoverable" test -f ".claude/skills/$skill/SKILL.md"
done

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
