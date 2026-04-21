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

Directory of ~737 GP community members. Fields:

| Field (Airtable) | Meaning | Type |
|---|---|---|
| `您的姓名` | Full name (primary identifier) | text |
| `别名/英文名` | English name / alias | text |
| `Title` | Job title | text |
| `目前就职` | Current company | text |
| `毕业院校` | Alma mater | text |
| `最高学历` | Highest education | text |
| `性别` | Gender | text |
| `会员状态` | Membership status | single-select |
| `建联状态` | Connection status | single-select |
| `熟悉程度` | Familiarity level | single-select |
| `参与活动次数` | # events attended | number |
| `标签` | Role tags (see below) | multi-select |
| `Base` | Location (e.g. `['Bay Area', 'US']`) | multi-select |
| `Profiles` | LinkedIn / social URL | URL text |
| `Profile Picture` | Headshot | attachment |
| `Bio` | 2-sentence professional bio | long text |

### Canonical tag values for `标签`

`Founder` · `Frontier` · `Researcher` · `Engineer` · `Investor` · `Academic` · `Student` · `Executive` · `Professional`

Older values (`Doer`, `Engineer / Lead`, `Professor`, `VP`, `lawyer`, `非会员`, `House Owner`) have been migrated out — don't reintroduce them.

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
