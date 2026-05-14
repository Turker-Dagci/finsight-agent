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

class FinSightState(TypedDict):
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
        return {
            "fx_shield": result["fx_shield"],
            "proactive_alerts": result["proactive_alerts"],
            "final_response": result["final_response"],
            "current_step": "done"
        }
    except Exception as e:
        logger.error(f"Advisory hatası: {str(e)}", exc_info=True)
        return {"errors": [str(e)], "current_step": "done"}

def route_step(state: FinSightState) -> str:
    step = state.get("current_step", "done")
    if step in ["analyst", "advisory", "done"]:
        return step
    return "done"

def build_graph():
    workflow = StateGraph(FinSightState)
    workflow.add_node("parser", parser_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("advisory", advisory_node)
    workflow.set_entry_point("parser")
    workflow.add_conditional_edges("parser", route_step, {"analyst": "analyst", "done": END})
    workflow.add_conditional_edges("analyst", route_step, {"advisory": "advisory", "done": END})
    workflow.add_conditional_edges("advisory", route_step, {"done": END})
    return workflow.compile()

graph = build_graph()

if __name__ == "__main__":
    result = graph.invoke({
        "file_path": "data/samples/demo_ekstre.pdf",
        "user_query": "Bu ay en çok neye harcadım?",
        "session_id": None,
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