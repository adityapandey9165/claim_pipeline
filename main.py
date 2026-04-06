import os
import shutil
import tempfile
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from workflow import workflow
from utils.state import ClaimState

app = FastAPI(
    title="Claim Processing Pipeline",
    description="FastAPI + LangGraph multi-agent PDF claim processor",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "service": "Claim Processing Pipeline",
        "version": "1.0.0",
        "endpoints": {
            "process_claim": "POST /api/process",
            "health": "GET /health"
        }
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/process")
async def process_claim(
    claim_id: str = Form(...),
    file: UploadFile = File(...)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # Save uploaded file to temp location
    tmp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(tmp_dir, f"{claim_id}.pdf")
    
    try:
        with open(pdf_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"\n{'='*60}")
        print(f"Processing claim: {claim_id}")
        print(f"File: {file.filename} ({len(content)/1024:.1f} KB)")
        print(f"{'='*60}\n")
        
        # Initialize state
        initial_state: ClaimState = {
            "claim_id": claim_id,
            "pdf_path": pdf_path,
            "all_pages": [],
            "page_classification": {},
            "id_result": None,
            "discharge_result": None,
            "itemized_bill_result": None,
            "final_result": None,
            "error": None
        }
        
        # Run the LangGraph workflow
        final_state = workflow.invoke(initial_state)
        
        if final_state.get("error"):
            raise HTTPException(status_code=500, detail=final_state["error"])
        
        return JSONResponse(content=final_state["final_result"])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)