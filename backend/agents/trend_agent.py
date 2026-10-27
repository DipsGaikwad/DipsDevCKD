import pandas
import numpy as np
from sklearn.linear_model import LinearRegression

def analyze_trends(visits: list) -> dict:
    if not visits or len(visits) < 2:
        return {"egfr_slope": 0.0, "egfr_trend": "unknown"}

    df = pandas.DataFrame(visits)
    df['visit_date'] = pandas.to_datetime(df['visit_date'], errors='coerce')
    df = df.dropna(subset=['visit_date', 'egfr_ml_min_1_73m2']).sort_values('visit_date')

    if len(df) < 2:
        return {"egfr_slope": 0.0, "egfr_trend": "unknown"}

    days = (df['visit_date'] - df['visit_date'].iloc[0]).dt.days.values.reshape(-1, 1)
    if np.max(days) == 0:
        return {"egfr_slope": 0.0, "egfr_trend": "unknown"}

    model = LinearRegression().fit(days, df['egfr_ml_min_1_73m2'].values)
    slope_per_year = model.coef_[0] * 365.25

    trend = "rapid decline" if slope_per_year <= -5.0 else "slow decline" if slope_per_year < 0 else "stable"
    return {"egfr_slope": round(float(slope_per_year), 2), "egfr_trend": trend}