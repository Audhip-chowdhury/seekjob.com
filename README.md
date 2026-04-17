# SeekJob

Full-stack job board for a simulated city: **React (Vite)** + **FastAPI** + **SQLite**.

## Prerequisites

- Python 3.11+ with `pip`
- Node.js 18+ with `npm`

## Backend

```bash
cd backend
pip install -r requirements.txt
python seed.py          # creates seekjob.db + uploads + demo data (password: password123)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://localhost:8000`
- Health: `GET http://localhost:8000/health`
- Static uploads: `http://localhost:8000/uploads/...`

### Seeded logins (after `seed.py`)

- **Companies:** emails like `careers@meridiantech.nm` … (see `seed.py` `COMPANIES_DATA`)
- **Applicants:** `priya.sharma@email.nm` … (see `APPLICANTS_DATA`)
- Password for all: **`password123`**

## Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: `http://localhost:5173`
- Optional: create `frontend/.env` with `VITE_API_URL=http://localhost:8000`

## Features

- Separate **company** vs **applicant** registration and JWT auth
- **Jobs:** filter (company name, job type), sort by date, detail page, apply (applicant)
- **Company:** create postings, view applicants, update status (Applied → Interview → Accepted / Rejected), CV/photo links
- **Discussions:** threaded posts with optional job/company tags

## Project layout

- `backend/` — FastAPI, SQLAlchemy, `seed.py`, `uploads/`
- `frontend/` — Vite + React + Tailwind
