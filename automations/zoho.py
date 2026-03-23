"""Zoho CRM helper — token refresh + COQL queries."""

import json
import urllib.request
import urllib.parse
from config import ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN, ZOHO_TOKEN_URL, ZOHO_API_BASE

_cached_token = None


def get_access_token() -> str:
    global _cached_token
    if _cached_token:
        return _cached_token
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "refresh_token": ZOHO_REFRESH_TOKEN,
    }).encode()
    req = urllib.request.Request(ZOHO_TOKEN_URL, data=data, method="POST")
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    _cached_token = result["access_token"]
    return _cached_token


def coql(query: str) -> dict:
    token = get_access_token()
    url = f"{ZOHO_API_BASE}/coql"
    headers = {"Authorization": f"Zoho-oauthtoken {token}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps({"select_query": query}).encode(), headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": str(e), "body": body}


def coql_count(query: str) -> int:
    result = coql(query)
    if "data" in result:
        return result["data"][0].get("total", result["data"][0].get("c", 0))
    return 0


def coql_paginate(base_query: str, max_records: int = 2000) -> list:
    all_data = []
    for offset in range(0, max_records, 200):
        q = f"{base_query} LIMIT {offset}, 200"
        result = coql(q)
        if "data" in result:
            all_data.extend(result["data"])
            if not result.get("info", {}).get("more_records"):
                break
        else:
            break
    return all_data
