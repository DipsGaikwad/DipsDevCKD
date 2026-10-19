from pathlib import Path
import pandas
import mysql.connector
import getpass

# ============================================================
# 1. PROJECT PATH
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASELINE_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "thai"
    / "baseline and lab data.csv"
)

print("PROJECT_ROOT:", PROJECT_ROOT)
print("BASELINE_FILE:", BASELINE_FILE)

# ============================================================
# 2. READ BASELINE CSV
# ============================================================
df_baseline = pandas.read_csv(BASELINE_FILE)
print("\nBaseline DataFrame:", df_baseline.shape)

# ============================================================
# 3. BASIC SOURCE VALIDATION
# ============================================================
print("\nUnique source patients:", df_baseline["id"].nunique())
print("Duplicate source IDs:", df_baseline["id"].duplicated().sum())

# ============================================================
# 4. CREATE OUR INTERNAL PATIENT ID
# ============================================================
df_baseline["patient_id"] = (
    "CKD-TH-"
    + df_baseline["id"].astype(int).astype(str).str.zfill(6)
)

# ============================================================
# 5. ADD SOURCE INFORMATION
# ============================================================
df_baseline["source_code"] = "TH"

df_baseline["source_patient_id"] = (
    df_baseline["id"].astype(int).astype(str)
)

# ============================================================
# 6. RENAME SOURCE COLUMNS TO OUR DATABASE NAMES
# ============================================================
df_patients = df_baseline.rename(columns={
    "age": "age_at_baseline",
    "ht": "hypertension",
    "dm": "diabetes",
    "dyslipid": "dyslipidemia",
    "sbp": "baseline_sbp",
    "dbp": "baseline_dbp",
    "bmi": "baseline_bmi",
    "egfr": "baseline_egfr",
    "hb": "baseline_hb",
    "chol": "baseline_chol",
    "tg": "baseline_tg",
    "ldl": "baseline_ldl",
    "hdl": "baseline_hdl",
    "albuminuria": "baseline_albuminuria"
})

# ============================================================
# 7. KEEP ONLY PATIENT TABLE COLUMNS
# ============================================================
patient_columns = [
    "patient_id",
    "source_code",
    "source_patient_id",
    "age_at_baseline",
    "gender",
    "ihd",
    "cvd",
    "hypertension",
    "diabetes",
    "dyslipidemia",
    "baseline_sbp",
    "baseline_dbp",
    "baseline_bmi",
    "baseline_egfr",
    "baseline_hb",
    "baseline_chol",
    "baseline_tg",
    "baseline_ldl",
    "baseline_hdl",
    "baseline_albuminuria",
    "raasi",
    "glp1ra",
    "sglt2i",
    "statin"
]

df_patients = df_patients[patient_columns]

# ============================================================
# 8. CONVERT PANDAS NaN TO PYTHON None
# ============================================================
df_patients = df_patients.astype(object).where(
    pandas.notnull(df_patients),
    None
)
# ============================================================
# 9. DISPLAY TRANSFORMED DATA
# ============================================================
print("\n--- TRANSFORMED PATIENT DATA (first 5 rows) ---")
print(df_patients.head())

print("\n--- TRANSFORMED COLUMNS ---")
print(df_patients.columns.tolist())

print("\n--- SHAPE ---")
print(df_patients.shape)

print("\n--- MISSING VALUES AFTER TRANSFORM ---")
print(df_patients.isnull().sum())


#now last step connection to mysql
mysql_password=getpass.getpass("Enter the mysql password: ")

connection=mysql.connector.connect(
    host="localhost",
    user='root',
    password=mysql_password,
    database="ckd_project"
)

cursor=connection.cursor()
print("MySQL connection successful")

# ============================================================
# 11. INSERT PATIENTS
# ============================================================
insert_sql = """
INSERT INTO patients (
    patient_id, source_code, source_patient_id,
    age_at_baseline, gender, ihd, cvd,
    hypertension, diabetes, dyslipidemia,
    baseline_sbp, baseline_dbp, baseline_bmi,
    baseline_egfr, baseline_hb, baseline_chol,
    baseline_tg, baseline_ldl, baseline_hdl,
    baseline_albuminuria, raasi, glp1ra,
    sglt2i, statin
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s
)
"""

patient_rows = list(
    df_patients.itertuples(index=False, name=None)
)

print("\nNumber of patients ready for insertion:", len(patient_rows))

# ============================================================
# 12. EXECUTE INSERT
# ============================================================
try:
    for row in patient_rows:
        cursor.execute(insert_sql, row)
    connection.commit()
    print("\nPatient insertion successful.")
    print("Rows inserted:", len(patient_rows))

except Exception as error:
    connection.rollback()
    print("\nERROR while inserting patients:")
    print(error)
    print("Transaction rolled back.")

finally:
    cursor.close()
    connection.close()
    print("\nMySQL connection closed.")
print(df_patients.columns.tolist())


