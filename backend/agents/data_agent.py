import pandas
import numpy as np

def validate_patient_data(visits: list) -> dict:
    issues = []
    if not visits:
        return {"status": "INVALID", "issues": ["No visit records provided."]}

    try:
        df = pandas.DataFrame(visits)
    except Exception as e:
        return {"status": "INVALID", "issues": [f"Data conversion error: {str(e)}"]}

    required_cols = ['visit_date', 'egfr_ml_min_1_73m2']
    for col in required_cols:
        if col not in df.columns:
            return {"status": "INVALID", "issues": [f"Missing required column: {col}"]}

    # eGFR checks
    if df['egfr_ml_min_1_73m2'].isnull().any():
        issues.append("Missing eGFR values detected.")
    elif not np.issubdtype(df['egfr_ml_min_1_73m2'].dtype, np.number):
        return {"status": "INVALID", "issues": ["eGFR contains non-numeric values."]}
    else:
        if (df['egfr_ml_min_1_73m2'] < 0).any() or (df['egfr_ml_min_1_73m2'] > 200).any():
            issues.append("Impossible eGFR value detected.")

    # Date checks
    try:
        df['visit_date'] = pandas.to_datetime(df['visit_date'], errors='raise')
        if not df['visit_date'].is_monotonic_increasing:
            issues.append("Dates are not chronological.")
        if df['visit_date'].duplicated().any():
            issues.append("Duplicate visit dates detected.")
    except Exception:
        return {"status": "INVALID", "issues": ["Invalid or unparseable visit dates."]}

    if len(issues) == 0:
        status = "VALID"
    elif any("Impossible" in i or "Invalid" in i or "Missing required" in i for i in issues):
        status = "INVALID"
    else:
        status = "PARTIAL"

    return {"status": status, "issues": issues}