from pydantic import BaseModel
from typing import List, Dict, Any

class BaselineData(BaseModel):
    age_at_baseline: float
    gender: int
    ihd: int
    cvd: int
    hypertension: int
    diabetes: int
    dyslipidemia: int
    baseline_sbp: float
    baseline_dbp: float
    baseline_bmi: float
    baseline_egfr: float
    baseline_hb: float
    baseline_chol: float
    baseline_tg: float
    baseline_ldl: float
    baseline_hdl: float
    baseline_albuminuria: float
    raasi: int
    glp1ra: int
    sglt2i: int
    statin: int

class VisitData(BaseModel):
    visit_date: str
    egfr_ml_min_1_73m2: float
    creatinine_mg_dl: float

class PatientRequest(BaseModel):
    baseline_data: BaselineData
    visits: List[VisitData]

class PredictionResponse(BaseModel):
    status: str
    risk_level: str
    probability: float
    egfr_trend: str
    top_factors: List[Dict[str, Any]]