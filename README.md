# Learnio
Learn Smarter. Study Faster.

Learnio is a production-grade, AI-powered study assistant designed for university students. It provides a centralized platform to organize study materials, generate AI summaries, create quizzes and flashcards, chat with notes using Retrieval-Augmented Generation (RAG), and track study progress.

Live Demo: https://learnio-xi.vercel.app

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Local Development Setup](#local-development-setup)
- [Deployment (Vercel)](#deployment-vercel)
- [Admin & CLI Tools](#admin--cli-tools)

## Overview
Students often manage hundreds of lecture slides, PDF notes, assignments, and deadlines across scattered platforms. Learnio solves this by acting as a single, intelligent workspace. It leverages Google Gemini and FAISS to allow students to interact with their specific study materials dynamically.

## Key Features
- **AI Chat (RAG):** Chat with uploaded documents. The AI answers exclusively based on provided study materials using semantic search and retrieval-augmented generation.
- **Study Material Management:** Secure upload and processing of PDFs, DOCX, PPTX, TXT, and images.
- **AI Summaries:** Automated generation of chapter summaries, key concepts, and formula sheets.
- **Quiz & Flashcard Generator:** AI-generated MCQs, True/False, and short/long questions with a built-in timer, scoring system, and spaced-repetition flashcards.
- **Analytics Dashboard:** Interactive Chart.js visualizations for study hours, quiz performance, and subject activity.
- **Assignments & Calendar:** Integrated tracking for deadlines and exam dates.
- **OCR & Global Search:** Convert handwritten notes to searchable text using Tesseract, with cross-entity global search.
- **Admin Panel:** Platform-wide management for users, storage, and system statistics — including suspending/reactivating accounts.

## Technology Stack

**Backend:**
- Python 3.12, Flask
- SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF

**Frontend:**
- HTML5, CSS3, JavaScript
- Chart.js

**Database & AI:**
- PostgreSQL via Neon (Production) / SQLite (Development)
- Google Gemini API — chat, quiz/summary generation, and text embeddings (`models/text-embedding-004`)
- FAISS — local vector similarity search over Gemini-generated embeddings

**File Processing:**
- pdfplumber, python-docx, python-pptx
- Pillow, pytesseract

**Storage:**
- Backblaze B2 (S3-compatible object storage) for uploaded materials

**Deployment:**
- Vercel (Serverless Python, via `uv`)
- GitHub (Version Control)

## Architecture
Learnio is built using a Clean Architecture approach, ensuring separation of concerns, maintainability, and scalability. Routes act as thin controllers, delegating business logic to dedicated service layers.
> **Note:** The entrypoint is `index.py`, not `app.py`. It's named this way specifically to avoid a module name collision with the `app/` package on Vercel's serverless runtime — `app.py` importing `from app import create_app` would otherwise shadow itself.

## Local Development Setup

To run Learnio locally, follow these steps:

**1. Clone the repository:**
```bash
git clone https://github.com/mhasantanveer546/Learnio.git
cd Learnio
```

**2. Install [uv](https://docs.astral.sh/uv/) (used for dependency management):**
```bash
pip install uv
```

**3. Install dependencies from `pyproject.toml`:**
```bash
uv sync
```

**4. Activate the virtual environment `uv` creates:**
```bash
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

**5. Configure environment variables:**
Create a `.env` file in the root directory:
```env
FLASK_APP=index.py
FLASK_ENV=development
SECRET_KEY=your_super_secret_key
GEMINI_API_KEY=your_google_gemini_api_key
R2_ENDPOINT_URL=your_backblaze_b2_endpoint
R2_ACCESS_KEY_ID=your_b2_key_id
R2_SECRET_ACCESS_KEY=your_b2_secret_key
R2_BUCKET_NAME=your_b2_bucket_name
```
(`DATABASE_URL` isn't needed for local dev — development mode uses a local SQLite file automatically. Set it only if you want to point locally at Neon.)

**6. Initialize the database:**
```bash
flask db upgrade
```

**7. Run the application:**
```bash
flask run
```
The application will be available at http://127.0.0.1:5000.

## Deployment (Vercel)

Learnio deploys to Vercel's serverless Python runtime via `uv` and `pyproject.toml`. Key points specific to this setup:

- **Entrypoint:** `vercel.json` points at `index.py`, matching the `functions` config:
```json
  {
    "functions": {
      "index.py": { "maxDuration": 60 }
    }
  }
```
- **Environment variables required in Vercel** (Project Settings → Environment Variables, set for Production): `SECRET_KEY`, `FLASK_ENV=production`, `DATABASE_URL` (Neon **pooled** connection string), `GEMINI_API_KEY`, `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`.
- **Database:** Uses Neon Postgres. `SQLALCHEMY_ENGINE_OPTIONS` (in `app/config.py`) sets `pool_pre_ping` and `pool_recycle` to handle Vercel's cold-start connection behavior against Neon's connection pooler.
- **Migrations:** Vercel's build step doesn't run migrations. After schema changes, run `flask db upgrade` from your local machine with `DATABASE_URL` pointed at Neon, before deploying.
- **Embeddings:** No local ML models are bundled (no `torch`/`transformers`/`sentence-transformers`) — embeddings are generated via the Gemini API at runtime, keeping the deployed bundle well under Vercel's size limits.

## Admin & CLI Tools

Two custom Flask CLI commands, defined in `app/cli.py`:

**Promote a user to admin:**
```bash
flask create-admin user@example.com
```

**Seed demo data** (subjects, assignments, study sessions, and material records) for an existing user:
```bash
flask seed-demo user@example.com
```
Run either against Neon by pointing your local `DATABASE_URL` at the production database first.
