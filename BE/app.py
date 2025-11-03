# app.py
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from processor import extract_texts_from_pdf_bytes
from ordering import Orderer
from pdf_utils import reorder_pdf_bytes
from typing import List, Dict, Any
import tempfile
import os
import json
from rich import print
from dotenv import load_dotenv

load_dotenv()  # loads .env for OPENAI_API_KEY and TESSERACT_CMD if provided

app = FastAPI(title="Reconstruct Jumbled PDF - MVP")

orderer = Orderer()

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

    # Summaries: short first-200 char snippets as page summaries for LLM if needed
    page_summaries = [ (t[:500] + "...") if len(t)>500 else t for t in page_texts ]

    # Embeddings and similarity
    print("[blue]Embedding pages...[/blue]")
    embs = orderer.embed_pages(page_texts)
    sim = orderer.similarity_matrix(embs)

    # Coarse order (greedy)
    initial_order, confidences = orderer.greedy_order(sim)

    # Optionally refine with LLM
    refined = orderer.refine_with_llm(page_summaries, initial_order)
    final_order = refined if refined is not None else initial_order

    # Map confidences to final order (best-effort: reorder confidences by mapping)
    # Build transition confidences aligned to final order
    conf_map = {p: c for p, c in zip(initial_order, confidences)}
    final_confidences = [conf_map.get(p, 0.0) for p in final_order]

    # Rebuild reordered PDF
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
        "initial_order": initial_order,
        "final_order": final_order,
        "confidences": final_confidences,
        "summaries": page_summaries
    }

    # Write log JSON alongside tmp PDF
    log_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w")
    json.dump(result, log_tmp, indent=2)
    log_tmp.flush()
    log_tmp.close()

    # Return a JSON response with links? For simplicity return JSON and provide file bytes in response
    # We'll return the PDF as streaming response and the metadata JSON as headers (or client can call metadata endpoint).
    return StreamingResponse(open(tmp.name, "rb"), media_type="application/pdf", headers={
        "X-Result-Meta": json.dumps(result)
    })

@app.get("/")
async def health():
    return {"status": "ok", "note": "POST a PDF to /reconstruct"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
