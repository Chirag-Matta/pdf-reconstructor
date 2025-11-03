# app.py

import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from services.pdf_svc import extract_texts_from_pdf_bytes, reorder_pdf_bytes
from services.ordering_svc import Orchestrator
from typing import List, Dict, Any
import tempfile
import os
import json
from rich import print
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware



load_dotenv()

app = FastAPI(title="Reconstruct Jumbled PDF - MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()

@app.post("/reconstruct")
async def reconstruct_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")
    
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    # Extract page texts (OCR fallback included)
    print("[blue]Extracting texts from PDF...[/blue]")
    try:
        page_texts = extract_texts_from_pdf_bytes(raw)
    except Exception as e:
        print(f"[red]Extraction failed: {e}[/red]")
        raise HTTPException(status_code=500, detail="Failed to extract text from PDF")
    
    print(f"[green]Extracted {len(page_texts)} pages[/green]")
    
    final_order, final_confidences = orchestrator.get_order(page_texts)

    
    # Rebuild reordered PDF
    print("[blue]Rebuilding PDF with new order...[/blue]")
    try:
        reordered_bytes = reorder_pdf_bytes(raw, final_order)
    except Exception as e:
        print(f"[red]PDF reassembly failed: {e}[/red]")
        raise HTTPException(status_code=500, detail="Failed to rebuild reordered PDF")
    
    # Save temporary file to return via StreamingResponse
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(reordered_bytes)
    tmp.flush()
    tmp.close()
    
    result = {
        "original_filename": file.filename,
        "page_count": len(page_texts),
        "final_order": final_order,
        "confidences": final_confidences,
        "avg_confidence": sum(final_confidences) / len(final_confidences) if final_confidences else 0.0,
    }
    
    # Debug logging
    with open("ordering_debug.json", "w") as f:
        json.dump({
            "final_order": final_order,
            "confidences": final_confidences,
            "avg_confidence": result["avg_confidence"]
        }, f, indent=2)
    
    print(f"[green]✓ PDF reconstruction complete[/green]")
    print(f"[green]  Original order: [0, 1, 2, ..., {len(page_texts)-1}][/green]")
    print(f"[green]  Final order: {final_order}[/green]")
    
    # Write log JSON alongside tmp PDF
    log_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w")
    json.dump(result, log_tmp, indent=2)
    log_tmp.flush()
    log_tmp.close()
    
    return StreamingResponse(
        open(tmp.name, "rb"),
        media_type="application/pdf",
        headers={
            "X-Result-Meta": json.dumps(result),
            "Content-Disposition": f'attachment; filename="reconstructed_{file.filename}"'
        }
    )

@app.get("/")
async def health():
    return {"status": "ok", "note": "POST a PDF to /reconstruct"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)