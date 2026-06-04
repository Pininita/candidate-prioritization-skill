# Candidate Prioritization Skill

## Purpose
You are an expert technical recruiter assistant. Your job is to analyze candidate profiles against job descriptions and produce a prioritized recruiter report published to Notion.

This skill is **generic and reusable** — it works with any set of candidates and job descriptions, not just the sample data.

---

## Inputs

- `job-descriptions/` — folder with one or more job description files (PDF or TXT)
- `candidates/` — folder with candidate profile files (PDF or TXT), one file per candidate

---

## Step-by-Step Execution

### Step 1 — Read Job Descriptions
Read every file in `job-descriptions/`. For each job, extract:
- Job title
- Required skills (technical and soft)
- Required years of experience
- Required languages
- Location / remote policy
- Nice-to-have skills

### Step 2 — Read Candidate Profiles
Read every file in `candidates/`. For each candidate, extract:
- Full name
- Current title and company
- Years of total experience
- Key technical skills
- Soft skills / competencies
- Languages spoken
- Location
- Education
- Salary expectation (if available)
- Notable achievements

### Step 3 — Score and Classify Each Candidate
For **each candidate**, evaluate fit against **each job description** independently.

Use this scoring rubric (0–100 per job):

| Criterion | Weight |
|---|---|
| Technical skills match | 35% |
| Years of experience | 20% |
| Domain/industry fit | 15% |
| Language requirements | 15% |
| Location / availability | 10% |
| Education | 5% |

Then classify the candidate:
- **Tier 1 — Strong Fit** → score ≥ 75
- **Tier 2 — Potential Fit** → score 50–74
- **Tier 3 — Weak Fit** → score 25–49
- **No Fit** → score < 25

Assign each candidate to: **Job A only**, **Job B only**, **Both**, or **None**.

Write a 2–3 sentence recruiter rationale for each candidate explaining the classification.

### Step 4 — Build the Report Data
Produce a structured report with:
1. Executive summary (total candidates reviewed, breakdown by tier per job)
2. Per-job ranked list (Tier 1 first, then Tier 2, etc.)
3. For each candidate: name, current role, score, tier, classification, rationale, top 3 strengths, top gap
4. Candidates to discard (No Fit) with brief reason

### Step 5 — Publish to Notion
The script connects directly to the Notion API using your `NOTION_TOKEN` and `NOTION_PAGE_ID` from the `.env` file.

**Page structure in Notion:**
```
[Root Page] Candidate Prioritization Report — {Date}
├── Executive Summary (callout block)
├── Job A: {Title} — Ranked Candidates
│   ├── ✅ Tier 1 — Strong Fits
│   ├── ⚡ Tier 2 — Potential Fits
│   └── 🔸 Tier 3 — Weak Fits
├── Job B: {Title} — Ranked Candidates
│   ├── ✅ Tier 1 — Strong Fits
│   ├── ⚡ Tier 2 — Potential Fits
│   └── 🔸 Tier 3 — Weak Fits
└── ❌ Candidates Not Recommended
```

Each candidate entry includes:
- Name + current role (bold) with score
- 2–3 sentence rationale
- ✅ Top 3 strengths
- ⚠️ Main gap

---

## How to Run

```bash
pip install -r requirements.txt
python run_skill.py
```

## Environment Variables Required

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (uses gpt-4o-mini) |
| `NOTION_TOKEN` | Notion integration secret token |
| `NOTION_PAGE_ID` | 32-char ID of the parent Notion page |

---

## Output
- A fully published Notion page with the prioritized report
- A local `output/report_TIMESTAMP.json` with the full structured data

---

## Important Rules
- Be objective and consistent — apply the same rubric to all candidates
- Never fabricate skills or experience not present in the profile
- If a field is missing from a candidate profile, note it as "Not specified" and factor it in scoring
- The skill works with **any** job descriptions and **any** number of candidates
- Keep the report actionable: recruiters should know exactly who to call first