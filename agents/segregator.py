import json
import requests
from utils.state import ClaimState
from utils.pdf_utils import extract_pages_as_images

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "llava:7b "

DOCUMENT_TYPES = [
    "claim_forms",
    "cheque_or_bank_details",
    "identity_document",
    "itemized_bill",
    "discharge_summary",
    "prescription",
    "investigation_report",
    "cash_receipt",
    "other"
]


def classify_page(image_b64, page_num):
    prompt = f"""
Classify this page into ONE label:
{", ".join(DOCUMENT_TYPES)}

Answer ONLY with label.
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "options": {"temperature": 0}
        },
        timeout=600
    )

    data = response.json()

    # 🔥 DEBUG (keep this for now)
    print(f"[RAW OUTPUT PAGE {page_num}]:", data)

    # ✅ SAFE PARSING
    if "response" in data:
        result = data["response"].strip().lower()
    elif "message" in data and "content" in data["message"]:
        result = data["message"]["content"].strip().lower()
    else:
        return "other"

    # ✅ CLEAN OUTPUT
    for dt in DOCUMENT_TYPES:
        if dt in result:
            return dt

    return "other"

def segregator_agent(state: ClaimState) -> ClaimState:
    print("[Segregator] Extracting pages...")
    all_pages = extract_pages_as_images(state["pdf_path"])

    classification = {dt: [] for dt in DOCUMENT_TYPES}

    print(f"[Segregator] Classifying {len(all_pages)} pages with LLAVA...")

    for page in all_pages:
        try:
            doc_type = classify_page(page["image_b64"], page["page_num"])
            classification[doc_type].append(page["page_num"])
            print(f"Page {page['page_num']} → {doc_type}")
        except Exception as e:
            print(f"Error on page {page['page_num']}: {e}")
            classification["other"].append(page["page_num"])

    classification = {k: v for k, v in classification.items() if v}

    print("[Segregator] Done:", classification)

    return {
        **state,
        "all_pages": all_pages,
        "page_classification": classification
    }