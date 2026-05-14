from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import shutil, os, uuid, sys, json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from graph.workflow import graph, FinSightState
from utils.logger import setup_logger

logger = setup_logger("api")

app = FastAPI(
    title="FinSight Agent API",
    description="Çok-Ajanlı KOBİ Finansal Analiz Sistemi",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
SESSION_FILE = "session_store.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def load_sessions() -> dict:
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_sessions(store: dict):
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Session kaydetme hatası: {str(e)}")

session_store = load_sessions()

class QueryRequest(BaseModel):
    query: str
    session_id: str

class ProfileRequest(BaseModel):
    session_id: str
    gelir_kaynak: Optional[str] = "Maaş"
    ek_gelir: Optional[str] = "Yok"
    bor: Optional[str] = "Belirtilmedi"
    yatirim: Optional[str] = "Belirtilmedi"

@app.get("/health")
def health():
    return {"status": "ok", "service": "FinSight Agent", "version": "1.0.0"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".png", ".jpg", ".jpeg")):
        raise HTTPException(400, "Sadece PDF veya görüntü dosyası kabul edilir.")

    # Dosya boyutu kontrolü (10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(400, "Dosya boyutu 10MB'ı geçemez.")

    # Magic bytes kontrolü
    if file.filename.endswith(".pdf") and not contents[:4] == b'%PDF':
        raise HTTPException(400, "Geçersiz PDF dosyası.")

    session_id = str(uuid.uuid4())
    file_path = f"{UPLOAD_DIR}/{session_id}_{file.filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    session_store[session_id] = {"file_path": file_path, "status": "uploaded"}
    save_sessions(session_store)

    logger.info(f"Dosya yüklendi: {file.filename} — session: {session_id[:8]}")

    return {
        "session_id": session_id,
        "file_path": file_path,
        "status": "uploaded",
        "message": "Dosya yüklendi. /analyze endpoint'ini çağırın."
    }

@app.post("/analyze")
async def analyze(session_id: str, query: str = "Bu ay nasıl harcadım?"):
    if session_id not in session_store:
        raise HTTPException(404, "Session bulunamadı. Önce /upload çağırın.")

    file_path = session_store[session_id]["file_path"]

    if not os.path.exists(file_path):
        raise HTTPException(404, "Dosya bulunamadı.")

    logger.info(f"Analiz başladı — session: {session_id[:8]}")

    state = FinSightState(
        file_path=file_path,
        user_query=query,
        session_id=session_id,
        raw_text=None, transactions=None,
        parsed_summary=None, categories=None,
        anomalies=None, subscriptions=None,
        inflation_analysis=None, tax_breakdown=None,
        cash_flow_prediction=None, fx_shield=None,
        proactive_alerts=None, final_response=None,
        current_step="parser", errors=[]
    )

    result = graph.invoke(state)

    session_store[session_id]["result"] = {
        "categories": result.get("categories"),
        "anomalies": result.get("anomalies"),
        "subscriptions": result.get("subscriptions"),
        "inflation_analysis": result.get("inflation_analysis"),
        "tax_breakdown": result.get("tax_breakdown"),
        "fx_shield": result.get("fx_shield"),
        "proactive_alerts": result.get("proactive_alerts"),
        "parsed_summary": result.get("parsed_summary"),
        "final_response": result.get("final_response"),
        "transactions": result.get("transactions"),
    }
    session_store[session_id]["status"] = "analyzed"
    save_sessions(session_store)

    logger.info(f"Analiz tamamlandı — session: {session_id[:8]}")

    return {
        "session_id": session_id,
        "status": "analyzed",
        "parsed_summary": result.get("parsed_summary"),
        "categories": result.get("categories"),
        "anomalies": result.get("anomalies"),
        "subscriptions": result.get("subscriptions"),
        "proactive_alerts": result.get("proactive_alerts"),
        "fx_shield": result.get("fx_shield"),
        "tax_total": result.get("tax_breakdown", {}).get("TOPLAM", {}).get("toplam_vergi", 0),
        "final_response": result.get("final_response"),
    }

@app.post("/query")
async def query(request: QueryRequest):
    if request.session_id not in session_store:
        raise HTTPException(404, "Session bulunamadı.")

    cached = session_store[request.session_id].get("result")
    if not cached:
        raise HTTPException(400, "Önce /analyze çağırın.")

    logger.info(f"Sorgu: {request.query[:50]} — session: {request.session_id[:8]}")

    from agents.advisory_agent import generate_advisory_response
    from utils.context_fetcher import get_market_context

    market_context = get_market_context()

    response = generate_advisory_response(
        user_query=request.query,
        categories=cached.get("categories", {}),
        inflation_analysis=cached.get("inflation_analysis", {}),
        tax_breakdown=cached.get("tax_breakdown", {}),
        anomalies=cached.get("anomalies", []),
        subscriptions=cached.get("subscriptions", []),
        parsed_summary=cached.get("parsed_summary", {}),
        fx_shield=cached.get("fx_shield", {}),
        market_context=market_context,
        proactive_alerts=cached.get("proactive_alerts", []),
    )

    return {
        "session_id": request.session_id,
        "query": request.query,
        "response": response
    }

@app.get("/session/{session_id}")
def get_session(session_id: str):
    if session_id not in session_store:
        raise HTTPException(404, "Session bulunamadı.")
    return session_store[session_id]