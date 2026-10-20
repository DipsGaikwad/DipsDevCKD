from pathlib import Path
import getpass
import pandas
import numpy as np
from sklearn.linear_model import LinearRegression
import mysql.connector

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE_FILE = PROJECT_ROOT / "data" / "raw" / "baseline and lab data.csv"

print("Connecting to MySQL...")
mysql_password = getpass.getpass("Enter MySQL password: ")
connection = mysql.connector.connect(host="localhost", user="root", password=mysql_password, database="ckd_project", use_pure=True)
cursor = connection.cursor(dictionary=True)

print("Fetching patient trajectories...")
query = """
SELECT v.patient_id, v.day_from_baseline, l.egfr_ml_min_1_73m2
FROM visits v
JOIN lab_results l ON v.visit_id = l.visit_id
WHERE l.egfr_ml_min_1_73m2 IS NOT NULL
ORDER BY v.patient_id, v.day_from_baseline ASC
"""
cursor.execute(query)
labs = cursor.fetchall()

patient_trajectories = {}
for row in labs:
    pid = row["patient_id"]
    if pid not in patient_trajectories:
        patient_trajectories[pid] = []
    patient_trajectories[pid].append({"day": float(row["day_from_baseline"]), "egfr": float(row["egfr_ml_min_1_73m2"])})

def calculate_slope(visits):
    if len(visits) < 2: return None
    days = np.array([v["day"] for v in visits]).reshape(-1, 1)
    egfrs = np.array([v["egfr"] for v in visits])
    if np.max(days) == np.min(days): return None
    model = LinearRegression().fit(days, egfrs)
    return float(model.coef_[0] * 365.25)

print("Calculating landmark labels (History = 365 days, Future = after 365 days)...")
labels_to_insert = []
LANDMARK_DAY = 365.0

for patient_id, visits in patient_trajectories.items():
    history_visits = [v for v in visits if v["day"] <= LANDMARK_DAY]
    future_visits = [v for v in visits if v["day"] > LANDMARK_DAY]
    
    if len(history_visits) >= 2 and len(future_visits) >= 2:
        history_slope = calculate_slope(history_visits)
        future_slope = calculate_slope(future_visits)
        
        if history_slope is not None and future_slope is not None:
            is_rapid = 1 if future_slope <= -5.0 else 0
            labels_to_insert.append((
                patient_id,
                None, # published_egfr_rate
                round(history_slope, 2),
                is_rapid,
                'KDIGO_landmark_365_slope'
            ))

print(f"Valid labels generated: {len(labels_to_insert)}")
cursor.execute("DELETE FROM progression_labels") # Clear old labels
cursor.executemany("""
    INSERT INTO progression_labels (patient_id, published_egfr_rate, egfr_slope_ours, rapid_progression, target_defination)
    VALUES (%s, %s, %s, %s, %s)
""", labels_to_insert)
connection.commit()
print("Labels updated successfully.")
cursor.close()
connection.close()