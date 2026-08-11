# Learnio
Learn Smarter. Study Faster.

Learnio is a production-grade, AI-powered study assistant designed for university students. It provides a centralized platform to organize study materials, generate AI summaries, create quizzes and flashcards, chat with notes using Retrieval-Augmented Generation (RAG), and track study progress.

Live Demo: https://your-vercel-app-url.vercel.app

Table of Contents
Overview
Key Features
Technology Stack
Architecture
Local Development Setup
Deployment (Vercel)
Overview
Students often manage hundreds of lecture slides, PDF notes, assignments, and deadlines across scattered platforms. Learnio solves this by acting as a single, intelligent workspace. It leverages Large Language Models (Google Gemini) and Vector Databases to allow students to interact with their specific study materials dynamically.

Key Features
AI Chat (RAG): Chat with uploaded documents. The AI answers exclusively based on provided study materials using semantic search and retrieval-augmented generation.
Study Material Management: Secure upload and processing of PDFs, DOCX, PPTX, TXT, and images.
AI Summaries: Automated generation of chapter summaries, key concepts, and formula sheets.
Quiz & Flashcard Generator: AI-generated MCQs, True/False, and short/long questions with a built-in timer, scoring system, and spaced-repetition flashcards.
Analytics Dashboard: Interactive Chart.js visualizations for study hours, quiz performance, and subject activity.
Assignments & Calendar: Integrated tracking for deadlines and exam dates.
OCR & Global Search: Convert handwritten notes to searchable text using Tesseract, with cross-entity global search.
Admin Panel: Platform-wide management for users, storage, and system statistics.
Technology Stack
Backend:

Python, Flask
SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF
Frontend:

HTML5, CSS3, JavaScript
Bootstrap 5, Chart.js
Database & AI:

PostgreSQL (Production) / SQLite (Development)
Google Gemini API
sentence-transformers & FAISS / pgvector (Semantic Search)
File Processing:

PyPDF2, pdfplumber, python-docx, python-pptx
Pillow, pytesseract
Deployment:

Vercel (Serverless)
GitHub (Version Control)
Architecture
Learnio is built using a Clean Architecture approach, ensuring separation of concerns, maintainability, and scalability. Routes act as thin controllers, delegating business logic to dedicated service layers.

Learnio/│├── app/│   ├── __init__.py          # Flask application factory│   ├── config.py            # Environment configurations│   ├── extensions.py        # SQLAlchemy, LoginManager, Migrate, CSRF│   ││   ├── routes/              # Flask Blueprints (controllers)│   ├── models/              # SQLAlchemy database models│   ├── services/            # Business logic (uploads, AI, analytics)│   ├── ai/                  # Gemini client, RAG pipeline, Vector stores│   ├── templates/           # Jinja2 HTML templates│   ├── static/              # CSS, JS, Images, Fonts│   └── utils/               # Decorators, validators, helpers│├── migrations/              # Database migration scripts├── wsgi.py                  # Vercel serverless entry point├── vercel.json              # Vercel deployment configuration├── requirements.txt         # Python dependencies└── README.md
Local Development Setup
To run Learnio locally, follow these steps:

Clone the repository:
bash

git clone https://github.com/mhasantanveer546/Learnio.git
cd Learnio
Create and activate a virtual environment:
bash

python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
Install dependencies:
bash

pip install -r requirements.txt
Configure Environment Variables:
Create a .env file in the root directory:
env

FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_super_secret_key
DATABASE_URL=postgresql://user:password@localhost:5432/learnio
GEMINI_API_KEY=your_google_gemini_api_key
Initialize the Database:
bash

flask db upgrade
Run the application:
bash

flask run
The application will be available at http://127.0.0.1:5000.