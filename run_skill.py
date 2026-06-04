#!/usr/bin/env python3
"""
Candidate Prioritization Skill
================================
Reads job descriptions + candidate profiles, classifies candidates using OpenAI,
and publishes a prioritized report to Notion.

Usage:
    python run_skill.py

Requirements:
    pip install -r requirements.txt
"""

import os
import json
import asyncio
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Config ───────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_TOKEN   = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")

JOBS_DIR       = Path("job-descriptions")
CANDIDATES_DIR = Path("candidates")
OUTPUT_DIR     = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── PDF / TXT reader ──────────────────────────────────────────────────────────
def read_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            import fitz
            doc = fitz.open(str(path))
            return "\n".join(page.get_text() for page in doc)
        except ImportError:
            raise ImportError("Install PyMuPDF: pip install pymupdf")
    else:
        return path.read_text(encoding="utf-8", errors="ignore")


# ── Load inputs ───────────────────────────────────────────────────────────────
def load_jobs() -> dict:
    jobs = {}
    for f in sorted(JOBS_DIR.glob("*")):
        if f.suffix.lower() in (".pdf", ".txt", ".md"):
            jobs[f.stem] = read_file(f)
    if not jobs:
        raise FileNotFoundError(f"No job files found in '{JOBS_DIR}/'")
    return jobs


def load_candidates() -> dict:
    candidates = {}
    for f in sorted(CANDIDATES_DIR.glob("*")):
        if f.suffix.lower() in (".pdf", ".txt", ".md"):
            candidates[f.stem] = read_file(f)
    if not candidates:
        raise FileNotFoundError(f"No candidate files found in '{CANDIDATES_DIR}/'")
    return candidates


# ── Call OpenAI ───────────────────────────────────────────────────────────────
def call_openai(system: str, user: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.2,
        "max_tokens": 8192
    }
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers, json=body, timeout=300
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ── Classify candidates in batches ────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert technical recruiter. Analyze candidate profiles against job descriptions.

Scoring rubric per job (0-100):
- Technical skills match: 35 points
- Years of experience: 20 points
- Domain/industry fit: 15 points
- Language requirements: 15 points
- Location / availability: 10 points
- Education: 5 points

Tiers:
- Tier 1 — Strong Fit: score >= 75
- Tier 2 — Potential Fit: score 50-74
- Tier 3 — Weak Fit: score 25-49
- No Fit: score < 25

Respond ONLY with valid JSON — no markdown, no backticks, no preamble."""


def parse_json(raw: str):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def classify_batch(job_texts: str, batch: list) -> list:
    """Classify a batch of (id, text) candidate tuples."""
    candidate_texts = "\n\n".join(
        f"=== CANDIDATE ID: {cid} ===\n{ctxt}" for cid, ctxt in batch
    )
    user_prompt = f"""JOB DESCRIPTIONS:
{job_texts}

CANDIDATE PROFILES:
{candidate_texts}

For each candidate evaluate fit for EACH job independently.
Determine overall classification: "Job A only", "Job B only", "Both", or "None".

Return a JSON array (no wrapper object):
[
  {{
    "id": "<candidate_id>",
    "name": "<full name>",
    "current_role": "<title at company>",
    "location": "<city, country>",
    "total_experience_years": <number>,
    "languages": ["<lang1>"],
    "top_skills": ["<skill1>", "<skill2>", "<skill3>"],
    "scores": {{
      "<job_id>": {{
        "score": <0-100>,
        "tier": "<Tier 1 — Strong Fit | Tier 2 — Potential Fit | Tier 3 — Weak Fit | No Fit>",
        "rationale": "<2-3 sentence recruiter rationale>",
        "strengths": ["<strength1>", "<strength2>", "<strength3>"],
        "main_gap": "<main gap or concern>"
      }}
    }},
    "classification": "<Job A only | Job B only | Both | None>",
    "overall_rationale": "<1-2 sentence summary for recruiter>"
  }}
]"""
    raw = call_openai(SYSTEM_PROMPT, user_prompt)
    return parse_json(raw)


def classify_candidates(jobs: dict, candidates: dict) -> dict:
    job_texts = "\n\n".join(
        f"=== JOB ID: {jid} ===\n{jtxt}" for jid, jtxt in jobs.items()
    )

    BATCH_SIZE = 10
    candidate_items = list(candidates.items())
    all_candidates = []
    total_batches = (len(candidate_items) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(candidate_items), BATCH_SIZE):
        batch = candidate_items[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"🤖 Processing batch {batch_num}/{total_batches} ({len(batch)} candidates)...")
        results = classify_batch(job_texts, batch)
        all_candidates.extend(results)
        print(f"   ✓ Batch {batch_num} done — {len(results)} candidates classified")

    # Get job metadata
    jobs_prompt = f"""Given these job descriptions return ONLY a JSON object (no markdown):
{job_texts}

Format:
{{
  "<job_id>": {{
    "title": "<job title>",
    "summary": "<1 sentence ideal candidate summary>"
  }}
}}"""
    print("📋 Fetching job metadata...")
    jobs_raw = call_openai(SYSTEM_PROMPT, jobs_prompt)
    jobs_meta = parse_json(jobs_raw)

    return {"jobs": jobs_meta, "candidates": all_candidates}


# ── Build summary ─────────────────────────────────────────────────────────────
def build_summary(data: dict) -> dict:
    summary = {}
    for job_id in data["jobs"]:
        tiers = {
            "Tier 1 — Strong Fit": [],
            "Tier 2 — Potential Fit": [],
            "Tier 3 — Weak Fit": [],
            "No Fit": []
        }
        for c in data["candidates"]:
            score_data = c["scores"].get(job_id, {})
            tier = score_data.get("tier", "No Fit")
            tiers.setdefault(tier, []).append(c["name"])
        summary[job_id] = {
            "title": data["jobs"][job_id]["title"],
            "tier_counts": {t: len(v) for t, v in tiers.items()},
            "tiers": tiers,
        }
    return summary


# ── Notion helpers ────────────────────────────────────────────────────────────
def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def create_notion_page(title: str, parent_id: str):
    body = {
        "parent": {"page_id": parent_id},
        "properties": {"title": {"title": [{"text": {"content": title}}]}}
    }
    resp = requests.post("https://api.notion.com/v1/pages",
                         headers=notion_headers(), json=body)
    resp.raise_for_status()
    return resp.json()["id"], resp.json()["url"]

def append_blocks(page_id: str, blocks: list):
    for i in range(0, len(blocks), 100):
        chunk = blocks[i:i+100]
        resp = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=notion_headers(), json={"children": chunk}
        )
        resp.raise_for_status()

def h2(text):
    return {"object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}}

def h3(text):
    return {"object": "block", "type": "heading_3",
            "heading_3": {"rich_text": [{"type": "text", "text": {"content": text}}]}}

def paragraph(text, bold=False):
    return {"object": "block", "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": text},
                                         "annotations": {"bold": bold}}]}}

def divider():
    return {"object": "block", "type": "divider", "divider": {}}

def callout(text, emoji="📊"):
    return {"object": "block", "type": "callout",
            "callout": {"rich_text": [{"type": "text", "text": {"content": text}}],
                        "icon": {"type": "emoji", "emoji": emoji}}}

def bullet(text):
    return {"object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}}


# ── Publish to Notion ─────────────────────────────────────────────────────────
def publish_to_notion(data: dict, summary: dict):
    if not NOTION_TOKEN or not NOTION_PAGE_ID:
        print("⚠️  NOTION_TOKEN or NOTION_PAGE_ID not set — skipping Notion publish.")
        return None

    today = datetime.now().strftime("%Y-%m-%d")
    title = f"Candidate Prioritization Report — {today}"

    print("📝 Creating Notion page...")
    page_id, page_url = create_notion_page(title, NOTION_PAGE_ID)

    total = len(data["candidates"])
    summary_lines = [f"Total candidates reviewed: {total}"]
    for job_id, s in summary.items():
        summary_lines.append(f"\n{s['title']}:")
        for tier, count in s["tier_counts"].items():
            if count > 0:
                summary_lines.append(f"  • {tier}: {count}")

    TIER_EMOJI = {
        "Tier 1 — Strong Fit": "✅",
        "Tier 2 — Potential Fit": "⚡",
        "Tier 3 — Weak Fit": "🔸",
        "No Fit": "❌"
    }

    blocks = []
    blocks.append(callout("\n".join(summary_lines), "📊"))
    blocks.append(divider())

    for job_id, s in summary.items():
        blocks.append(h2(f"📋 {s['title']}"))

        job_candidates = []
        for c in data["candidates"]:
            sd = c["scores"].get(job_id, {})
            if sd.get("tier", "No Fit") != "No Fit":
                job_candidates.append((c, sd))
        job_candidates.sort(key=lambda x: x[1].get("score", 0), reverse=True)

        current_tier = None
        for c, sd in job_candidates:
            tier = sd.get("tier", "No Fit")
            if tier != current_tier:
                current_tier = tier
                blocks.append(h3(f"{TIER_EMOJI.get(tier, '')} {tier}"))
            score = sd.get("score", 0)
            name = c.get("name", c["id"])
            role = c.get("current_role", "")
            rationale = sd.get("rationale", "")
            strengths = sd.get("strengths", [])
            gap = sd.get("main_gap", "")
            blocks.append(paragraph(f"{TIER_EMOJI.get(tier,'•')} {name} — {role} | Score: {score}/100", bold=True))
            blocks.append(paragraph(rationale))
            if strengths:
                blocks.append(bullet("Strengths: " + " · ".join(strengths)))
            if gap:
                blocks.append(bullet(f"Gap: {gap}"))

        blocks.append(divider())

    blocks.append(h2("❌ Candidates Not Recommended"))
    no_fit = [c for c in data["candidates"] if c.get("classification") == "None"]
    if no_fit:
        for c in no_fit:
            blocks.append(bullet(f"{c.get('name', c['id'])} — {c.get('overall_rationale', '')}"))
    else:
        blocks.append(paragraph("All candidates have at least some fit for one of the positions."))

    blocks.append(divider())
    blocks.append(paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} by Candidate Prioritization Skill"))

    print(f"📤 Appending {len(blocks)} blocks to Notion...")
    append_blocks(page_id, blocks)
    print("✅ Notion report published!")
    return page_url


# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    print("=" * 60)
    print("  Candidate Prioritization Skill")
    print("=" * 60)

    print(f"\n📂 Loading job descriptions from '{JOBS_DIR}/'...")
    jobs = load_jobs()
    print(f"   Found {len(jobs)} job(s): {', '.join(jobs.keys())}")

    print(f"📂 Loading candidates from '{CANDIDATES_DIR}/'...")
    candidates = load_candidates()
    print(f"   Found {len(candidates)} candidate(s)")

    data = classify_candidates(jobs, candidates)
    summary = build_summary(data)

    report_path = OUTPUT_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(
        json.dumps({"data": data, "summary": summary}, ensure_ascii=False, indent=2)
    )
    print(f"\n💾 Report saved locally → {report_path}")

    print("\n📊 CLASSIFICATION SUMMARY")
    print("-" * 40)
    for job_id, s in summary.items():
        print(f"\n{s['title']}")
        for tier, count in s["tier_counts"].items():
            if count > 0:
                bar = "█" * count
                print(f"  {tier:<32} {count:>2}  {bar}")

    notion_url = publish_to_notion(data, summary)
    if notion_url:
        print(f"\n🔗 Notion Report: {notion_url}")

    print("\n✅ Skill execution complete.")


if __name__ == "__main__":
    asyncio.run(main())
