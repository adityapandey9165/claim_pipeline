import json
import re
import requests
from utils.state import ClaimState
from utils.pdf_utils import extract_pages_by_indices

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5-coder:3b"  # change to "mistral" or "llama3" if you pull those


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
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError(f"Could not parse JSON from model output: {text[:500]}")


def discharge_summary_agent(state: ClaimState) -> ClaimState:
    """
    Extracts clinical information from discharge_summary pages.
    """
    classification = state.get("page_classification", {})
    page_nums = classification.get("discharge_summary", [])

    if not page_nums:
        print("[Discharge Agent] No discharge summary pages found.")
        return {**state, "discharge_result": {"error": "No discharge summary pages found"}}

    pages = extract_pages_by_indices(state["all_pages"], page_nums)
    print(f"[Discharge Agent] Processing pages: {page_nums}")

    pages_text = "\n\n".join(
        f"Page {page['page_num']}:\n{page['text'][:2000]}"
        for page in pages
    )

    prompt = f"""
You are a clinical data extractor for insurance claims.

Extract ALL clinical information from the discharge summary text below.

Return ONLY valid JSON in this format:
{{
  "admission_date": string,
  "discharge_date": string,
  "length_of_stay": string,
  "admission_diagnosis": string,
  "final_diagnosis": string,
  "attending_physician": string,
  "hospital_name": string,
  "hospital_course": string,
  "condition_at_discharge": string,
  "discharge_medications": list,
  "follow_up_instructions": string,
  "mrn": string
}}

Rules:
- Use null if a field is not found
- Do not add any explanation
- Do not wrap in markdown

Text:
{pages_text}
""".strip()

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0
            }
        },
        timeout=300
    )

    response.raise_for_status()
    result_text = response.json().get("response", "").strip()

    result = _extract_json(result_text)
    result["_pages_processed"] = page_nums
    print("[Discharge Agent] Extracted clinical data successfully.")

    return {**state, "discharge_result": result}