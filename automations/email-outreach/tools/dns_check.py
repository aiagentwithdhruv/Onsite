#!/usr/bin/env python3
"""
DNS Check — Verify SPF, DKIM, DMARC for Onsite email domains.
Usage: python tools/dns_check.py --domains "onsitesteam.com,onsiteteams.online"
"""

import argparse
import json
import subprocess
import sys


def dig_record(domain, record_type, name=None):
    query = name if name else domain
    try:
        result = subprocess.run(
            ["dig", "+short", query, record_type],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        try:
            result = subprocess.run(
                ["nslookup", "-type=" + record_type, query],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip()
        except Exception:
            return ""


def check_spf(domain):
    txt_records = dig_record(domain, "TXT")
    spf_found = None
    for line in txt_records.split("\n"):
        clean = line.strip('"').strip()
        if clean.startswith("v=spf1"):
            spf_found = clean
            break

    if not spf_found:
        return {"status": "MISSING", "record": None,
                "fix": f"Add TXT record:\nv=spf1 include:zoho.in include:_spf.instantly.ai ~all",
                "priority": "CRITICAL"}

    has_zoho = "zoho.in" in spf_found or "zoho.com" in spf_found
    has_instantly = "instantly" in spf_found
    issues = []
    if not has_zoho:
        issues.append("Missing include:zoho.in")
    if not has_instantly:
        issues.append("Missing include:_spf.instantly.ai")

    if issues:
        return {"status": "INCOMPLETE", "record": spf_found, "issues": issues,
                "fix": f"Update TXT record:\nv=spf1 include:zoho.in include:_spf.instantly.ai ~all",
                "priority": "HIGH"}

    return {"status": "OK", "record": spf_found, "priority": "NONE"}


def check_dkim(domain):
    selectors = ["zoho", "zmail", "default", "google", "selector1", "selector2", "instantly"]
    found = []
    for sel in selectors:
        result = dig_record(f"{sel}._domainkey.{domain}", "TXT")
        if result and ("DKIM" in result.upper() or "v=DKIM1" in result or "p=" in result):
            found.append({"selector": sel, "record": result[:100] + "..."})

    if not found:
        return {"status": "MISSING", "records": [],
                "fix": f"Enable DKIM in Zoho Mail Admin → Domain → DKIM → add selector 'zoho' for {domain}",
                "priority": "HIGH"}
    return {"status": "OK", "records": found, "priority": "NONE"}


def check_dmarc(domain):
    result = dig_record(f"_dmarc.{domain}", "TXT")
    if not result or "v=DMARC1" not in result:
        return {"status": "MISSING", "record": None,
                "fix": f"Add TXT record _dmarc.{domain}:\nv=DMARC1; p=none; rua=mailto:dmarc@{domain}",
                "priority": "MEDIUM"}
    return {"status": "OK", "record": result.strip('"'), "priority": "NONE"}


def check_mx(domain):
    result = dig_record(domain, "MX")
    if not result:
        return {"status": "MISSING", "records": [],
                "fix": f"Add MX: 10 mx.zoho.in / 20 mx2.zoho.in / 50 mx3.zoho.in",
                "priority": "CRITICAL"}
    return {"status": "OK", "records": [l.strip() for l in result.split("\n") if l.strip()], "priority": "NONE"}


def check_domain(domain):
    spf = check_spf(domain)
    dkim = check_dkim(domain)
    dmarc = check_dmarc(domain)
    mx = check_mx(domain)

    statuses = [spf["status"], dkim["status"], dmarc["status"], mx["status"]]
    if all(s == "OK" for s in statuses):
        health, score = "HEALTHY", 100
    elif any(s == "MISSING" for s in [spf["status"], mx["status"]]):
        health, score = "CRITICAL", 25
    elif "MISSING" in statuses:
        health, score = "NEEDS_FIX", 50
    elif "INCOMPLETE" in statuses:
        health, score = "PARTIAL", 75
    else:
        health, score = "HEALTHY", 100

    fixes = []
    for name, check in [("SPF", spf), ("DKIM", dkim), ("DMARC", dmarc), ("MX", mx)]:
        if check["status"] != "OK":
            fixes.append({"record": name, "status": check["status"],
                          "fix": check.get("fix", ""), "priority": check.get("priority")})

    return {"domain": domain, "health": health, "score": score,
            "spf": spf, "dkim": dkim, "dmarc": dmarc, "mx": mx,
            "fixes_needed": fixes, "total_issues": len(fixes)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check DNS records for email domains")
    parser.add_argument("--domains", required=True, help="Comma-separated domains")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()

    results = []
    for domain in args.domains.split(","):
        domain = domain.strip()
        result = check_domain(domain)
        results.append(result)
        print(f"\n{'='*50}", file=sys.stderr)
        print(f"  {domain} — {result['health']} ({result['score']}/100)", file=sys.stderr)
        print(f"  SPF: {result['spf']['status']}  DKIM: {result['dkim']['status']}  DMARC: {result['dmarc']['status']}  MX: {result['mx']['status']}", file=sys.stderr)
        for fix in result['fixes_needed']:
            print(f"  [{fix['priority']}] {fix['record']}: {fix['fix'][:80]}", file=sys.stderr)

    output = {"status": "success", "domains_checked": len(results), "results": results}
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
    else:
        print(json.dumps(output, indent=2))
