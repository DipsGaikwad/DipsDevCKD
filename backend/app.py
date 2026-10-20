from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas import PatientRequest, PredictionResponse
from backend.agents.orchestrator import run_ckd_pipeline

app = FastAPI(title="CKD Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "CKD Prediction API is running!"}

@app.post("/predict", response_model=PredictionResponse)
def predict_patient(request: PatientRequest):
    baseline_dict = request.baseline_data.model_dump()
    visits_list = [visit.model_dump() for visit in request.visits]
    
    result = run_ckd_pipeline(baseline_dict, visits_list)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["details"])
        
    return result