from utils.state import ClaimState
from datetime import datetime


def aggregator_node(state: ClaimState) -> ClaimState:
    """
    Combines results from all extraction agents into final JSON.
    """
    print("[Aggregator] Combining all agent results...")

    classification = state.get("page_classification", {})
    total_pages = len(state.get("all_pages", []))

    final_result = {
        "claim_id": state["claim_id"],
        "processed_at": datetime.utcnow().isoformat() + "Z",
        "document_classification": {
            doc_type: {"pages": pages, "page_count": len(pages)}
            for doc_type, pages in classification.items()
        },
        "total_pages": total_pages,
        "identity_and_policy": state.get("id_result") or {},
        "clinical_summary": state.get("discharge_result") or {},
        "billing_details": state.get("itemized_bill_result") or {},
        "claim_summary": _build_claim_summary(state)
    }

    print("[Aggregator] Final result assembled.")
    return {**state, "final_result": final_result}


def _build_claim_summary(state: ClaimState) -> dict:
    """Build a high-level claim summary."""
    id_data = state.get("id_result") or {}
    discharge_data = state.get("discharge_result") or {}
    bill_data = state.get("itemized_bill_result") or {}

    return {
        "patient_name": id_data.get("patient_name"),
        "policy_number": id_data.get("policy_number"),
        "insurance_provider": id_data.get("insurance_provider"),
        "admission_diagnosis": discharge_data.get("admission_diagnosis"),
        "admission_date": discharge_data.get("admission_date"),
        "discharge_date": discharge_data.get("discharge_date"),
        "total_bill_amount": bill_data.get("total_amount"),
        "insurance_payment": bill_data.get("insurance_payment"),
        "patient_responsibility": bill_data.get("patient_responsibility"),
        "attending_physician": discharge_data.get("attending_physician"),
    }