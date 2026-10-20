CKD CARE REPLACEMENT BUNDLE — SETUP (WINDOWS, SIMPLE STEPS)

WHAT IS IN THIS DOWNLOAD
- frontend.zip: React UI, database-backed screens, profile, notifications, reports and Knowledge Base upload.
- backend.zip: FastAPI endpoints, MySQL models, JWT login, approval workflow, reports PDF generation and upload handling.
- CKD_MySQL_Migration.sql: a migration to add support columns/tables. It does not create or replace your five original clinical tables.

IMPORTANT BEFORE REPLACING FILES
1. Make a copy of your existing project folder first.
2. Extract frontend.zip into your project and replace the frontend folder.
3. Extract backend.zip into your project and replace the backend folder. Preserve your existing `models/trained/ckd_model.joblib` if you have it locally; the ZIP does not contain the trained model.
4. Root `.env` belongs beside the `backend` and `frontend` folders. This download includes `root.env.example`, not a secret-filled `.env`. Keep the `.env` you created and check it has DATABASE_URL, JWT_SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, FRONTEND_ORIGINS. Never upload .env to GitHub.
5. Back up database `ckd_project` before running CKD_MySQL_Migration.sql.

MYSQL CHANGES REQUIRED
- Add `patients.full_name`: your current patients table has source identifiers, but no human-readable patient name. The UI lets staff create a patient with a name, so the column is needed.
- Add `user_profile_settings`, `notifications`, and `knowledge_resources`: MySQL currently has no place to save those functions' data. The uploaded document itself stays in the configured local resource folder; MySQL stores its metadata.
- Do not run another ALTER to the `users` table if you have already followed the earlier instruction and added full_name, account_status, approved_by, approved_at and role enum ADMIN/DOCTOR/DEO. Verify first with DESCRIBE users. If those fields are missing, stop and ask before running another migration.

START BACKEND
Open PowerShell in your project root (the folder containing backend and frontend):
  python -m venv .venv.\.venv\Scripts\Activate.ps1
  python -m pip install -r backend\requirements.txt
  python -m backend.test_db_connection
  python -m backend.bootstrap_admin
  python -m uvicorn backend.app:app --reload --port 8000

The bootstrap command asks you to create the first Admin username, name, email and password. It does not print or save the plain-text password. Use that account to sign in and approve future Doctor/DEO accounts. If your existing users table already has a legitimate approved Admin, do NOT run bootstrap_admin a second time with the same account; it will refuse the duplicate.

START FRONTEND (NEW POWERSHELL WINDOW)
  cd frontend
  Copy-Item .env.example .env
  npm install
  npm run dev
Open http://localhost:5173. API docs: http://127.0.0.1:8000/docs

DO NOT use production patient-care data yet. This is a college project prototype. Passwords are hashed and API permissions are enforced, but the system still needs formal security, privacy, audit and clinical validation. Existing schema does not link patients to assigned doctors, so all approved staff currently share the development workspace.
