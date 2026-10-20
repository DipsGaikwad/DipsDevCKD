from pathlib import Path
import getpass
import pandas
import mysql.connector

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "ml_dataset.csv"
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

print("Connecting to MySQL...")
mysql_password = getpass.getpass("Enter MySQL password: ")
connection = mysql.connector.connect(host="localhost", user="root", password=mysql_password, database="ckd_project", use_pure=True)
cursor = connection.cursor(dictionary=True)

query = """
SELECT 
    p.patient_id, 
    p.age_at_baseline, 
    p.gender, 
    p.ihd, 
    p.cvd, 
    p.hypertension, 
    p.diabetes, 
    p.dyslipidemia, 
    p.baseline_sbp, 
    p.baseline_dbp, 
    p.baseline_bmi, 
    p.baseline_egfr, 
    p.baseline_hb, 
    p.baseline_chol, 
    p.baseline_tg, 
    p.baseline_ldl, 
    p.baseline_hdl, 
    p.baseline_albuminuria, 
    p.raasi, 
    p.glp1ra, 
    p.sglt2i, 
    p.statin,
    l.egfr_slope_ours, 
    l.rapid_progression
FROM 
    patients p
JOIN 
    progression_labels l ON p.patient_id = l.patient_id
"""
cursor.execute(query)
df = pandas.DataFrame(cursor.fetchall())

# We keep patient_id for GroupShuffleSplit in train_model.py
# We KEEP egfr_slope_ours because it is now a historical feature (Days 0-365)
df.to_csv(OUTPUT_FILE, index=False)
print(f"ML Dataset saved to {OUTPUT_FILE}. Rows: {len(df)}")

cursor.close()
connection.close()