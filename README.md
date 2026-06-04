# Candidate Prioritization Skill

An agentic skill that reads job descriptions and candidate profiles, scores and classifies each candidate using OpenAI, and publishes a prioritized recruiter report to Notion.

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/candidate-prioritization-skill
cd candidate-prioritization-skill

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY, NOTION_TOKEN, NOTION_PAGE_ID

# 4. Add your input files
# → job-descriptions/   (PDF or TXT job descriptions)
# → candidates/         (PDF or TXT candidate profiles)

# 5. Run
python run_skill.py
```

See [NOTION_MCP_SETUP.md](./NOTION_MCP_SETUP.md) for full Notion integration instructions.

## How It Works

1. **Reads** all files from `job-descriptions/` and `candidates/`
2. **Classifies** each candidate against each job in batches of 10 using a structured scoring rubric (via OpenAI gpt-4o-mini)
3. **Tiers** candidates: Strong Fit / Potential Fit / Weak Fit / No Fit
4. **Publishes** a formatted, prioritized report to Notion
5. **Saves** a local JSON report to `output/` for auditability

## Project Structure

```
candidate-prioritization-skill/
├── agent.md                  ← skill instructions for AI agents
├── run_skill.py              ← main execution script
├── requirements.txt
├── .env.example              ← environment variables template
├── NOTION_MCP_SETUP.md       ← step-by-step Notion setup
├── SUBMISSION.txt            ← submission links and notes
├── job-descriptions/         ← put job description files here
├── candidates/               ← put candidate profile files here
└── output/                   ← generated reports saved here
```

## Scoring Rubric

| Criterion | Weight |
|---|---|
| Technical skills match | 35% |
| Years of experience | 20% |
| Domain / industry fit | 15% |
| Language requirements | 15% |
| Location / availability | 10% |
| Education | 5% |
