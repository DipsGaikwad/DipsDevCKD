from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from backend.agents.data_agent import validate_patient_data
from backend.agents.trend_agent import analyze_trends
from backend.agents.prediction_agent import predict_progression
from backend.agents.explanation_agent import explain_prediction

class CKDState(TypedDict):
    baseline_data: Dict[str, Any]
    visits: List[Dict[str, Any]]
    validation_status: str
    issues: List[str]
    trends: Dict[str, Any]
    prediction: Dict[str, Any]
    features_df_dict: Dict[str, Any]
    explanations: List[Dict[str, Any]]

def data_validator_node(state: CKDState):
    result = validate_patient_data(state["visits"])
    return {"validation_status": result["status"], "issues": result["issues"]}

def trend_analyzer_node(state: CKDState):
    return {"trends": analyze_trends(state["visits"])}

def prediction_node(state: CKDState):
    result = predict_progression(state["baseline_data"], state["trends"])
    if "error" in result:
        return {"prediction": result}
    
    features_dict = result["features_df"].to_dict(orient="records")[0]
    return {
        "prediction": {"risk_level": result["risk_level"], "probability": result["probability"]},
        "features_df_dict": features_dict
    }

def explanation_node(state: CKDState):
    import pandas
    df = pandas.DataFrame([state["features_df_dict"]])
    return {"explanations": explain_prediction(df)}

def route_after_validation(state: CKDState):
    return "stop" if state["validation_status"] == "INVALID" else "continue"

workflow = StateGraph(CKDState)
workflow.add_node("validator", data_validator_node)
workflow.add_node("trend", trend_analyzer_node)
workflow.add_node("predictor", prediction_node)
workflow.add_node("explainer", explanation_node)
workflow.set_entry_point("validator")
workflow.add_conditional_edges("validator", route_after_validation, {"continue": "trend", "stop": END})
workflow.add_edge("trend", "predictor")
workflow.add_edge("predictor", "explainer")
workflow.add_edge("explainer", END)
ckd_graph = workflow.compile()

def run_ckd_pipeline(baseline_data: dict, visits: list) -> dict:
    initial_state = {
        "baseline_data": baseline_data, "visits": visits, "validation_status": "",
        "issues": [], "trends": {}, "prediction": {}, "features_df_dict": {}, "explanations": []
    }
    
    final_state = ckd_graph.invoke(initial_state)
    
    if final_state["validation_status"] == "INVALID" or "error" in final_state["prediction"]:
        return {"error": "Pipeline failed", "details": final_state["issues"]}
        
    return {
        "status": "success",
        "risk_level": final_state["prediction"]["risk_level"],
        "probability": final_state["prediction"]["probability"],
        "egfr_trend": final_state["trends"].get("egfr_trend", "unknown"),
        "top_factors": final_state["explanations"]
    }