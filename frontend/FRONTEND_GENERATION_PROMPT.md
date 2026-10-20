# Master prompt: CKD Care frontend implementation

Act as a senior frontend engineer and healthcare-product UI/UX designer. Build a complete, responsive, working React frontend for the student project **Clinical Decision Support System for Chronic Kidney Disease** (also described as Agentic AI-driven CKD Progression Prediction and Clinical Decision Support using RAG).

## Reference priority

Use `DB DESIGN and FRONTEND.pdf` as the authoritative visual reference for screens 2–11. Ignore page 1 for UI design; it contains database design context. Match the screen hierarchy, information density, navigation, clinical dashboard layout, and visible controls. Do not merely place the screenshots in the app; implement the interfaces as real components. The design reference contains:

1. Login / Sign Up
2. Doctor Dashboard
3. Patient List
4. Add / Edit Patient
5. Patient Profile
6. Visit Details and Laboratory Results
7. AI Risk Assessment with Risk Prediction, SHAP Explanation, and Trend Analysis tabs
8. Clinical Assistant (RAG)
9. Reports & Analytics
10. Knowledge Base
11. Profile / Settings

Also respect the project's roadmap and architecture: React frontend, FastAPI REST backend, MySQL for structured users/patients/visits/lab results, Random Forest or other trained model for progression-risk prediction, SHAP for explainability, LangGraph for internal workflow orchestration, and ChromaDB + an LLM for clinical evidence retrieval. Internal agents are not separate chatbots for the doctor; present their meaningful outputs through the UI.

## Design system

- Use a polished, professional medical SaaS aesthetic: primarily white/light theme, navy/blue navigation and accents, restrained green/amber/red risk states, clear typography, subtle shadows, clean cards, consistent spacing, and high-contrast tables.
- The first-run/default theme must be **light/white**. Provide a visible light/dark theme switch in Profile → Theme & Appearance and optionally on the login screen. Persist the user's choice in browser local storage and restore it after refresh.
- Provide a responsive desktop/tablet/mobile layout, accessible labels, keyboard focus states, clear empty states, loading/error states, and confirmation for destructive actions.
- Use React + Vite + JavaScript. Use Recharts for trends/distributions and Lucide icons. Keep code modular, readable, and easy for a student to maintain.
- Avoid excessive animation, decorative medical claims, or a flashy glassmorphism-heavy layout. Clinical clarity is more important than visual effects.

## Screen functionality

### 1. Login / Sign Up
Login/register tab, email and password fields, password visibility toggle, remember-me checkbox, forgot-password action, clear validation/errors, and a calm CKD Care introduction. Do not claim secure real authentication unless connected to backend.

### 2. Dashboard
Summary cards for total patients, high-risk patients, follow-up due, and new patients; eGFR trend chart; risk-distribution donut; recent/high-priority patient table; quick actions and follow-up reminders. Search should lead into patient discovery.

### 3. Patient List
Search by patient name or ID, risk filter, sorting, pagination, add/edit/delete actions, view-profile action, risk badges, latest eGFR/ACR, age/gender and last-visit information.

### 4. Add/Edit Patient
Patient ID, name, age, gender, source, relevant comorbidities (hypertension, diabetes, CVD, IHD, dyslipidemia), medication flags (RAAS inhibitor, SGLT2 inhibitor, statin, GLP-1 RA), and baseline measurements (eGFR, ACR, blood pressure, BMI, creatinine, HbA1c where available). Validate required fields and numeric values. Preserve fields that map to the backend schema.

### 5. Patient Profile
Overview, visit history, lab results, trends, AI insights, and notes. Show demographics, medical history, latest metrics, dates and risk status. Let the user open visits and start an analysis.

### 6. Visit / Lab Results
Display longitudinal visits and lab results with dates, units, and contextual reference information. Add-visit form must capture date, eGFR, creatinine, ACR, blood pressure, haemoglobin and other available lab fields. Never silently invent a missing lab value.

### 7. AI Risk Assessment
Show a risk category/result returned by the actual backend, risk factors, eGFR/ACR trends, and a SHAP explanation panel with direction/importance. Distinguish model probability from risk category and show a clear disclaimer if the model is unavailable. Never hardcode a demonstration score as a real clinical prediction. Include a path to clinical evidence.

### 8. Clinical Assistant (RAG)
Provide a doctor-facing chat interface, optional selected-patient context, suggested questions, response loading/error states, and source citations with document title and section/page when returned by the backend. Use retrieved clinical passages from ChromaDB via FastAPI. If the backend is unavailable, label fallback text as demo-only; do not claim that it was retrieved from KDIGO/NICE or another source.

### 9. Reports & Analytics
Charts for eGFR trends and risk distribution, cohort summaries, filterable date period, and CSV export. Label sample data clearly. Do not present mock aggregate metrics as clinical findings.

### 10. Knowledge Base
Sections for clinical guidelines, drug information, patient education and recent searches. Show document title, description, source/version metadata and open/view actions. Add/upload/ingestion should call a real backend endpoint or be clearly marked as not connected.

### 11. Profile / Settings
Profile information, password change UI, notification preferences, and Theme & Appearance with Light/Dark selection. Save theme persistently. Password change and notification delivery must not be claimed as server-persisted until endpoints exist.

## Backend and database integration

- Centralise API requests in `src/api.js` or `src/services/api.js`; configure the API base URL with a Vite environment variable, never hardcode secrets.
- Support the intended FastAPI architecture and JWT bearer authentication when endpoints are available.
- Map data to the MySQL schema: `users`, `patients`, `visits`, `lab_results`, and `progression_labels`. Patient and visit forms should preserve IDs and measurement units. Structured patient data belongs in MySQL; clinical document embeddings belong in ChromaDB.
- Make the backend contract configurable and document any assumed routes/response fields. Do not silently assume endpoint shapes that have not been confirmed.
- Include useful error handling for API unavailable, unauthorized access, validation failure and empty results.
- Keep the app runnable as a demo without backend, but label synthetic data and mock behavior transparently.

## Safety, accuracy and project credibility

This is a student clinical decision-support prototype, not an autonomous doctor or a treatment-prescribing system. The doctor remains the final decision-maker. Do not label heuristic demo outputs as a trained Random Forest prediction, do not fabricate SHAP values, and do not state that RAG responses have citations unless source metadata actually came back from retrieval. Include a clear demo disclaimer and document the remaining integration work.

## Deliverables

Return a complete ZIP containing all source code, `package.json`, Vite configuration if needed, `.env.example`, README with setup instructions, a master prompt file, and any assets. Include commands to install dependencies, run the dev server, and create a production build. Test the production build where the environment permits; report honestly any checks blocked by unavailable dependency installation. Do not omit code files or return screenshots in place of a working interface.
