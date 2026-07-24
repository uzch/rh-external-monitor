#!/usr/bin/env bash
# Verify a Backstory / People.ai Query API packet against the LIVE API.
# Authenticates, POSTs the packet, and reports which requested slugs survived in the returned CSV
# header (invalid slugs/variation_ids are silently dropped). Prints column names only — no row data.
#
# Usage:
#   PEOPLEAI_CLIENT_ID=.. PEOPLEAI_CLIENT_SECRET=.. ./verify-packet.sh packet.json
# Run against a customer tenant by exporting THEIR API key/secret as the two env vars.
#
# Env overrides: PAI_BASE (default https://api.people.ai)
set -uo pipefail
PACKET="${1:?packet.json required}"
BASE="${PAI_BASE:-https://api.people.ai}"
: "${PEOPLEAI_CLIENT_ID:?set PEOPLEAI_CLIENT_ID}"
: "${PEOPLEAI_CLIENT_SECRET:?set PEOPLEAI_CLIENT_SECRET}"
[ -f "$PACKET" ] || { echo "packet not found: $PACKET" >&2; exit 1; }

TOKEN=$(curl -sS -X POST "$BASE/v3/auth/tokens" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode grant_type=client_credentials \
  --data-urlencode "client_id=$PEOPLEAI_CLIENT_ID" \
  --data-urlencode "client_secret=$PEOPLEAI_CLIENT_SECRET" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])') \
  || { echo "auth failed" >&2; exit 1; }

echo "== Requested slugs (from $PACKET) =="
python3 - "$PACKET" <<'PY'
import json, sys
for c in json.load(open(sys.argv[1])).get("columns", []):
    print("  -", c["slug"] + (f"  [{c['variation_id']}]" if c.get("variation_id") else ""))
PY

echo
echo "== Returned columns (valid slugs only) =="
curl -sS --no-buffer -X POST "$BASE/v3/beta/insights/export" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  --data-binary @"$PACKET" 2>/dev/null | head -1 | tr ',' '\n' | nl

echo
echo "Returned names are display labels (not slugs) — match by count/position, not slug string."
echo "Any requested field absent was silently rejected for this tenant — check its slug/variation_id."
echo "If ALL/most columns are absent, re-check individual slugs with validate-slugs.sh (it carries controls)."
