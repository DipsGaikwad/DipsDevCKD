#creation of porgression_laels for the ML model preparation
#this file reads the original egfr_rate and stores it in the published_egfr_rate
#pulls the first and last egfr rate from the database and calculate the slope
#assigns rapid_progression=1 if egfr<=-0.5 ,else rapid_proression=0


from pathlib import Path
import pandas as pd
import getpass
import mysql.connector


#Project Files path setting
PROJECT_ROOT=Path(__file__).resolve().parent.parent.parent
BASELINE_FILE=PROJECT_ROOT/"data"/"raw"/"thai"/"baseline and lab data.csv"

#MYSQL Connection
print("Connecting to mysql...")
mysql_password=getpass.getpass("Enter the mysql Password: ")

connection=mysql.connector.connect(
    host="localhost",
    user="root",
    password=mysql_password,
    database="ckd_project",
    use_pure=True
)

cursor=connection.cursor(dictionary=True)
print("Mysql Connection Successful")

#loading egfr_rate from 'baseline and lab data '

print("Reading CSV file... ")
df_baseline=pd.read_csv(BASELINE_FILE)
#create a empty dictionary :source_id (str) -> egfrrate
#fill NaN with None So that Mysql Will get it As NULL
published_rates={
    str(int(row.id)): (float(row.egfrrate) if pd.notnull(row.egfrrate) else None)
    for row in df_baseline.itertuples()
}

#load patient data and visits from MYSQL
print("Fetching patient lab trajectories...")
#join visits and lab_results table so we can gate egfr at every visit

query = """
Select v.patient_id,v.day_from_baseline,l.egfr_ml_min_1_73m2
from visits v join lab_results l ON v.visit_id=l.visit_id
WHERE l.egfr_ml_min_1_73m2 IS NOT NULL
ORDER BY v.patient_id,v.day_from_baseline ASC
"""
cursor.execute(query)
labs = cursor.fetchall()


#Group By patient id
patient_trajectories={}
for row in labs:
    pid=row["patient_id"]
    if pid not in patient_trajectories:
        patient_trajectories[pid]=[]
    patient_trajectories[pid].append({
        "day":float(row["day_from_baseline"]),
        "egfr":float(row["egfr_ml_min_1_73m2"])
    })
    
    
#calculate slopes and labels
print("Calculating slopes and progression labels...")
labels_to_insert=[]
# Get source_patient_id map to link our patient_id to the CSV's id
cursor.execute("SELECT patient_id, source_patient_id FROM patients")
source_map = {row["patient_id"]: str(row["source_patient_id"]) for row in cursor.fetchall()}
rapid_count = 0
stable_count = 0
skipped_count = 0
for patient_id,visits in patient_trajectories.items():
    #Rule --At least 2 visits Required
    if len(visits)<2:
        skipped_count+=1
        continue
    first_visits=visits[0]
    last_visits=visits[-1]
    # Calculate time in years between first and last visit
    days_diff=last_visits["day"]-first_visits["day"]
    years_diff=days_diff/365.25
    # Safety check to avoid division by zero
    if years_diff <= 0.1: 
        skipped_count += 1
        continue
    
    # Calculate slope: (Last eGFR - First eGFR) / Years
    egfr_slope=(last_visits["egfr"]-first_visits["egfr"])/years_diff
    egfr_slope=round(egfr_slope,2)
    
     # Apply the Rule: Rapid progression if slope <= -5.0
    is_rapid = 1 if egfr_slope <= -5.0 else 0
    
    if is_rapid:
        rapid_count += 1
    else:
        stable_count += 1
    # Get the published rate from the original CSV
    source_id=source_map.get(patient_id)
    published_rate= published_rates.get(source_id)
    labels_to_insert.append((
        patient_id,
        published_rate,
        egfr_slope,
        is_rapid,
        'KDIGO_slope_leq_-5'  # <--- ADD THIS LINE
    ))
print(f"Calculated labels for {len(labels_to_insert)} patients.")
print(f"Rapid Progressors: {rapid_count}")
print(f"Stable/Slow: {stable_count}")
print(f"Skipped (insufficient data): {skipped_count}")

# ============================================================
# 6. INSERT INTO MYSQL
# ============================================================
insert_label_sql = """
INSERT INTO progression_labels (patient_id, published_egfr_rate, egfr_slope_ours, rapid_progression,target_defination)
VALUES (%s, %s, %s, %s,%s)
"""

print("\nInserting labels into database...")
try:
    cursor.executemany(insert_label_sql, labels_to_insert)
    connection.commit()
    print("Progression labels inserted successfully!")
except Exception as e:
    connection.rollback()
    print(f"Error inserting labels: {e}")
    
# ============================================================
# 7. CLEANUP
# ============================================================
cursor.close()
connection.close()
print("\nETL Checkpoint 3 Complete.")