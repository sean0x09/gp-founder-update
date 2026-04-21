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

## 4. Conventions

- **Primary key is `您的姓名`.** Watch for duplicates when adding rows.
- **Tags are multi-select** — pass a list (`["Founder", "Investor"]`), not a comma-separated string.
- **`Base` is also multi-select** and can hold country + city (e.g. `["Bay Area", "US"]`).
- **Rate-limit writes**: Airtable's API caps at 5 req/sec per base. Sleep ~0.2s between calls or use `batch_update`.
- **Never commit `.env`** — it's already in `.gitignore`.
