import json
import re
import requests
from utils.state import ClaimState
from utils.pdf_utils import extract_pages_by_indices

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5-coder:3b"


def _extract_json(text: str) -> dict:
    text = text.strip()

    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1].strip()
            if text.startswith("json"):
                text = text[4:].strip()

    try:
        return json.loads(text)
    except:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))

    raise ValueError("Invalid JSON from model")


def id_agent(state: ClaimState) -> ClaimState:
    classification = state.get("page_classification", {})
    relevant_types = ["identity_document", "claim_forms"]

    page_nums = []
    for dt in relevant_types:
        page_nums.extend(classification.get(dt, []))

    if not page_nums:
        print("[ID Agent] No relevant pages found.")
        return {**state, "id_result": {"error": "No relevant pages"}}

    pages = extract_pages_by_indices(state["all_pages"], page_nums)
    print(f"[ID Agent] Processing pages: {page_nums}")

    pages_text = "\n\n".join(
        f"Page {p['page_num']}:\n{p['text'][:2000]}"
        for p in pages
    )

    prompt = f"""
Extract identity + policy info from text.

Return ONLY JSON:
{{
  "patient_name": string,
  "date_of_birth": string,
  "gender": string,
  "id_number": string,
  "policy_number": string,
  "contact_number": string,
  "email": string,
  "address": string,
  "blood_group": string,
  "insurance_provider": string,
  "claim_reference": string,
  "date_filed": string
}}

Rules:
- Use null if missing
- No explanation

Text:
{pages_text}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0}
        }
    )

    result_text = response.json()["response"]
    result = _extract_json(result_text)

    result["_pages_processed"] = page_nums

    return {**state, "id_result": result}