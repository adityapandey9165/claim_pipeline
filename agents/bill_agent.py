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


def itemized_bill_agent(state: ClaimState) -> ClaimState:
    """
    Extracts itemized charges from itemized_bill and cash_receipt pages.
    """
    classification = state.get("page_classification", {})
    relevant_types = ["itemized_bill", "cash_receipt"]

    page_nums = []
    for dt in relevant_types:
        page_nums.extend(classification.get(dt, []))

    if not page_nums:
        print("[Bill Agent] No billing pages found.")
        return {**state, "itemized_bill_result": {"error": "No billing pages found"}}

    pages = extract_pages_by_indices(state["all_pages"], page_nums)
    print(f"[Bill Agent] Processing pages: {page_nums}")

    pages_text = "\n\n".join(
        f"Page {page['page_num']}:\n{page['text'][:2000]}"
        for page in pages
    )

    prompt = f"""
You are a medical billing extractor for insurance claims.

Extract ALL itemized charges from these billing documents.

Return ONLY valid JSON in this format:
{{
  "bill_number": string,
  "bill_date": string,
  "patient_id": string,
  "items": [
    {{"description": string, "quantity": number, "unit_rate": number, "amount": number, "date": string}}
  ],
  "subtotal": number,
  "tax": number,
  "total_amount": number,
  "insurance_payment": number,
  "patient_responsibility": number,
  "insurance_coverage_percent": number,
  "payment_method": string
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

    if "items" in result and result["items"]:
        calc_total = 0
        for item in result["items"]:
            try:
                calc_total += float(item.get("amount", 0) or 0)
            except (TypeError, ValueError):
                continue
        result["_calculated_items_total"] = round(calc_total, 2)

    print(f"[Bill Agent] Extracted {len(result.get('items', []))} line items.")
    return {**state, "itemized_bill_result": result}