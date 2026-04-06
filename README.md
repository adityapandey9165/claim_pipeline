# Claim Processing Pipeline

A FastAPI + LangGraph multi-agent service that processes PDF insurance claims by classifying pages and extracting structured data using local AI agents.

## Architecture

```text
START → [Segregator Agent (LLAVA vision)] → [ID Agent] ----------------------↘
                       ↓                → [Discharge Summary Agent] → [Aggregator] → END
               classifies pages            → [Itemized Bill Agent]   ↗
               into 9 doc types,
               routes relevant pages
```

### Nodes

| Node | Role |
|------|------|
| **Segregator** | AI-powered: sends all pages to Claude vision, classifies each into 1 of 9 doc types |
| **ID Agent** | Extracts patient identity, policy, and claim reference data |
| **Discharge Summary Agent** | Extracts admission/discharge dates, diagnosis, physician, medications |
| **Itemized Bill Agent** | Extracts all line items, totals, insurance coverage amounts |
| **Aggregator** | Combines all results into a single structured JSON response |

### Document Types Recognized
- `claim_forms`
- `cheque_or_bank_details`
- `identity_document`
- `itemized_bill`
- `discharge_summary`
- `prescription`
- `investigation_report`
- `cash_receipt`
- `other`

## Setup

### 1. Clone & Install

```bash
git clone <repo>
cd claim_pipeline
pip install -r requirements.txt
```

### 2. Set API Key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Usage

### POST /api/process

**Request** (multipart/form-data):
- `claim_id` (string) — unique claim identifier
- `file` (PDF) — the claim PDF file

**Example with curl:**
```bash
curl -X POST http://localhost:8000/api/process \
  -F "claim_id=CLM-2025-001" \
  -F "file=@final_image_protected.pdf"
```

**Example with Python:**
```python
import requests

with open("final_image_protected.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/process",
        data={"claim_id": "CLM-2025-001"},
        files={"file": ("claim.pdf", f, "application/pdf")}
    )
print(response.json())
```

### Response Structure

```json
{
  "claim_id": "CLM-2025-001",
  "processed_at": "2025-04-06T10:00:00Z",
  "total_pages": 18,
  "document_classification": {
    "claim_forms": {"pages": [1], "page_count": 1},
    "cheque_or_bank_details": {"pages": [2], "page_count": 1},
    "identity_document": {"pages": [3], "page_count": 1},
    "discharge_summary": {"pages": [4], "page_count": 1},
    "itemized_bill": {"pages": [9], "page_count": 1},
    ...
  },
  "identity_and_policy": {
    "patient_name": "John Michael Smith",
    "date_of_birth": "March 15, 1985",
    "policy_number": "POL-987654321",
    "insurance_provider": "HealthCare Insurance Company",
    ...
  },
  "clinical_summary": {
    "admission_date": "January 20, 2025",
    "discharge_date": "January 25, 2025",
    "admission_diagnosis": "Community Acquired Pneumonia (CAP)",
    "attending_physician": "Dr. Sarah Johnson, MD",
    ...
  },
  "billing_details": {
    "total_amount": 6418.65,
    "insurance_payment": 5134.92,
    "patient_responsibility": 1283.73,
    "items": [...]
  },
  "claim_summary": {
    "patient_name": "John Michael Smith",
    "policy_number": "POL-987654321",
    "total_bill_amount": 6418.65,
    "patient_responsibility": 1283.73
  }
}
```

## Project Structure

```
claim_pipeline/
├── main.py                    # FastAPI app & /api/process endpoint
├── workflow.py                # LangGraph workflow definition
├── requirements.txt
├── agents/
│   ├── segregator.py          # AI page classifier (vision)
│   ├── id_agent.py            # Identity/policy extractor
│   ├── discharge_agent.py     # Clinical data extractor
│   ├── bill_agent.py          # Billing/itemized charges extractor
│   └── aggregator.py          # Result combiner
└── utils/
    ├── pdf_utils.py           # PDF → page images/text
    └── state.py               # LangGraph TypedDict state
```

## How the Segregator Works

1. Opens the PDF using PyMuPDF
2. Renders each page as a PNG image (1.5x scale)
3. Sends ALL page images to Claude (claude-sonnet-4) in a single API call
4. Claude returns a JSON mapping `{page_num: doc_type}`
5. The mapping is inverted to `{doc_type: [page_nums]}`
6. Each extraction agent receives only its relevant page images

## Deployment (Render)

1. Push to GitHub
2. Create new Web Service on [render.com](https://render.com)
3. Set `ANTHROPIC_API_KEY` in environment variables
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Tech Stack

- **FastAPI** — REST API framework
- **LangGraph** — Agent workflow orchestration
- **Anthropic Claude** — AI for page classification and data extraction (vision)
- **PyMuPDF** — PDF rendering to images
- **Pydantic** — Data validation