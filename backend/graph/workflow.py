from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END

class FinSightState(TypedDict):
    file_path: Optional[str]
    user_query: Optional[str]
    raw_text: Optional[str]
    transactions: Optional[List[dict]]
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

def parser_node(state: FinSightState) -> dict:
    print("[Parser Agent] Çalışıyor...")
    return {
        "raw_text": "STUB: Gün 2'de Gemini Vision ile doldurulacak",
        "transactions": [
            {"date": "2026-05-01", "description": "Migros", "amount": -450.0, "currency": "TRY"},
            {"date": "2026-05-02", "description": "Netflix", "amount": -299.99, "currency": "TRY"},
            {"date": "2026-05-03", "description": "Shell", "amount": -1200.0, "currency": "TRY"},
        ],
        "current_step": "analyst"
    }

def analyst_node(state: FinSightState) -> dict:
    print("[Analyst Agent] Çalışıyor...")
    return {
        "categories": {"gida": 450.0, "eglence": 299.99, "ulasim": 1200.0},
        "anomalies": [],
        "inflation_analysis": {},
        "tax_breakdown": {},
        "current_step": "advisory"
    }

def advisory_node(state: FinSightState) -> dict:
    print("[Advisory Agent] Çalışıyor...")
    return {
        "final_response": "Analiz tamamlandı. Gün 4'te gerçek yanıt üretilecek.",
        "proactive_alerts": [],
        "current_step": "done"
    }

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

    workflow.add_conditional_edges(
        "parser", route_step,
        {"analyst": "analyst", "done": END}
    )
    workflow.add_conditional_edges(
        "analyst", route_step,
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
        "file_path": "test.pdf",
        "user_query": "Bu ay en çok neye harcadım?",
        "raw_text": None, "transactions": None,
        "categories": None, "anomalies": None,
        "inflation_analysis": None, "tax_breakdown": None,
        "cash_flow_prediction": None, "fx_shield": None,
        "proactive_alerts": None, "final_response": None,
        "current_step": "parser", "errors": []
    })
    print("\nGraf tamamlandı:")
    print(f"  Kategoriler : {result.get('categories')}")
    print(f"  Yanıt       : {result.get('final_response')}")