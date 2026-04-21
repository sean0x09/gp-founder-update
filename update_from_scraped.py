"""Backfill Airtable fields from the `Scraped Information` column.

Treats the scraped LinkedIn JSON as the source of truth and overwrites
Title / Company / Alias / Alma mater / Education level / Base / Bio /
Profile Picture on each row where scraped data is present.

Usage:
    python update_from_scraped.py                 # dry run, all scraped rows
    python update_from_scraped.py --limit 10      # dry run, first 10
    python update_from_scraped.py --apply         # actually write
    python update_from_scraped.py --apply --limit 5
    python update_from_scraped.py --apply --skip-pictures
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

from dotenv import find_dotenv, load_dotenv
from pyairtable import Api


FIELDS_READ = [
    "您的姓名",
    "别名/英文名",
    "Title",
    "目前就职",
    "毕业院校",
    "最高学历",
    "Base",
    "Bio",
    "Profile Picture",
    "Scraped Information",
]

DEGREE_RANK = {"Post-Doc": 4, "PhD": 3, "Master": 2, "Bachelor": 1, "Below Bachelor": 0}

BAY_AREA_CITIES = (
    "san francisco", "palo alto", "mountain view", "berkeley",
    "oakland", "menlo park", "bay area", "sunnyvale", "san jose",
    "san mateo", "redwood city", "cupertino", "santa clara",
)
NY_CITIES = ("new york", "nyc", "brooklyn", "manhattan")


def classify_degree(subtitle: str) -> str | None:
    if not subtitle:
        return None
    s = subtitle.lower()
    if re.search(r"post[\s-]?doc|postdoctoral", s):
        return "Post-Doc"
    if re.search(r"ph\.?\s?d|doctor(ate|al)?", s):
        return "PhD"
    if re.search(r"master|m\.s\.|\bmsc\b|mba|m\.eng", s):
        return "Master"
    if re.search(r"bachelor|b\.s\.|\bbsc\b|undergraduate|b\.eng|b\.a\.", s):
        return "Bachelor"
    return None


def pick_highest_education(educations: list) -> tuple[str | None, str | None]:
    """Return (school, degree_label) for the highest-ranked education entry."""
    if not educations:
        return None, None
    best = None
    best_rank = -1
    best_year = -1
    for edu in educations:
        degree = classify_degree(edu.get("subtitle") or "")
        rank = DEGREE_RANK.get(degree, -1) if degree else -1
        ended = ((edu.get("period") or {}).get("endedOn") or {}).get("year") or 0
        if rank > best_rank or (rank == best_rank and ended > best_year):
            best = edu
            best_rank = rank
            best_year = ended
    school = (best or {}).get("title")
    degree = classify_degree((best or {}).get("subtitle") or "") if best else None
    return school, degree


def map_base(country: str | None, city: str | None) -> list[str] | None:
    if not country:
        return None
    c = country.strip().lower()
    city_l = (city or "").lower()
    if c in ("china", "people's republic of china"):
        return ["China"]
    if c in ("united states", "usa", "us"):
        if any(k in city_l for k in BAY_AREA_CITIES):
            return ["Bay Area", "US"]
        if any(k in city_l for k in NY_CITIES):
            return ["New York", "US"]
        return ["US"]
    if c in ("united kingdom", "uk", "great britain"):
        return ["UK"]
    if c == "singapore":
        return ["Singapore"]
    if c == "japan":
        return ["Japan"]
    if c in ("korea", "south korea", "republic of korea"):
        return ["Korea"]
    if c == "australia":
        return ["Australia"]
    return None


def format_bio(profile: dict) -> str:
    about = (profile.get("about") or "").strip()
    lines = []
    if about:
        lines.append(about)
    exps = profile.get("experiences") or []
    if exps:
        lines.append("")
        lines.append("Experience:")
        for e in exps:
            title = e.get("title") or "(role)"
            company = e.get("companyName") or ""
            start = e.get("jobStartedOn") or ""
            end = e.get("jobEndedOn") or ("Present" if e.get("jobStillWorking") else "")
            header = f"- {title} at {company}".rstrip()
            if start or end:
                header += f" ({start} – {end})"
            lines.append(header)
            desc = (e.get("jobDescription") or "").strip()
            if desc:
                if len(desc) > 500:
                    desc = desc[:497].rstrip() + "…"
                lines.append(f"  {desc}")
    return "\n".join(lines).strip()


def build_proposed(profile: dict) -> dict:
    """Build a dict of field → new value from scraped profile. Skip None values."""
    out: dict = {}

    full_name = profile.get("fullName")
    if full_name:
        out["别名/英文名"] = full_name

    job_title = profile.get("jobTitle")
    if job_title:
        out["Title"] = job_title

    company = profile.get("companyName")
    if company:
        out["目前就职"] = company

    school, degree = pick_highest_education(profile.get("educations") or [])
    if school:
        out["毕业院校"] = school
    if degree:
        out["最高学历"] = degree

    base = map_base(profile.get("addressCountryOnly"), profile.get("addressWithoutCountry"))
    if base:
        out["Base"] = base

    bio = format_bio(profile)
    if bio:
        out["Bio"] = bio

    return out


def diff_update(current: dict, proposed: dict) -> dict:
    """Keep only fields where proposed differs from current."""
    changes = {}
    for k, v in proposed.items():
        cur = current.get(k)
        if isinstance(v, list):
            if sorted(cur or []) != sorted(v):
                changes[k] = v
        else:
            if (cur or "") != v:
                changes[k] = v
    return changes


def preview(v):
    if isinstance(v, str) and len(v) > 100:
        return v[:97].replace("\n", " ") + "…"
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Actually PATCH Airtable (default: dry run)")
    ap.add_argument("--limit", type=int, default=None, help="Cap to first N scraped rows")
    ap.add_argument("--skip-pictures", action="store_true", help="Don't upload profile pictures")
    args = ap.parse_args()

    env_path = find_dotenv(usecwd=True) or "/Users/yizeshen/repos/gp-founder-update/.env"
    load_dotenv(env_path)

    token = os.environ.get("AIRTABLE_TOKEN")
    base_id = os.environ.get("AIRTABLE_BASE_ID")
    table_id = os.environ.get("AIRTABLE_TABLE_ID")
    if not all([token, base_id, table_id]):
        print(f"Missing AIRTABLE_* env vars (loaded from: {env_path})", file=sys.stderr)
        sys.exit(1)

    table = Api(token).table(base_id, table_id)

    print(f"Fetching records from {base_id}/{table_id}...")
    records = table.all(fields=FIELDS_READ)
    print(f"Fetched {len(records)} rows. Filtering to those with Scraped Information...")

    scraped_rows = [r for r in records if r["fields"].get("Scraped Information")]
    if args.limit:
        scraped_rows = scraped_rows[: args.limit]
    print(f"Processing {len(scraped_rows)} rows (apply={args.apply}).\n")

    field_counts: dict[str, int] = {}
    rows_changed = 0
    pictures_uploaded = 0
    parse_failures = 0

    for rec in scraped_rows:
        rid = rec["id"]
        fields = rec["fields"]
        name = fields.get("您的姓名") or "(no name)"
        raw = fields.get("Scraped Information") or ""

        try:
            profile = json.loads(raw)
        except json.JSONDecodeError as e:
            parse_failures += 1
            print(f"[parse-fail] {rid} | {name} | {e}")
            continue

        if profile.get("succeeded") is False or profile.get("error"):
            continue

        proposed = build_proposed(profile)
        changes = diff_update(fields, proposed)

        # Decide on picture upload (only if empty)
        pic_url = profile.get("profilePicHighQuality") or profile.get("profilePic")
        needs_picture = (
            not args.skip_pictures
            and pic_url
            and not fields.get("Profile Picture")
        )

        if not changes and not needs_picture:
            continue

        if changes:
            changes["Last Updated"] = datetime.now(timezone.utc).isoformat()

        rows_changed += 1
        for k in changes:
            if k != "Last Updated":
                field_counts[k] = field_counts.get(k, 0) + 1
        if needs_picture:
            field_counts["Profile Picture"] = field_counts.get("Profile Picture", 0) + 1

        if args.apply:
            if changes:
                table.update(rid, changes, typecast=True)
                time.sleep(0.25)
            if needs_picture:
                try:
                    table.update(
                        rid,
                        {"Profile Picture": [{"url": pic_url}]},
                        typecast=True,
                    )
                    pictures_uploaded += 1
                    time.sleep(0.5)
                except Exception as e:
                    print(f"[pic-fail] {rid} | {name} | {e}")
            print(f"[apply] {rid} | {name} | {list(changes.keys()) + (['Profile Picture'] if needs_picture else [])}")
        else:
            summary = {k: preview(v) for k, v in changes.items() if k != "Last Updated"}
            if needs_picture:
                summary["Profile Picture"] = "(upload url)"
            print(f"[dry]   {rid} | {name} | {summary}")

    print("\n=== Summary ===")
    print(f"rows scanned      : {len(scraped_rows)}")
    print(f"rows changed      : {rows_changed}")
    print(f"parse failures    : {parse_failures}")
    print(f"pictures uploaded : {pictures_uploaded}")
    print("per-field counts  :")
    for k, v in sorted(field_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k:20s} {v}")


if __name__ == "__main__":
    main()
