from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import shutil, os, uuid, sys, json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from graph.workflow import graph, FinSightState
from utils.logger import setup_logger
from utils.sanitizer import sanitize_query

from utils.financial_profile import calculate_budget_plan, build_profile_context
from utils.scenario_planner import simulate_scenario
from utils.category_learning import save_category_correction

logger = setup_logger("api")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="FinSight Agent API",
    description="Çok-Ajanlı KOBİ Finansal Analiz Sistemi",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
SESSION_FILE = "session_store.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class CategoryCorrectionRequest(BaseModel):
    aciklama: str
    eski_kategori: str
    yeni_kategori: str

@app.post("/correct-category")
@limiter.limit("30/minute")
async def correct_category(request: Request, correction: CategoryCorrectionRequest):
    """Kullanıcının kategori düzeltmesini öğren."""
    success = save_category_correction(
        aciklama=correction.aciklama,
        eski_kategori=correction.eski_kategori,
        yeni_kategori=correction.yeni_kategori
    )
    return {"success": success, "mesaj": "Kategori öğrenildi."}

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
@limiter.limit("10/minute")
async def upload_file(request: Request, file: UploadFile = File(...)):
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
@limiter.limit("5/minute")
async def analyze(request: Request, session_id: str, query: str = "Bu ay nasıl harcadım?"):
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
        "monthly_summary": result.get("monthly_summary"),
        "categories": result.get("categories"),
        "anomalies": result.get("anomalies"),
        "subscriptions": result.get("subscriptions"),
        "inflation_analysis": result.get("inflation_analysis"),
        "tax_breakdown": result.get("tax_breakdown"),
        "fx_shield": result.get("fx_shield"),
        "proactive_alerts": result.get("proactive_alerts"),
        "parsed_summary": result.get("parsed_summary"),
        "final_response": result.get("final_response"),
        "health_score": result.get("health_score"),
        "transactions": result.get("transactions"),
        "awareness_message": result.get("awareness_message"),
        "behavioral_insights": result.get("behavioral_insights"),
        "predicted_expenses": result.get("predicted_expenses"),
        "cashflow_forecast": result.get("cashflow_forecast"),
    }
    session_store[session_id]["status"] = "analyzed"
    save_sessions(session_store)

    logger.info(f"Analiz tamamlandı — session: {session_id[:8]}")

    return {
        "session_id": session_id,
        "status": "analyzed",
        "monthly_summary": result.get("monthly_summary"),
        "parsed_summary": result.get("parsed_summary"),
        "categories": result.get("categories"),
        "anomalies": result.get("anomalies"),
        "subscriptions": result.get("subscriptions"),
        "proactive_alerts": result.get("proactive_alerts"),
        "fx_shield": result.get("fx_shield"),
        "health_score": result.get("health_score"),
        "awareness_message": result.get("awareness_message"),
        "tax_total": result.get("tax_breakdown", {}).get("TOPLAM", {}).get("toplam_vergi", 0),
        "final_response": result.get("final_response"),
        "behavioral_insights": result.get("behavioral_insights"),
        "predicted_expenses": result.get("predicted_expenses"),
        "cashflow_forecast": result.get("cashflow_forecast"),
    }

@app.post("/query")
@limiter.limit("20/minute")
async def query(request: Request, request_body: QueryRequest):
    if request_body.session_id not in session_store:
        raise HTTPException(404, "Session bulunamadı.")

    cached = session_store[request_body.session_id].get("result")
    if not cached:
        raise HTTPException(400, "Önce /analyze çağırın.")

    clean_query = sanitize_query(request_body.query)  # ← bu satır eklendi
    logger.info(f"Sorgu: {clean_query[:50]} — session: {request_body.session_id[:8]}")

    from agents.advisory_agent import generate_advisory_response
    from utils.context_fetcher import get_market_context

    market_context = get_market_context()

    response = generate_advisory_response(
        user_query=clean_query,  # ← request_body.query yerine clean_query
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
        "session_id": request_body.session_id,
        "query": clean_query,  # ← clean_query döndür
        "response": response
    }

class GoalRequest(BaseModel):
    ad: str
    hedef_tutar: Optional[float] = None
    aylik_butce: Optional[float] = None
    sure_ay: Optional[int] = 12

class FinancialProfileRequest(BaseModel):
    session_id: str
    gelir_kaynak: Optional[str] = "Maaş"
    aylik_gelir: Optional[float] = 0
    ek_gelir: Optional[str] = "Yok"
    borclar: Optional[str] = "Belirtilmedi"
    yatirimlar: Optional[str] = "Belirtilmedi"
    hedefler: Optional[list] = []
    yatirim_tutar: Optional[float] = 0 
    birikim_tutar: Optional[float] = 0
    nakit_tutar: Optional[float] = 0   
    borc_tutar: Optional[float] = 0
    hedefler: Optional[list] = []

class ScenarioRequest(BaseModel):
    session_id: str
    senaryo_tutar: float
    senaryo_aciklama: str
    hedef_tutar: Optional[float] = None
    sure_ay: Optional[int] = 12

class NLPRequest(BaseModel):
    session_id: str
    text: str

@app.post("/profile")
@limiter.limit("10/minute")
async def save_profile(request: Request, profile_req: FinancialProfileRequest):
    if profile_req.session_id not in session_store:
        raise HTTPException(404, "Session bulunamadı.")

    cached = session_store[profile_req.session_id].get("result", {})

    profile = {
        "gelir_kaynak": profile_req.gelir_kaynak,
        "aylik_gelir": profile_req.aylik_gelir,
        "ek_gelir": profile_req.ek_gelir,
        "borclar": profile_req.borclar,
        "yatirimlar": profile_req.yatirimlar,
        "yatirim_tutar": profile_req.yatirim_tutar,  
        "birikim_tutar": profile_req.birikim_tutar, 
        "nakit_tutar": profile_req.nakit_tutar,  
        "borc_tutar": profile_req.borc_tutar,       
    }

    budget_plan = calculate_budget_plan(
        profile=profile,
        categories=cached.get("categories", {}),
        parsed_summary=cached.get("parsed_summary", {}),
        hedefler=profile_req.hedefler
    )

    session_store[profile_req.session_id]["profile"] = profile
    session_store[profile_req.session_id]["budget_plan"] = budget_plan
    save_sessions(session_store)

    logger.info(f"Profil kaydedildi — session: {profile_req.session_id[:8]}")

    return {
        "session_id": profile_req.session_id,
        "profile": profile,
        "budget_plan": budget_plan,
    }

@app.post("/scenario")
@limiter.limit("10/minute")
async def scenario(request: Request, scenario_req: ScenarioRequest):
    if scenario_req.session_id not in session_store:
        raise HTTPException(404, "Session bulunamadı.")

    cached = session_store[scenario_req.session_id].get("result", {})
    parsed_summary = cached.get("parsed_summary", {})

    if not parsed_summary:
        raise HTTPException(400, "Önce /analyze çağırın.")

    result = simulate_scenario(
        senaryo_tutar=scenario_req.senaryo_tutar,
        senaryo_aciklama=scenario_req.senaryo_aciklama,
        parsed_summary=parsed_summary,
        hedef_tutar=scenario_req.hedef_tutar,
        sure_ay=scenario_req.sure_ay
    )

    logger.info(f"Senaryo simüle edildi — session: {scenario_req.session_id[:8]}")
    return result

@app.post("/nlp-transaction")
@limiter.limit("20/minute")
async def nlp_transaction(request: Request, nlp_req: NLPRequest):
    if nlp_req.session_id not in session_store:
        raise HTTPException(404, "Session bulunamadı.")

    from agents.nlp_parser import parse_natural_language, save_nlp_transaction
    from agents.analyst_agent import categorize_transactions

    parsed = parse_natural_language(nlp_req.text)
    saved = save_nlp_transaction(parsed, nlp_req.session_id)

    # Mevcut analizi güncelle
    cached = session_store[nlp_req.session_id].get("result", {})
    if cached and saved:
        mevcut_transactions = cached.get("transactions", []) or []

        # Yeni işlemi listeye ekle
        yeni_islem = {
            "tarih": parsed.get("tarih"),
            "aciklama": parsed.get("aciklama"),
            "tutar": -abs(parsed.get("tutar", 0)) if parsed.get("tur") == "gider"
                     else abs(parsed.get("tutar", 0)),
            "tur": parsed.get("tur", "gider"),
            "kategori": parsed.get("kategori", "diger"),
        }
        mevcut_transactions.append(yeni_islem)

        # Kategorileri yeniden hesapla
        yeni_kategoriler = categorize_transactions(mevcut_transactions)

        # Özeti güncelle
        mevcut_summary = cached.get("parsed_summary", {}) or {}
        if parsed.get("tur") == "gider":
            mevcut_summary["toplam_gider"] = (
                (mevcut_summary.get("toplam_gider") or 0) +
                abs(parsed.get("tutar", 0))
            )
        else:
            mevcut_summary["toplam_gelir"] = (
                (mevcut_summary.get("toplam_gelir") or 0) +
                abs(parsed.get("tutar", 0))
            )

        # Cache'i güncelle
        session_store[nlp_req.session_id]["result"]["transactions"] = mevcut_transactions
        session_store[nlp_req.session_id]["result"]["categories"] = yeni_kategoriler
        session_store[nlp_req.session_id]["result"]["parsed_summary"] = mevcut_summary
        save_sessions(session_store)

        logger.info(
            f"Canlı güncelleme: {parsed.get('aciklama')} — "
            f"yeni kategori toplamları hesaplandı"
        )

    return {
        "session_id": nlp_req.session_id,
        "parsed": parsed,
        "saved": saved,
        "live_update": cached is not None,
        "updated_categories": session_store[nlp_req.session_id].get(
            "result", {}
        ).get("categories", {})
    }

@app.get("/session/{session_id}")
def get_session(session_id: str):
    if session_id not in session_store:
        raise HTTPException(404, "Session bulunamadı.")
    return session_store[session_id]