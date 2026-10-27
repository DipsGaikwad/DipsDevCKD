import joblib
import pandas
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_FILE = PROJECT_ROOT / "models" / "trained" / "ckd_model.joblib"

if not MODEL_FILE.exists():
    raise FileNotFoundError(f"Model not found at {MODEL_FILE}")

pipeline = joblib.load(MODEL_FILE)
expected_features = pipeline.feature_names_in_

def predict_progression(baseline_data: dict, trend_data: dict) -> dict:
    df = pandas.DataFrame([baseline_data])
    df['egfr_slope_ours'] = trend_data.get('egfr_slope', 0.0)
    df = df.reindex(columns=expected_features)
    
    try:
        prob = pipeline.predict_proba(df)[0][1]
    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}
        
    # Using a dynamically tuned threshold of 0.45 instead of 0.7 based on training
    risk = "HIGH" if prob > 0.45 else "MEDIUM" if prob > 0.25 else "LOW"
    return {"probability": round(float(prob), 4), "risk_level": risk, "features_df": df}