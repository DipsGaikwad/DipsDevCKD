import requests
import json

url = "http://127.0.0.1:8000/predict"

payload = {
    "baseline_data": {
        "age_at_baseline": 58.0, "gender": 1, "ihd": 0, "cvd": 0, "hypertension": 1,
        "diabetes": 1, "dyslipidemia": 1, "baseline_sbp": 145.0, "baseline_dbp": 90.0,
        "baseline_bmi": 28.5, "baseline_egfr": 55.0, "baseline_hb": 13.5, "baseline_chol": 210.0,
        "baseline_tg": 150.0, "baseline_ldl": 130.0, "baseline_hdl": 40.0,
        "baseline_albuminuria": 150.0, "raasi": 1, "glp1ra": 0, "sglt2i": 1, "statin": 1
    },
    "visits": [
        {"visit_date": "2022-01-01", "egfr_ml_min_1_73m2": 58.0, "creatinine_mg_dl": 1.3},
        {"visit_date": "2022-07-01", "egfr_ml_min_1_73m2": 54.0, "creatinine_mg_dl": 1.4},
        {"visit_date": "2023-01-01", "egfr_ml_min_1_73m2": 48.0, "creatinine_mg_dl": 1.6}
    ]
}

print("Sending POST request to API...")
response = requests.post(url, json=payload)

print(f"HTTP Status: {response.status_code}")
print("Response Body:")
print(json.dumps(response.json(), indent=4))