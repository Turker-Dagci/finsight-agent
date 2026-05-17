from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from utils.logger import setup_logger
logger = setup_logger("workflow")
from agents.parser_agent import parse_pdf, save_to_qdrant
import uuid
from agents.analyst_agent import run_analyst
from agents.advisory_agent import run_advisory
from agents.analyst_agent import run_analyst

from utils.health_score import calculate_health_score
from utils.awareness import get_awareness_message
from utils.monthly_summary import generate_monthly_summary
from utils.predicted_expenses import predict_upcoming_expenses
from utils.cashflow_forecast import forecast_cashflow

class FinSightState(TypedDict):
    cashflow_forecast: Optional[dict]
    predicted_expenses: Optional[dict]
    monthly_summary: Optional[str]
    behavioral_insights: Optional[List[str]]
    file_path: Optional[str]
    user_query: Optional[str]
    session_id: Optional[str]
    raw_text: Optional[str]
    transactions: Optional[List[dict]]
    parsed_summary: Optional[dict]
    categories: Optional[dict]
    anomalies: Optional[List[str]]
    inflation_analysis: Optional[dict]
    tax_breakdown: Optional[dict]
    cash_flow_prediction: Optional[dict]
    fx_shield: Optional[dict]
    proactive_alerts: Optional[List[str]]
    final_response: Optional[str]
    current_step: str
    errors: List[str]
    health_score: Optional[dict]
    awareness_message: Optional[str]
    subscription_insights: Optional[dict]
    subscriptions: Optional[List[dict]]

def parser_node(state: FinSightState) -> dict:
    logger.info("Parser Agent başladı")
    try:
        file_path = state.get("file_path")
        session_id = state.get("session_id") or str(uuid.uuid4())

        parsed = parse_pdf(file_path)
        save_to_qdrant(parsed, session_id)

        return {
            "session_id": session_id,
            "transactions": parsed.get("islemler", []),
            "parsed_summary": {
                "hesap_sahibi": parsed.get("hesap_sahibi"),
                "donem": parsed.get("donem"),
                "toplam_gelir": parsed.get("toplam_gelir"),
                "toplam_gider": parsed.get("toplam_gider"),
            },
            "current_step": "analyst"
        }
    except Exception as e:
        logger.error(f"Parser hatası: {str(e)}", exc_info=True)
        return {
            "errors": [str(e)],
            "transactions": [],
            "current_step": "done"
        }

def analyst_node(state: FinSightState) -> dict:
    logger.info("Analyst Agent başladı")
    try:
        transactions = state.get("transactions", [])
        parsed_summary = state.get("parsed_summary", {})
        result = run_analyst(transactions, parsed_summary)
        return {
            "categories": result["categories"],
            "anomalies": result["anomalies"],
            "subscriptions": result.get("subscriptions", []),
            "inflation_analysis": result["inflation_analysis"],
            "tax_breakdown": result["tax_breakdown"],
            "behavioral_insights": result.get("behavioral_insights", []),
            "current_step": "advisory"
        }
    except Exception as e:
        logger.error(f"Analyst hatası: {str(e)}", exc_info=True)
        return {"errors": [str(e)], "current_step": "done"}

def advisory_node(state: FinSightState) -> dict:
    logger.info("Advisory Agent başladı")
    try:
        result = run_advisory(
            user_query=state.get("user_query", "Genel analiz yap"),
            categories=state.get("categories", {}),
            inflation_analysis=state.get("inflation_analysis", {}),
            tax_breakdown=state.get("tax_breakdown", {}),
            anomalies=state.get("anomalies", []),
            subscriptions=state.get("subscriptions", []),
            parsed_summary=state.get("parsed_summary", {}),
        )

        health = calculate_health_score(
            parsed_summary=state.get("parsed_summary", {}),
            categories=state.get("categories", {}),
            inflation_analysis=state.get("inflation_analysis", {}),
            subscriptions=state.get("subscriptions", []),
            anomalies=state.get("anomalies", [])
        )

        awareness = get_awareness_message(
            categories=state.get("categories", {}),
            subscriptions=state.get("subscriptions", []),
            health_score=health.get("toplam_skor")
        )

        monthly_summary = generate_monthly_summary(
            categories=state.get("categories", {}),
            parsed_summary=state.get("parsed_summary", {}),
            inflation_analysis=state.get("inflation_analysis", {}),
            anomalies=state.get("anomalies", []),
            subscriptions=state.get("subscriptions", []),
            health_score=health
        )

        predicted = predict_upcoming_expenses(
            transactions=state.get("transactions", []),
            categories=state.get("categories", {}),
            subscriptions=state.get("subscriptions", [])
        )

        cashflow = forecast_cashflow(
            parsed_summary=state.get("parsed_summary", {}),
            categories=state.get("categories", {}),
            predicted_expenses=predicted
        )

        return {
            "fx_shield": result["fx_shield"],
            "proactive_alerts": result["proactive_alerts"],
            "final_response": result["final_response"],
            "health_score": health,
            "awareness_message": awareness,
            "monthly_summary": monthly_summary,
            "predicted_expenses": predicted,
            "cashflow_forecast": cashflow,
            "current_step": "done"
        }
    except Exception as e:
        logger.error(f"Advisory hatası: {str(e)}", exc_info=True)
        return {"errors": [str(e)], "current_step": "done"}

# Yeni node ekle — subscription optimizer
def subscription_optimizer_node(state: FinSightState) -> dict:
    logger.info("Subscription Optimizer Agent başladı")
    try:
        subscriptions = state.get("subscriptions", [])
        categories = state.get("categories", {})
        
        toplam_gider = sum(categories.values())
        toplam_abone = sum(s["tutar"] for s in subscriptions)
        
        oneriler = []
        for s in subscriptions:
            # Döviz bazlı abonelik tespiti
            doviz_keywords = ["netflix", "spotify", "amazon", "apple", "youtube", "openai"]
            if any(k in s["aciklama"].lower() for k in doviz_keywords):
                oneriler.append(
                    f"'{s['aciklama']}' döviz bazlı abonelik — "
                    f"TL maliyeti her ay artıyor ({s['tutar']:.0f} TL)"
                )
            else:
                oneriler.append(
                    f"'{s['aciklama']}' aboneliğini değerlendirin ({s['tutar']:.0f} TL/ay)"
                )
        
        tasarruf_potansiyeli = round(toplam_abone * 0.4, 2)
        
        logger.info(f"Abonelik optimizasyonu: {len(oneriler)} öneri, "
                   f"{tasarruf_potansiyeli} TL tasarruf potansiyeli")
        
        return {
            "subscription_insights": {
                "oneriler": oneriler,
                "toplam_abone_gider": toplam_abone,
                "tasarruf_potansiyeli": tasarruf_potansiyeli,
                "abone_gider_orani": round(toplam_abone / toplam_gider * 100, 1) if toplam_gider > 0 else 0
            },
            "current_step": "advisory"
        }
    except Exception as e:
        logger.error(f"Subscription Optimizer hatası: {str(e)}", exc_info=True)
        return {"current_step": "advisory"}


# Mevcut route_step'i bu yeni versiyonla değiştir
def route_after_analyst(state: FinSightState) -> str:
    """
    Analyst sonucuna göre dinamik routing.
    Gerçek agentic karar verme burada.
    """
    anomalies = state.get("anomalies", [])
    subscriptions = state.get("subscriptions", [])
    categories = state.get("categories", {})

    toplam_gider = sum(categories.values()) if categories else 0
    toplam_abone = sum(s["tutar"] for s in subscriptions) if subscriptions else 0

    # Abonelik yükü %15'i geçiyorsa optimizer devreye girer
    if toplam_gider > 0 and toplam_abone / toplam_gider > 0.15:
        logger.info(f"Abonelik yükü yüksek (%{toplam_abone/toplam_gider*100:.1f}) "
                   f"— Subscription Optimizer devreye giriyor")
        return "subscription_optimizer"

    # Kritik anomali varsa direkt advisory
    if len(anomalies) > 2:
        logger.info(f"{len(anomalies)} anomali tespit edildi — direkt Advisory'e geçiliyor")
        return "advisory"

    # Normal akış
    logger.info("Normal akış — Advisory'e geçiliyor")
    return "advisory"

def route_step(state: FinSightState) -> str:
    step = state.get("current_step", "done")
    if step in ["analyst", "advisory", "done"]:
        return step
    return "done"

def build_graph():
    workflow = StateGraph(FinSightState)

    workflow.add_node("parser", parser_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("subscription_optimizer", subscription_optimizer_node)
    workflow.add_node("advisory", advisory_node)

    workflow.set_entry_point("parser")

    workflow.add_conditional_edges(
        "parser", route_step,
        {"analyst": "analyst", "done": END}
    )

    # Analyst'tan sonra dinamik routing
    workflow.add_conditional_edges(
        "analyst", route_after_analyst,
        {
            "subscription_optimizer": "subscription_optimizer",
            "advisory": "advisory"
        }
    )

    # Optimizer her zaman advisory'e geçer
    workflow.add_conditional_edges(
        "subscription_optimizer", route_step,
        {"advisory": "advisory", "done": END}
    )

    workflow.add_conditional_edges(
        "advisory", route_step,
        {"done": END}
    )

    return workflow.compile()

graph = build_graph()

if __name__ == "__main__":
    result = graph.invoke({
        "file_path": "data/samples/demo_ekstre.pdf",
        "user_query": "Bu ay en çok neye harcadım?",
        "session_id": None,
        "subscription_insights": None,
        "raw_text": None, "transactions": None,
        "parsed_summary": None, "categories": None,
        "anomalies": None, "inflation_analysis": None,
        "tax_breakdown": None, "cash_flow_prediction": None,
        "fx_shield": None, "proactive_alerts": None,
        "final_response": None, "current_step": "parser",
        "errors": []
    })
    print("\nGraf tamamlandı:")
    print(f"  Session    : {result.get('session_id')}")
    print(f"  İşlem sayısı: {len(result.get('transactions', []))}")
    print(f"  Özet       : {result.get('parsed_summary')}")