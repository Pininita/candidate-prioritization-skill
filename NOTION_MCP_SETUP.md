# Notion MCP Setup — Instructions for Pablo

Follow these steps to connect the Notion MCP and run the skill in your environment (Cowork / Codex / OpenCode).

---

## Step 1 — Create a Notion Integration

1. Go to https://www.notion.so/profile/integrations
2. Click **"New integration"**
3. Give it a name (e.g., `candidate-prioritization-skill`)
4. Select your workspace
5. Under **Capabilities**, enable: Read content, Update content, Insert content
6. Click **Save** and copy the **"Internal Integration Secret"** — this is your `NOTION_TOKEN`

---

## Step 2 — Connect the Integration to a Page

1. Open or create a Notion page where the report will be published (e.g., "Recruiting Reports")
2. Click the **⋯ menu** (top right of the page) → **Connections** → search for your integration and click **Connect**
3. Copy the **Page ID** from the URL:
   - URL format: `https://www.notion.so/Page-Title-{PAGE_ID}`
   - The PAGE_ID is the last part after the last `-` (32 hex characters)
   - This is your `NOTION_PAGE_ID`

---

## Step 3 — Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Then edit `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...       # your Anthropic key
NOTION_TOKEN=secret_...            # from Step 1
NOTION_PAGE_ID=abc123...           # from Step 2
```

---

## Step 4 — Add Your Input Files

Place your files in the correct folders:

```
candidate-prioritization/
├── job-descriptions/
│   ├── job-a.pdf        ← job description A
│   └── job-b.pdf        ← job description B
└── candidates/
    ├── candidate-01.pdf
    ├── candidate-02.pdf
    └── ...              ← all candidate profiles (PDF or TXT)
```

---

## Step 5 — Install Dependencies and Run

```bash
cd candidate-prioritization
pip install -r requirements.txt
python run_skill.py
```

The skill will:
1. Read all job descriptions and candidate profiles
2. Classify each candidate using Claude
3. Save a local JSON report to `output/`
4. Publish the full report to your Notion page

---

## Notes

- The skill works with **any number of candidates and any job descriptions** — just drop files in the folders
- Candidate files can be PDF or plain text
- The Notion token and page ID are used only locally and never stored in the repo
- If Notion publish fails, the local JSON report in `output/` always contains the full data
