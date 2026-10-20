
from pathlib import Path
import shutil
from datetime import datetime
import sys

# Put this script at <repo-root>/scripts/apply_ckd_quickfix.py.
ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "frontend" / "src" / "App.jsx"
MODELS = ROOT / "backend" / "models.py"
ETL = ROOT / "scripts" / "etl" / "import_thai_dataset.py"

def backup(path):
    dst = path.with_suffix(path.suffix + ".backup-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(path, dst)
    print("Backup created:", dst.relative_to(ROOT))

def main():
    if not APP.exists() or not MODELS.exists():
        print("ERROR: place this script in <repo-root>/scripts/apply_ckd_quickfix.py.")
        sys.exit(2)

    # Uploaded DB schema has progression_labels.target_defination (not target_definition).
    model_text = MODELS.read_text(encoding="utf-8")
    old = 'target_definition: Mapped[str]=mapped_column(String(255),nullable=False)'
    new = 'target_definition: Mapped[str]=mapped_column("target_defination", String(255), nullable=False)'
    if old in model_text:
        backup(MODELS)
        MODELS.write_text(model_text.replace(old, new, 1), encoding="utf-8")
        print("Patched models.py for the target_defination MySQL column.")
    elif '"target_defination"' in model_text or "'target_defination'" in model_text:
        print("models.py is already mapped to target_defination.")
    else:
        print("WARNING: could not match the expected target-definition line; left models.py unchanged.")

    # Help labels in the large React file are patched automatically; no manual App.jsx editing.
    app_text = APP.read_text(encoding="utf-8")
    old_form = '''<label>Patient ID *<input value={patientForm.patient_id||''} onChange={e=>setPatientForm({...patientForm,patient_id:e.target.value})} required disabled={!!patientForm.editing}/></label><label>Full name *<input value={patientForm.full_name||''} onChange={e=>setPatientForm({...patientForm,full_name:e.target.value})} required/></label><label>Source code<input value={patientForm.source_code||'HOSP'} onChange={e=>setPatientForm({...patientForm,source_code:e.target.value.toUpperCase()})} required maxLength={10} placeholder="HOSP / TH / NHANES"/><small>HOSP = hospital-entered; TH = Thai cohort.</small></label><label>Source patient ID *<input value={patientForm.source_patient_id||''} onChange={e=>setPatientForm({...patientForm,source_patient_id:e.target.value})} required maxLength={100} placeholder="Hospital record number or original dataset ID"/><small>For imported research data, preserve the original source ID. For newly entered data, use a hospital reference.</small></label>'''
    new_form = '''<label>Patient ID (internal ID) *<input value={patientForm.patient_id||''} onChange={e=>setPatientForm({...patientForm,patient_id:e.target.value})} placeholder="Example: CKD-HOSP-000001" required disabled={!!patientForm.editing}/><small>Unique internal ID. Thai research records use CKD-TH-000001. New hospital records can use CKD-HOSP-000001.</small></label><label>Patient display name *<input value={patientForm.full_name||''} onChange={e=>setPatientForm({...patientForm,full_name:e.target.value})} required placeholder="Example: Synthetic Demo Patient 001"/></label><label>Source code<input value={patientForm.source_code||'HOSP'} onChange={e=>setPatientForm({...patientForm,source_code:e.target.value.toUpperCase()})} required maxLength={10} placeholder="HOSP / TH / DEMO"/><small>HOSP = manually entered; TH = Thai cohort; DEMO = synthetic records.</small></label><label>Source record ID *<input value={patientForm.source_patient_id||''} onChange={e=>setPatientForm({...patientForm,source_patient_id:e.target.value})} required maxLength={100} placeholder="Hospital record number or original dataset ID"/><small>Preserve the original ID for imported research rows. Use a hospital reference for a new record.</small></label>'''
    if old_form in app_text:
        backup(APP)
        APP.write_text(app_text.replace(old_form, new_form, 1), encoding="utf-8")
        print("Patched App.jsx Add Patient helper labels.")
    else:
        print("WARNING: latest App.jsx form markup did not match; no App.jsx change made.")

    # Thai source records are de-identified: create a display label, not a real patient name.
    if ETL.exists():
        etl_text = ETL.read_text(encoding="utf-8")
        if 'df_baseline["full_name"]' in etl_text:
            print("Thai ETL already generates full_name labels.")
        else:
            m1 = 'df_baseline["source_code"] = "TH"'
            m2 = '    "patient_id",\n    "source_code",'
            m3 = 'INSERT INTO patients (\n    patient_id, source_code, source_patient_id,'
            old_ph = '''    %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s'''
            new_ph = '''    %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s'''
            if m1 in etl_text and m2 in etl_text and m3 in etl_text and old_ph in etl_text:
                etl_text = etl_text.replace(
                    m1,
                    m1 + '\n\n# De-identified cohort label; not a real name.\ndf_baseline["full_name"] = "Thai Cohort Patient " + df_baseline["id"].astype(int).astype(str).str.zfill(6)',
                    1,
                )
                etl_text = etl_text.replace(m2, '    "patient_id",\n    "full_name",\n    "source_code",', 1)
                etl_text = etl_text.replace(m3, 'INSERT INTO patients (\n    patient_id, full_name, source_code, source_patient_id,', 1)
                etl_text = etl_text.replace(old_ph, new_ph, 1)
                backup(ETL)
                ETL.write_text(etl_text, encoding="utf-8")
                print("Patched Thai ETL import to write display labels.")
            else:
                print("WARNING: Thai ETL source did not match expected layout; no change made.")
    else:
        print("Thai ETL importer wasn't found; skipped.")

    print("Finished. Restart FastAPI and Vite. Timestamped backups are next to original files.")

if __name__ == "__main__":
    main()
