# GP Founder Update

A minimal workspace for interacting with the **GP founder community directory** in Airtable. It contains only the credentials (`.env`) and this reference — bring your own scripts or use the Airtable UI / API directly.

---

## 1. Credentials

Secrets live in `.env` (gitignored). A template is provided as `.env.example`.

| Variable | Purpose |
|---|---|
| `AIRTABLE_BASE_ID` | The base the founder table belongs to. |
| `AIRTABLE_TABLE_ID` | The specific table within the base. |
| `AIRTABLE_TOKEN` | Personal Access Token for the Airtable REST API. |
| `ANTHROPIC_API_KEY` | Claude API key — used for bio generation and any LLM-powered enrichment. |

If you need to rotate any of these:

- **Airtable token** → https://airtable.com/create/tokens (required scopes: `data.records:read`, `data.records:write`, `schema.bases:read`).
- **Anthropic key** → https://console.anthropic.com/settings/keys.

---

## 2. What's in the table

Directory of **770 GP community members** (table ID `tbluZvRKR9uatnlMU`, "GRC Database"). The table is a CRM-style roster tracking who's in the community, how the GP team knows them, and what their membership / BD status is. Most rows are founders and frontier AI operators split roughly evenly between China and the US.

### Fields

| Field (Airtable) | Meaning | Type | Populated |
|---|---|---|---|
| `您的姓名` | Full name (primary identifier) | long text | 769/770 |
| `别名/英文名` | English name / alias | long text | 425/770 |
| `Title` | Job title | long text | 739/770 |
| `目前就职` | Current company | long text | 747/770 |
| `毕业院校` | Alma mater | long text | 649/770 |
| `最高学历` | Highest education | single-select | 529/770 |
| `性别` | Gender | single-select | 620/770 |
| `会员状态` | Membership status | single-select | 700/770 |
| `建联状态` | BD / outreach status | single-select | 691/770 |
| `熟悉程度` | Familiarity level | single-select | 623/770 |
| `参与活动次数` | # events attended | number | 402/770 |
| `标签` | Role tag (**single-select**, not multi) | single-select | 651/770 |
| `Base` | Location (multi, e.g. `["Bay Area", "US"]`) | multi-select | 764/770 |
| `Profiles` | LinkedIn / social URL | URL | 504/770 |
| `Profile Picture` | Headshot | attachment | 446/770 |
| `Bio` | LLM-generated professional bio (often multi-paragraph) | long text | 750/770 |
| `Last Updated` | Row update timestamp | datetime | 0/770 |

### Canonical option values

Pass these strings exactly (or send `typecast: true` to auto-create new options). The Airtable schema also allows `""` as a valid "blank" choice for every single-select below — we treat it as unset.

- **`标签`** (one of): `Founder` · `Frontier` · `Engineer` · `Investor` · `Student` · `Executive` · `Academic` · `Professional`
  - Current distribution: Founder 276 · Frontier 121 · Engineer 120 · Investor 62 · Student 32 · Executive 20 · Academic 16 · Professional 4.
  - **`Researcher` is not a valid option** — it was removed from the schema. Map former researcher rows to `Academic` or `Frontier`.
  - Other migrated-out values (don't reintroduce): `Doer`, `Engineer / Lead`, `Professor`, `VP`, `lawyer`, `非会员`, `House Owner`.
- **`Base`** (one or more): `Bay Area` · `US` · `China` · `Undisclosed` · `UK` · `Singapore` · `Japan` · `Korea` · `Australia` · `New York` · `United States`. US-based rows usually carry both `["Bay Area", "US"]`; `United States` is a legacy variant of `US` — prefer `US`.
- **`最高学历`**: `Bachelor` · `Master` · `PhD` · `Post-Doc` · `Below Bachelor` · `Unkown` (sic — existing typo in schema).
- **`会员状态`**: `非会员` · `非付费会员` · `正在转化` · `付费会员`.
- **`熟悉程度`**: `陌生人` · `线上网友` · `线下见过`.
- **`建联状态`**: `待 BD` · `已建联`.
- **`性别`**: `男` · `女`.

---

## 3. How to interact with the table

### Option A — Airtable UI
Open the base at https://airtable.com/{AIRTABLE_BASE_ID} (replace with the value in `.env`). This is the right path for manual edits, schema changes, and building views.

### Option B — REST API (cURL)

List 5 records:

```bash
set -a && source .env && set +a
curl "https://api.airtable.com/v0/$AIRTABLE_BASE_ID/$AIRTABLE_TABLE_ID?maxRecords=5" \
  -H "Authorization: Bearer $AIRTABLE_TOKEN"
```

Update one field on one record:

```bash
curl -X PATCH "https://api.airtable.com/v0/$AIRTABLE_BASE_ID/$AIRTABLE_TABLE_ID/REC_ID_HERE" \
  -H "Authorization: Bearer $AIRTABLE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fields": {"Bio": "New bio text"}}'
```

Full API reference: https://airtable.com/developers/web/api/introduction

### Option C — Python (`pyairtable`)

```python
import os
from dotenv import load_dotenv
from pyairtable import Api

load_dotenv()
table = Api(os.environ["AIRTABLE_TOKEN"]).table(
    os.environ["AIRTABLE_BASE_ID"],
    os.environ["AIRTABLE_TABLE_ID"],
)

# Read
for record in table.all(max_records=5):
    print(record["id"], record["fields"].get("您的姓名"))

# Update
table.update("recXXXXXXXXXXXXXX", {"Bio": "New bio text"})

# Upload an attachment (e.g. profile picture)
table.upload_attachment("recXXXXXXXXXXXXXX", "Profile Picture", "./headshot.png")
```

Install once: `pip install pyairtable python-dotenv anthropic`.

### Option D — Claude for enrichment

Pair the Airtable client with the Anthropic SDK when you need the model to write/clean fields:

```python
from anthropic import Anthropic
claude = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

msg = claude.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=200,
    messages=[{"role": "user", "content": f"Write a 2-sentence founder bio for {name}, {title} at {company}."}],
)
table.update(record_id, {"Bio": msg.content[0].text})
```

---

## 4. Scraping LinkedIn profiles

The `Scraped Information` column is populated by the apify actor [`dev_fusion/Linkedin-Profile-Scraper`](https://console.apify.com/actors/2SyF0bVxmgGr8IVCZ) — **$10 per 1,000 results** (~$0.01 per profile). Full per-profile JSON is saved in the column and mirrored under `scraped information/<record_id>.json` locally (gitignored).

### Prerequisites

```bash
brew install apify-cli           # macOS
apify login                      # paying account required for API/CLI runs; free tier is UI-only
```

### Input format

The actor takes a JSON array of LinkedIn profile URLs:

```json
{ "profileUrls": ["https://www.linkedin.com/in/williamhgates", "..."] }
```

### URL normalization — **critical**

Raw LinkedIn URLs from the table break the actor in predictable ways. Normalize before sending:

- **Strip query strings.** `?originalSubdomain=cn|hk|sg|uk|...` and `?locale=zh_CN` trigger `"No person found"` even when the profile exists.
- **Strip trailing subpaths.** `/overlay/photo/`, `/overlay/about-this-profile/` — keep only `/in/<handle>/`.
- **Skip non-person URLs.** `/company/*`, `/pub/*` (legacy), `/posts/*` will fail.
- **Keep regional subdomains as-is** (`cn.linkedin.com`, `hk.linkedin.com`, `uk.linkedin.com` all work).

Python helper:

```python
import re
from urllib.parse import urlsplit, urlunsplit

def normalize_linkedin(u: str) -> str:
    parts = urlsplit(u.strip())
    path = re.sub(r"/overlay/[^/]*/?$", "", parts.path)
    m = re.match(r"^(/in/[^/]+)(/.*)?$", path)
    if m:
        path = m.group(1) + "/"
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))
```

### Running the actor

Small batch (CLI, piped stdin):

```bash
echo '{"profileUrls":["https://www.linkedin.com/in/williamhgates"]}' \
  | apify call dev_fusion/Linkedin-Profile-Scraper --silent --output-dataset \
  > output.json
```

For >150 profiles, chunk the input. Typical throughput on this actor: ~1 profile/sec per chunk with internal parallelism.

### Output shape

Each item in the returned array has:

- **Core**: `linkedinUrl`, `fullName`, `firstName`, `lastName`, `headline`, `email`, `mobileNumber`, `connections`, `followers`, `publicIdentifier`, `urn`, `addressWithCountry`.
- **Current role**: `jobTitle`, `companyName`, `companyIndustry`, `companyWebsite`, `companyLinkedin`, `companySize`, `jobStartedOn`, `currentJobDuration`.
- **Arrays**: `experiences[]`, `educations[]`, `skills[]`, `languages[]`, `publications[]`, `patents[]`, `recommendations[]`, `updates[]` (posts), `peopleAlsoViewed[]`.
- **Failures**: `{"linkedinUrl": "...", "succeeded": false, "error": "..."}` — match by `linkedinUrl` to identify.

Match scraped results back to Airtable records by normalized `linkedinUrl` — the actor echoes the input URL, so indexing by both raw and normalized forms covers subdomain variants.

### Writing to Airtable — watch the 100K long-text cap

The `Scraped Information` field is `multilineText` with a **100,000-character cap**. Pretty-printed JSON (`indent=2`) fits for almost all profiles, but very large records (lots of `peopleAlsoViewed` and `updates`) overflow. Fall back to minified JSON (no indentation) for those — all data preserved, just no whitespace:

```python
pretty = json.dumps(profile, indent=2, ensure_ascii=False)
body = pretty if len(pretty) <= 100_000 else json.dumps(profile, ensure_ascii=False, separators=(",", ":"))
```

### Observed success rate

On the 504 existing Profiles URLs:

- 350 were LinkedIn URLs; **338 scraped successfully** (96.6%) after URL normalization.
- 12 LinkedIn failures: deleted/private profiles, malformed URLs (emoji, encoded Chinese commas), `/company/` or `/posts/` URLs, and legacy `/pub/` paths.
- 154 non-LinkedIn URLs skipped (94 Baidu Baike, 8 Google Scholar, plus ~40 other domains) — this actor only handles LinkedIn.

---

## 5. Conventions

- **Primary key is `您的姓名`.** Watch for duplicates when adding rows.
- **Tags are multi-select** — pass a list (`["Founder", "Investor"]`), not a comma-separated string.
- **`Base` is also multi-select** and can hold country + city (e.g. `["Bay Area", "US"]`).
- **Rate-limit writes**: Airtable's API caps at 5 req/sec per base. Sleep ~0.2s between calls or use `batch_update`.
- **Never commit `.env`** — it's already in `.gitignore`.
