"""
Prompt 1A — Export sanitized Active + Closed listings from SimplyRETS.
Usage:
    python tools/export_sample_listings.py
Writes:
    tmp/samples/active.json          (raw)
    tmp/samples/closed.json          (raw)
    tmp/samples/active.sanitized.json
    tmp/samples/closed.sanitized.json
"""
import json
import os
import pathlib
import requests

AUTH = (os.environ["SIMPLYRETS_USERNAME"], os.environ["SIMPLYRETS_PASSWORD"])
BASE = "https://api.simplyrets.com"

# Keys to fully strip (PII / contact)
STRIP_KEYS = {
    "privateRemarks", "showingInstructions",
    "showingContactName", "showingContactPhone",
}

# Agent/coAgent sub-keys to strip
STRIP_CONTACT_SUBKEYS = {"email", "cell", "office", "phone", "fax"}


def _sanitize_contact(obj):
    """Strip PII from a contact sub-object."""
    if not isinstance(obj, dict):
        return obj
    return {k: "**REDACTED**" if k in STRIP_CONTACT_SUBKEYS else v
            for k, v in obj.items()}


def _sanitize_person(obj):
    """Strip contact from an agent/coAgent object."""
    if not isinstance(obj, dict):
        return obj
    out = {}
    for k, v in obj.items():
        if k == "contact":
            out[k] = _sanitize_contact(v)
        elif k in ("firstName", "lastName"):
            out[k] = "**REDACTED**"
        else:
            out[k] = v
    return out


def _sanitize_remarks(text):
    """Keep remarks but strip any phone/email patterns."""
    if not text:
        return text
    import re
    text = re.sub(r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b', '***-***-****', text)
    text = re.sub(r'[\w.+-]+@[\w-]+\.[a-z]{2,}', '***@***.***', text, flags=re.IGNORECASE)
    return text


def sanitize(listing: dict) -> dict:
    out = {}
    for k, v in listing.items():
        if k in STRIP_KEYS:
            out[k] = "**REDACTED**"
        elif k == "agent":
            out[k] = _sanitize_person(v)
        elif k == "coAgent":
            out[k] = _sanitize_person(v) if v else None
        elif k == "remarks":
            out[k] = _sanitize_remarks(v)
        elif k == "photos":
            count = len(v) if v else 0
            out["photos_count"] = count
            out["photos_sample"] = v[:2] if v else []
        else:
            out[k] = v
    return out


def fetch_one(params: dict) -> dict:
    r = requests.get(f"{BASE}/properties", params={**params, "limit": 1},
                     auth=AUTH, timeout=15)
    r.raise_for_status()
    data = r.json()
    if not data:
        raise ValueError(f"No results for {params}")
    return data[0]


def null_check(listing: dict):
    checks = {
        "tax.taxAnnualAmount":  listing.get("tax", {}).get("taxAnnualAmount"),
        "originalListPrice":    listing.get("originalListPrice"),
        "listDate":             listing.get("listDate"),
        "sales.contractDate":   (listing.get("sales") or {}).get("contractDate"),
        "association.fee":      (listing.get("association") or {}).get("fee"),
        "school.district":      (listing.get("school") or {}).get("district"),
    }
    return checks


def main():
    out_dir = pathlib.Path("tmp/samples")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Fetching Active listing (Downey)...")
    active = fetch_one({"cities": "Downey", "status": "Active", "type": "residential"})

    print("Fetching Closed listing (Downey)...")
    closed = fetch_one({"cities": "Downey", "status": "Closed", "type": "residential"})

    # Write raw
    (out_dir / "active.json").write_text(json.dumps(active, indent=2, default=str), encoding="utf-8")
    (out_dir / "closed.json").write_text(json.dumps(closed, indent=2, default=str), encoding="utf-8")

    # Sanitize + write
    active_s = sanitize(active)
    closed_s = sanitize(closed)
    (out_dir / "active.sanitized.json").write_text(json.dumps(active_s, indent=2, default=str), encoding="utf-8")
    (out_dir / "closed.sanitized.json").write_text(json.dumps(closed_s, indent=2, default=str), encoding="utf-8")

    for label, listing, sanitized in [("ACTIVE", active, active_s), ("CLOSED", closed, closed_s)]:
        print(f"\n{'='*60}")
        print(f"{label} listing — top-level keys ({len(listing)} keys):")
        print("  " + ", ".join(sorted(listing.keys())))

        nulls = null_check(listing)
        print(f"\n  Null-check for {label}:")
        for path, val in nulls.items():
            status = "NULL" if val is None else f"PRESENT ({repr(val)[:60]})"
            print(f"    {path:35s} -> {status}")

        photo_count = len(listing.get("photos") or [])
        print(f"\n  Photo count: {photo_count}")

    print("\n\nSanitized JSON follows:\n")
    print("--- active.sanitized.json ---")
    print(json.dumps(active_s, indent=2, default=str))
    print("\n--- closed.sanitized.json ---")
    print(json.dumps(closed_s, indent=2, default=str))
    print("\nFiles written to tmp/samples/")


if __name__ == "__main__":
    main()
