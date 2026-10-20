# CKD Care — React Frontend

A responsive React + Vite frontend prototype based on the submitted **DB DESIGN and FRONTEND.pdf** screens 2–11. The default theme is light/white for clinical readability; users can switch to dark mode from Profile → Theme & Appearance or the login screen. Theme preference persists in `localStorage`.

## Included screens
1. Login / Sign Up
2. Doctor Dashboard
3. Patient List
4. Add / Edit Patient
5. Patient Profile
6. Visits and Laboratory Results
7. AI Risk Assessment / SHAP explanation placeholder
8. Clinical Assistant (RAG interface)
9. Reports & Analytics
10. Knowledge Base
11. Profile and Settings

## Run locally
Requirements: Node.js 20+ recommended.

```bash
npm install
npm run dev
```

Open the local URL printed by Vite (usually `http://localhost:5173`). To verify a production bundle:

```bash
npm run build
npm run preview
```

## Backend integration
By default, this app runs in **demo mode** using clearly labelled sample data. It does not pretend to return real predictions or live clinical retrieval. Set up `.env` from `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_API=true
```

Restart Vite after changing environment variables. The starter API service is in `src/api.js`. Current optional calls are:
- `POST /patients/{patient_id}/analyze`
- `POST /rag/query` with `{ "question": "...", "patient_id": "P123" }`

These routes are assumptions to align with the CKD project roadmap, not a guarantee that your current FastAPI backend implements them. Update `src/api.js` and the call sites in `src/App.jsx` to match the actual backend contract. Patient create/edit/visit changes currently stay in React state and are not persisted to MySQL.

## Important implementation notes
- Demo patient records are fictional examples. Replace them with API data before any real deployment.
- The demo risk category is based on simple illustrative rules. It is **not** the trained Random Forest model, not a calibrated probability and not a clinical assessment.
- SHAP factors, charts and knowledge-source entries are interface scaffolding until connected to backend responses.
- RAG answers are clearly marked as demo responses when live API retrieval is unavailable. Add source citations and document metadata from the backend before representing any answer as evidence-grounded.
- The interface is a student-project prototype, not a medical device. Do not use it to make patient-care decisions.
- For real clinical data, implement authentication/authorization, role restrictions, audit trails, server-side validation, secure transport, appropriate data governance and privacy controls. Do not store secrets in frontend code.

## Project structure
```
ckd-care-frontend/
├── index.html
├── vite.config.js
├── package.json
├── .env.example
├── README.md
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── api.js
    └── styles.css
```
