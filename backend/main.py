from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import shutil, os, uuid
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from graph.workflow import graph, FinSightState

app = FastAPI(
    title="FinSight Agent API",
    description="Çok-Ajanlı KOBİ Finansal Analiz Sistemi",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

@app.get("/health")
def health():
    return {"status": "ok", "service": "FinSight Agent"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".png", ".jpg", ".jpeg")):
        raise HTTPException(400, "Sadece PDF veya görüntü dosyası kabul edilir.")
    file_id = str(uuid.uuid4())
    file_path = f"{UPLOAD_DIR}/{file_id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"file_id": file_id, "file_path": file_path, "status": "uploaded"}

@app.post("/analyze")
async def analyze(file_id: str, query: str = "Genel analiz yap"):
    state = FinSightState(
        file_path=f"{UPLOAD_DIR}/{file_id}",
        user_query=query,
        raw_text=None, transactions=None,
        categories=None, anomalies=None,
        inflation_analysis=None, tax_breakdown=None,
        cash_flow_prediction=None, fx_shield=None,
        proactive_alerts=None, final_response=None,
        current_step="parser", errors=[]
    )
    result = graph.invoke(state)
    return result

@app.post("/query")
async def query(request: QueryRequest):
    return {"query": request.query, "response": "Gün 4'te aktif olacak."}