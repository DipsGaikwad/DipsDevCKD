# CKD Care API

## Start
Run from the repository root so `backend` imports resolve. Create and activate a Python virtual environment, then `python -m pip install -r backend/requirements.txt`. Copy root `.env.example` to root `.env` and fill in your database password and JWT secret. Do not share or commit `.env`.

Check MySQL first: `python -m backend.test_db_connection`. Then create the first administrator by running `python -m backend.bootstrap_admin`, and start the API with `python -m uvicorn backend.app:app --reload --port 8000`. Open `http://127.0.0.1:8000/docs`.

## Important limitations
- The API is designed to use your existing MySQL `ckd_project` tables; it never calls `create_all()` to mutate the database automatically.
- Before use, apply the supplied SQL migration (after taking a backup). It adds `patients.full_name` and metadata/settings/notification support tables.
- Auth checks approval status and role on each protected request. Initial Admin is created from terminal, not public signup.
- The existing project has no doctor-to-patient assignments, so approved staff currently share the single student-project workspace. Add assignments before separating users/clinics.
- The current repository does not commit `models/trained/ckd_model.joblib`. Prediction returns a clear 503 until the model file and feature schema are installed/validated.
- Knowledge uploads store files and metadata only. Indexing, embeddings and RAG are deliberately not implemented yet.
- No real MySQL server is available from the package-building environment. Run the provided connection and endpoint tests locally with your own `.env`.
