# app.py

import os
import io
import re
import sys
import json
import tempfile
from urllib.parse import quote
from contextlib import redirect_stdout, redirect_stderr
from typing import List, Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Form
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from rich import print as rich_print
from dotenv import load_dotenv

from services.pdf_svc import extract_texts_from_pdf_bytes, reorder_pdf_bytes
from services.ordering_svc import Orchestrator


load_dotenv()

app = FastAPI(title="Reconstruct Jumbled PDF - MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080" , "http://192.168.1.38:8080"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Result-Meta"],
)

# Store logs for this request
request_logs = []

class LogCapture(io.StringIO):
    """Custom StringIO that captures both terminal output and stores it"""
    def __init__(self):
        super().__init__()
        self.logs = []
        self.buffer = ""
        
    def write(self, text):
        if text and text.strip():
            # Write to actual stdout so it appears in terminal
            sys.__stdout__.write(text)
            
            # Store clean version for frontend
            # Remove ANSI color codes
            clean_text = re.sub(r'\x1b\[[0-9;]*m', '', text)
            # Remove rich formatting
            clean_text = re.sub(r'\[/?[a-z]+\]', '', clean_text)
            clean_text = clean_text.strip()
            
            if clean_text:
                # Buffer incomplete lines
                self.buffer += clean_text
                
                # If we have a complete line (ends with newline in original), store it
                if text.endswith('\n'):
                    if self.buffer:
                        self.logs.append(self.buffer)
                        self.buffer = ""
                elif '\n' in text:
                    # Handle multiple lines
                    lines = self.buffer.split('\n')
                    for line in lines[:-1]:
                        if line.strip():
                            self.logs.append(line.strip())
                    self.buffer = lines[-1]
        
        return len(text)
    
    def flush(self):
        sys.__stdout__.flush()
        # Flush any remaining buffer
        if self.buffer:
            self.logs.append(self.buffer)
            self.buffer = ""

orchestrator = Orchestrator()

@app.post("/reconstruct")
async def reconstruct_pdf(
    file: UploadFile = File(...),
    disposition: str = Query("inline", enum=["inline", "attachment"]),
    save_path: Optional[str] = Form(None)
):
    # Create log capture
    log_capture = LogCapture()
    
    # Redirect stdout and stderr to our capture
    with redirect_stdout(log_capture), redirect_stderr(log_capture):
        try:
            if not file.filename.lower().endswith(".pdf"):
                rich_print("[red]Only PDF files accepted[/red]")
                raise HTTPException(status_code=400, detail="Only PDF files accepted")
            
            raw = await file.read()
            if not raw:
                rich_print("[red]Empty file uploaded[/red]")
                raise HTTPException(status_code=400, detail="Empty file uploaded")
            
            # Extract page texts (OCR fallback included)
            rich_print("[blue]Extracting texts from PDF...[/blue]")
            page_texts = extract_texts_from_pdf_bytes(raw)
            
            rich_print(f"[green]Extracted {len(page_texts)} pages[/green]")
            
            # Get ordering from orchestrator (this will print all the strategy logs)
            final_order, final_confidences = orchestrator.get_order(page_texts)

            # Rebuild reordered PDF
            rich_print("[blue]Rebuilding PDF with new order...[/blue]")
            reordered_bytes = reorder_pdf_bytes(raw, final_order)
            
            rich_print(f"[green]✓ PDF reconstruction complete[/green]")
            rich_print(f"[green]  Original order: [0, 1, 2, ..., {len(page_texts)-1}][/green]")
            rich_print(f"[green]  Final order: {final_order}[/green]")
            
            # Prepare result metadata
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
            
            # Get all captured logs
            log_capture.flush()  # Flush any remaining buffer
            all_logs = log_capture.logs
            
            rich_print(f"[cyan]Captured {len(all_logs)} log entries[/cyan]")
            
            # Check if custom save path was provided
            if save_path:
                rich_print(f"[blue]💾 Saving to custom location: {save_path}[/blue]")
                
                # Ensure directory exists
                save_dir = os.path.dirname(save_path)
                if save_dir:
                    os.makedirs(save_dir, exist_ok=True)
                    rich_print(f"[blue]📁 Directory verified: {save_dir}[/blue]")
                
                # Write PDF to custom location
                with open(save_path, "wb") as f:
                    f.write(reordered_bytes)
                rich_print("[green]✅ File saved successfully![/green]")
                
                # Also save metadata alongside
                metadata_path = save_path.replace(".pdf", "_metadata.json")
                with open(metadata_path, "w") as f:
                    json.dump(result, f, indent=2)
                rich_print(f"[blue]📄 Metadata saved to: {metadata_path}[/blue]")
                
                # Get final logs including save operations
                log_capture.flush()
                all_logs = log_capture.logs
                
                # Return JSON response with logs
                return JSONResponse(
                    content={
                        "status": "success",
                        "saved_path": save_path,
                        "metadata_path": metadata_path,
                        "logs": all_logs,
                        "result": result
                    },
                    headers={
                        "X-Backend-Logs": quote(json.dumps(all_logs))
                    }
                )
            else:
                # Return file for browser download
                # Save temporary file
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                tmp.write(reordered_bytes)
                tmp.flush()
                tmp.close()

                # Write metadata to temp file
                log_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w")
                json.dump(result, log_tmp, indent=2)
                log_tmp.flush()
                log_tmp.close()
                
                content_disposition = f'{disposition}; filename="reconstructed_{file.filename}"'
                
                return StreamingResponse(
                    open(tmp.name, "rb"),
                    media_type="application/pdf",
                    headers={
                        "X-Result-Meta": json.dumps(result),
                        "X-Backend-Logs": quote(json.dumps(all_logs)),
                        "Content-Disposition": content_disposition
                    }
                )
        
        except HTTPException:
            raise
        except Exception as e:
            rich_print(f"[red]❌ Error: {str(e)}[/red]")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/")
async def health():
    return {"status": "ok", "note": "POST a PDF to /reconstruct"}

if __name__ == "__main__":
    print("🚀 Starting PDF Reconstruction Server")
    print("📍 Server: http://localhost:8000")
    print("📝 All terminal output will be captured and sent to frontend")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

