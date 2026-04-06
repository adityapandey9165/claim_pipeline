from typing import TypedDict, List, Dict, Any, Optional


class ClaimState(TypedDict):
    claim_id: str
    pdf_path: str
    all_pages: List[Dict]           # All pages with image + text
    page_classification: Dict[str, List[int]]  # doc_type -> [page_nums]
    id_result: Optional[Dict]
    discharge_result: Optional[Dict]
    itemized_bill_result: Optional[Dict]
    final_result: Optional[Dict]
    error: Optional[str]