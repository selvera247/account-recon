import os
import json
from typing import Dict, List, Any
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

import gspread
from google.oauth2.service_account import Credentials
import openai

load_dotenv()

GOOGLE_SA_JSON = os.getenv("GOOGLE_SA_JSON", "service_account.json")
SHEET_ID = os.getenv("SHEET_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
EMBED_CACHE_PATH = Path("embeddings_cache.json")


# ---------- Google Sheet helpers ----------

def get_sheet():
    creds = Credentials.from_service_account_file(GOOGLE_SA_JSON, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).worksheet("Intake")


# ---------- Embeddings + cache ----------

def embed_text(text: str) -> List[float]:
    """Call OpenAI embeddings API."""
    if not text.strip():
        return [0.0]

    resp = openai.Embedding.create(
        model="text-embedding-3-small",
        input=text,
    )
    return resp["data"][0]["embedding"]


def load_cache() -> Dict[str, Any]:
    if EMBED_CACHE_PATH.exists():
        with EMBED_CACHE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: Dict[str, Any]) -> None:
    with EMBED_CACHE_PATH.open("w", encoding="utf-8") as f:
        json.dump(cache, f)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    if not a.any() or not b.any():
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# ---------- RAG retrieval over completed items ----------

def build_text_blob(row: Dict[str, Any]) -> str:
    """Combine the most informative fields into a single text for embeddings."""
    parts = [
        f"Title: {row.get('Request Title','')}",
        f"Type: {row.get('Request Type','')}",
        f"Team: {row.get('Requestor Team','')}",
        f"Business Question: {row.get('Business Question','')}",
        f"Key Metrics: {row.get('Key Metrics','')}",
        f"Segments / Filters: {row.get('Segments / Filters','')}",
        f"Success Criteria: {row.get('Success Criteria','')}",
        f"Outcome: {row.get('Final Outcome Notes','')}",
        f"Systems: {row.get('Primary Systems Touched','')}",
    ]
    return "\n".join(parts)


def get_completed_examples(values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter rows that are 'Completed' and have some outcome info."""
    examples = []
    for i, row in enumerate(values, start=2):  # row index in sheet
        status = (row.get("Status") or "").strip()
        outcome_notes = (row.get("Final Outcome Notes") or "").strip()
        if status.lower() == "completed" and outcome_notes:
            row["_row_index"] = i
            examples.append(row)
    return examples


def retrieve_similar_examples(
    current_row: Dict[str, Any],
    completed_rows: List[Dict[str, Any]],
    cache: Dict[str, Any],
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Return top_k most similar completed rows for the current request."""
    if not completed_rows:
        return []

    cache.setdefault("rows", {})
    cache_rows = cache["rows"]

    # Embed current row
    cur_text = build_text_blob(current_row)
    cur_emb = np.array(embed_text(cur_text))

    sims = []

    for row in completed_rows:
        idx = row["_row_index"]
        key = str(idx)

        if key in cache_rows and "embedding" in cache_rows[key]:
            emb = np.array(cache_rows[key]["embedding"])
        else:
            txt = build_text_blob(row)
            emb_list = embed_text(txt)
            emb = np.array(emb_list)
            cache_rows[key] = {
                "embedding": emb_list,
                "request_title": row.get("Request Title", ""),
            }

        sim = cosine_sim(cur_emb, emb)
        sims.append((sim, row))

    sims.sort(key=lambda x: x[0], reverse=True)
    top_rows = [r for (sim, r) in sims[:top_k] if sim > 0]

    return top_rows


# ---------- Prompt building ----------

def format_example_for_prompt(row: Dict[str, Any]) -> str:
    return f"""
Request Title: {row.get('Request Title','')}
Request Type: {row.get('Request Type','')}
Team: {row.get('Requestor Team','')}
Business Question: {row.get('Business Question','')}
Key Metrics: {row.get('Key Metrics','')}
Outcome Notes: {row.get('Final Outcome Notes','')}
Final Impact Rating: {row.get('Final Impact Rating','')}
Final Effort Actual: {row.get('Final Effort Actual','')}
Final Cycle Time Days: {row.get('Final Cycle Time Days','')}
Primary Systems Touched: {row.get('Primary Systems Touched','')}
"""


def build_prompt(current: Dict[str, Any], similar: List[Dict[str, Any]]) -> str:
    context_block = "No prior similar requests found." if not similar else "\n".join(
        f"Example {i+1}:{format_example_for_prompt(r)}"
        for i, r in enumerate(similar)
    )

    return f"""
You are a PMO intake triage assistant for a Revenue & Analytics organization.

You receive a NEW analytics request with the following details:

Request Title: {current.get('Request Title','')}
Request Type: {current.get('Request Type','')}
Requestor Team: {current.get('Requestor Team','')}
Urgency: {current.get('Urgency','')}
Business Impact: {current.get('Business Impact','')}
Business Question: {current.get('Business Question','')}
Key Metrics: {current.get('Key Metrics','')}
Segments / Filters: {current.get('Segments / Filters','')}
Expected Output: {current.get('Expected Output','')}
Existing Analysis: {current.get('Existing Analysis','')}
Success Criteria: {current.get('Success Criteria','')}
Additional Notes: {current.get('Additional Notes','')}

You also have historical COMPLETED requests with outcomes:

{context_block}

TASK:
Using both the NEW request and the historical examples, you must:
- Summarize the new request in 2–3 concise bullets.
- Suggest tags (short keywords like "pipeline", "churn", "enterprise", "self-serve", "CS dashboard").
- Suggest a numeric priority_score from 1–100 (higher = more urgent AND higher impact).
- Suggest effort as one of: "S", "M", "L".
- Provide risk_notes that mention any likely blockers, data gaps, or scope uncertainty.
- Provide a confidence score from 1–100 based on how similar the past examples are.

Return ONLY valid JSON with this structure:

{{
  "summary": "...",
  "tags": ["tag1", "tag2"],
  "priority_score": 75,
  "effort": "M",
  "risk_notes": "...",
  "confidence": 80
}}
"""


# ---------- OpenAI chat call ----------

def call_model(prompt: str) -> Dict[str, Any]:
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # adjust if needed
        messages=[
            {"role": "system", "content": "You are a precise JSON-only assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    content = resp.choices[0].message["content"]
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        data = json.loads(content[start:end+1])
    return data


# ---------- Main triage loop ----------

def main():
    sheet = get_sheet()
    values = sheet.get_all_records()
    header_row = sheet.row_values(1)
    header_idx = {h: i + 1 for i, h in enumerate(header_row)}  # 1-based

    cache = load_cache()
    completed_rows = get_completed_examples(values)

    for i, row in enumerate(values, start=2):
        status = (row.get("Status") or "").strip()
        ai_summary = (row.get("AI Summary") or "").strip()

        # Only triage brand new items
        if status or ai_summary:
            continue

        similar = retrieve_similar_examples(row, completed_rows, cache)
        prompt = build_prompt(row, similar)
        ai_result = call_model(prompt)

        summary = ai_result.get("summary", "")
        tags = ", ".join(ai_result.get("tags", []))
        priority_score = ai_result.get("priority_score", "")
        effort = ai_result.get("effort", "")
        risk_notes = ai_result.get("risk_notes", "")
        confidence = ai_result.get("confidence", "")

        sheet.update_cell(i, header_idx["AI Summary"], summary)
        sheet.update_cell(i, header_idx["AI Tags"], tags)
        sheet.update_cell(i, header_idx["AI Priority Score"], priority_score)
        sheet.update_cell(i, header_idx["AI Effort"], effort)

        risk_full = f"Confidence: {confidence}. {risk_notes}"
        sheet.update_cell(i, header_idx["AI Risk Notes"], risk_full)

        sheet.update_cell(i, header_idx["Status"], "Needs Review")

        print(f"Row {i}: priority={priority_score}, effort={effort}, confidence={confidence}")

    save_cache(cache)


if __name__ == "__main__":
    main()