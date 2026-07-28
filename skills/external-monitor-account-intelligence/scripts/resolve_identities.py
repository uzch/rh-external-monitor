#!/usr/bin/env python
"""Cache-aware identity resolution for registry accounts.

Two modes:

Resolve mode (default):
    python scripts/resolve_identities.py \
        --accounts scoped-accounts.json \
        --cache data/local/identity-cache.json \
        --out identities.json

    Emits one identity record per account. Cached accounts get their stored
    identity; uncached accounts get identity_status="needs_resolution" with
    a name_variations array of normalized candidates for find_account.

Update mode:
    python scripts/resolve_identities.py \
        --update-cache data/local/identity-cache.json \
        --resolved new-identities.json

    Merges confirmed identities from a resolved identities file back into
    the cache for future runs.

Stdlib only.
"""
import argparse
import json
import os
import re
import sys


LEGAL_SUFFIXES = [
    ", INC.", ", LLC", ", LTD.", ", L.P.", ", L.L.C.",
    " CORPORATION", " CORP.", " CO.", " INC", " LLC", " LTD",
]

REGIONAL_QUALIFIERS = [" - NA", " - US", " - EMEA", " - APAC", " - LATAM"]


def normalize_account_name(name):
    """Generate candidate name variations from an ALL CAPS registry name.

    Returns a list of 2-4 candidates ordered from most specific to least:
    1. Title-cased original
    2. Title-cased with legal suffix stripped
    3. Title-cased with regional qualifier stripped
    4. Title-cased with both stripped
    """
    candidates = []
    seen = set()

    def _add(s):
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            candidates.append(s)

    upper = name.strip()

    stripped_region = upper
    for qual in REGIONAL_QUALIFIERS:
        if stripped_region.upper().endswith(qual):
            stripped_region = stripped_region[: -len(qual)]
            break

    stripped_legal = stripped_region
    for suf in LEGAL_SUFFIXES:
        if stripped_legal.upper().endswith(suf.upper()):
            stripped_legal = stripped_legal[: -len(suf)]
            break

    _add(_title_case(upper))
    _add(_title_case(stripped_region))
    _add(_title_case(stripped_legal))

    return candidates


def _title_case(s):
    """Title-case that preserves common abbreviations and punctuation."""
    words = s.split()
    result = []
    for w in words:
        if re.fullmatch(r"[A-Z]{2,5}", w) and w not in ("THE", "AND", "FOR", "INC", "LLC", "LTD"):
            result.append(w)
        elif w == "-":
            result.append(w)
        elif "." in w and len(w) <= 6:
            result.append(w.upper())
        elif "&" in w:
            result.append(w.title())
        else:
            result.append(w.capitalize())
    return " ".join(result)


def resolve(accounts_path, cache_path, out_path):
    with open(accounts_path, encoding="utf-8") as f:
        accounts = json.load(f)

    cache = {}
    if cache_path and os.path.isfile(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)

    identities = []
    cached_count = 0
    needs_count = 0

    for acct in accounts:
        name = acct["account_name"]
        if name in cache:
            entry = cache[name]
            identities.append({
                "registry_account_name": name,
                "query_account_name": entry["query_account_name"],
                "peopleai_account_id": entry["peopleai_account_id"],
                "identity_status": entry["identity_status"],
                "identity_notes": entry.get("identity_notes", "resolved from cache"),
            })
            cached_count += 1
        else:
            variations = normalize_account_name(name)
            identities.append({
                "registry_account_name": name,
                "query_account_name": None,
                "peopleai_account_id": None,
                "identity_status": "needs_resolution",
                "identity_notes": f"not in cache; try name variations: {variations}",
                "name_variations": variations,
            })
            needs_count += 1

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(identities, f, indent=1, ensure_ascii=False)

    print(f"Resolved: {cached_count} from cache, {needs_count} need resolution")
    print(f"Written to {out_path}")
    if needs_count:
        print(f"\nAccounts needing resolution:", file=sys.stderr)
        for rec in identities:
            if rec["identity_status"] == "needs_resolution":
                print(f"  {rec['registry_account_name']}  ->  {rec.get('name_variations', [])}", file=sys.stderr)


def update_cache(cache_path, resolved_path):
    cache = {}
    if os.path.isfile(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)

    with open(resolved_path, encoding="utf-8") as f:
        resolved = json.load(f)

    added = 0
    for rec in resolved:
        if rec.get("identity_status") == "confirmed":
            name = rec["registry_account_name"]
            cache[name] = {
                "query_account_name": rec["query_account_name"],
                "peopleai_account_id": rec["peopleai_account_id"],
                "identity_status": "confirmed",
                "identity_notes": rec.get("identity_notes", ""),
            }
            added += 1

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    print(f"Cache updated: {added} identities merged, {len(cache)} total entries")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--accounts", help="Path to scoped-accounts.json (resolve mode)")
    ap.add_argument("--cache", help="Path to identity-cache.json")
    ap.add_argument("--out", help="Output path for identities (resolve mode)")
    ap.add_argument("--update-cache", dest="update_cache_path",
                    help="Path to identity-cache.json (update mode)")
    ap.add_argument("--resolved", help="Path to resolved identities file (update mode)")
    args = ap.parse_args()

    if args.update_cache_path and args.resolved:
        update_cache(args.update_cache_path, args.resolved)
    elif args.accounts and args.out:
        resolve(args.accounts, args.cache, args.out)
    else:
        ap.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
