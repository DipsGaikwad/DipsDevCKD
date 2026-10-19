from pathlib import Path
import getpass
from datetime import datetime, timedelta
import pandas
import mysql.connector

# ============================================================
# 1. PROJECT PATHS
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
    database="ckd_project"
)
cursor = connection.cursor(dictionary=True)
print("MySQL connection successful.")

# ============================================================
# 3. LOAD PATIENT DATA
# ============================================================
print("\nLoading baseline demographics from MySQL...")
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
# 4. LOAD LONGITUDINAL DATA
# ============================================================
print(f"Loading longitudinal data from: {LONGITUDINAL_FILE}")
df_long = pandas.read_csv(LONGITUDINAL_FILE)
df_long.rename(columns={"cr": "creatinine"}, inplace=True)

# Drop rows where id or day is missing to prevent errors
df_long = df_long.dropna(subset=['id', 'day'])
print(f"Longitudinal rows loaded: {len(df_long)}")

# ============================================================
# 5. CALCULATE EGFR AND VISIT DATES
# ============================================================
print("Calculating eGFR (CKD-EPI 2021) and Visit Dates...")

baseline_date = datetime(2020, 1, 1)

def calculate_egfr(age, gender, creatinine):
    is_female = (gender == 2)
    kappa = 0.7 if is_female else 0.9
    alpha = -0.241 if is_female else -0.302
    scr_k = creatinine / kappa
    egfr = 142 * (min(scr_k, 1) ** alpha) * (max(scr_k, 1) ** -1.200) * (0.9938 ** age)
    if is_female:
        egfr *= 1.012
    return round(egfr, 2)

visits_to_insert = []
visit_counter = {} 

for row in df_long.itertuples():
    source_id = str(int(row.id))
    
    if source_id not in patient_lookup:
        continue 
        
    patient_info = patient_lookup[source_id]
    visit_date = baseline_date + timedelta(days=int(row.day))
    
    # Safely increment visit counter
    visit_counter[source_id] = visit_counter.get(source_id, 0) + 1
        
    # NOTE: We do NOT do visits_to_insert = visits_to_insert.append(...)
    # We simply call the .append() method.
    visits_to_insert.append((
        patient_info["patient_id"],
        visit_counter[source_id],        
        int(row.day),                    
        visit_date.strftime('%Y-%m-%d'),
        'outpatient'                    
    ))

# ============================================================
# 6. INSERT VISITS
# ============================================================
insert_visit_sql = """
INSERT INTO visits (patient_id, visit_number, day_from_baseline, visit_date, encounter_type)
VALUES (%s, %s, %s, %s, %s)
"""

print(f"Inserting {len(visits_to_insert)} visits...")
try:
    batch_size = 10000
    for i in range(0, len(visits_to_insert), batch_size):
        batch = visits_to_insert[i:i+batch_size]
        cursor.executemany(insert_visit_sql, batch)
        connection.commit()
    print("Visits inserted successfully.")
except Exception as e:
    connection.rollback()
    print(f"Error inserting visits: {e}")
    exit()

# ============================================================
# 7. FETCH VISIT IDs
# ============================================================
print("Fetching generated visit_ids...")
cursor.execute("SELECT visit_id, patient_id, visit_date FROM visits")
all_visits = cursor.fetchall()

visit_map = {
    (v["patient_id"], v["visit_date"].strftime('%Y-%m-%d')): v["visit_id"] 
    for v in all_visits
}

# ============================================================
# 8. PREPARE AND INSERT LAB RESULTS
# ============================================================
print("Preparing lab results (Creatinine + Computed eGFR)...")
labs_to_insert = []

for row in df_long.itertuples():
    source_id = str(int(row.id))
    if source_id not in patient_lookup:
        continue
        
    patient_info = patient_lookup[source_id]
    age_at_visit = patient_info["age"] + (row.day / 365.25)
    egfr_value = calculate_egfr(age_at_visit, patient_info["gender"], row.creatinine)
    
    visit_date_str = (baseline_date + timedelta(days=int(row.day))).strftime('%Y-%m-%d')
    visit_id = visit_map.get((patient_info["patient_id"], visit_date_str))
    
    if visit_id:
        labs_to_insert.append((visit_id, 'creatinine', float(row.creatinine), 'mg/dL'))
        labs_to_insert.append((visit_id, 'egfr', egfr_value, 'mL/min/1.73m2'))

insert_lab_sql = """
INSERT INTO lab_results (visit_id, lab_code, value, unit)
VALUES (%s, %s, %s, %s)
"""

print(f"Inserting {len(labs_to_insert)} lab result rows...")
try:
    batch_size = 10000
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
print("\nETL Checkpoint 2 Complete.")

