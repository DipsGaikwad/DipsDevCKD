from pathlib import Path
import getpass
from datetime import datetime, timedelta
import pandas
import mysql.connector

# ============================================================
# 1. PROJECT PATHS & CONFIG
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LONGITUDINAL_FILE = (
    PROJECT_ROOT / "data" / "raw" / "thai" / "longitudinal_creatinine.csv" 
)

# ============================================================
# 2. MYSQL CONNECTION
# ============================================================
print("Connecting to MySQL...")
mysql_password = getpass.getpass("Enter MySQL password: ")

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password=mysql_password,
    database="ckd_project",
    use_pure=True  # Added to prevent Python 3.14 crashes
)
cursor = connection.cursor(dictionary=True)
print("MySQL connection successful.")

# ============================================================
# 3. LOAD PATIENTS (For Age, Gender, and patient_id)
# ============================================================
print("\nLoading patients from database...")
cursor.execute("SELECT patient_id, source_patient_id, age_at_baseline, gender FROM patients")
patients = cursor.fetchall()

patient_lookup = {
    str(p["source_patient_id"]): {
        "patient_id": p["patient_id"],
        "age": float(p["age_at_baseline"]) if p["age_at_baseline"] else 0.0,
        "gender": int(p["gender"])
    } for p in patients
}

# ============================================================
# 4. LOAD VISITS (To map day_from_baseline -> visit_id)
# ============================================================
print("Loading visits from database...")
cursor.execute("SELECT visit_id, patient_id, day_from_baseline FROM visits")
visits = cursor.fetchall()

# We create a map: (patient_id, day_from_baseline) -> visit_id
# This is much safer than matching by date strings
visit_map = {
    (v["patient_id"], int(v["day_from_baseline"])): v["visit_id"] 
    for v in visits
}

# ============================================================
# 5. LOAD LONGITUDINAL DATA
# ============================================================
print(f"Loading longitudinal data from: {LONGITUDINAL_FILE}")
df_long = pandas.read_csv(LONGITUDINAL_FILE)
df_long.rename(columns={"cr": "creatinine"}, inplace=True)
df_long = df_long.dropna(subset=['id', 'day'])
print(f"Longitudinal rows loaded: {len(df_long)}")

# ============================================================
# 6. EGFR CALCULATION FUNCTION (Copied Here)
# ============================================================
def calculate_egfr(age, gender, creatinine):
    is_female = (gender == 2)
    kappa = 0.7 if is_female else 0.9
    alpha = -0.241 if is_female else -0.302
    scr_k = creatinine / kappa
    egfr = 142 * (min(scr_k, 1) ** alpha) * (max(scr_k, 1) ** -1.200) * (0.9938 ** age)
    if is_female:
        egfr *= 1.012
    return round(egfr, 2)

# ============================================================
# 7. PREPARE LAB RESULTS
# ============================================================
print("Preparing lab results...")
labs_to_insert = []

for row in df_long.itertuples():
    source_id = str(int(row.id))
    
    if source_id not in patient_lookup:
        continue
        
    patient_info = patient_lookup[source_id]
    
    # Calculate eGFR
    age_at_visit = patient_info["age"] + (row.day / 365.25)
    egfr_value = calculate_egfr(age_at_visit, patient_info["gender"], row.creatinine)
    
    # Fetch the visit_id using the lookup map
    visit_id = visit_map.get((patient_info["patient_id"], int(row.day)))
    
    if visit_id:
        labs_to_insert.append((
            visit_id,
            float(row.creatinine),
            egfr_value,
            'thai_dataset'
        ))

# ============================================================
# 8. INSERT LAB RESULTS
# ============================================================
insert_lab_sql = """
INSERT INTO lab_results (visit_id, creatinine_mg_dl, egfr_ml_min_1_73m2, data_source)
VALUES (%s, %s, %s, %s)
"""

print(f"Inserting {len(labs_to_insert)} lab result rows...")
try:
    # Ping the server to ensure connection is alive
    connection.ping(reconnect=True, attempts=3, delay=2)
    
    batch_size = 5000  # Safe batch size
    for i in range(0, len(labs_to_insert), batch_size):
        batch = labs_to_insert[i:i+batch_size]
        cursor.executemany(insert_lab_sql, batch)
        connection.commit()
        print(f"Inserted {i + len(batch)} rows...")
        
    print("All lab results inserted successfully.")
except Exception as e:
    connection.rollback()
    print(f"Error inserting lab results: {e}")

# ============================================================
# 9. CLEANUP
# ============================================================
cursor.close()
connection.close()
print("\nETL Lab Results Complete.")