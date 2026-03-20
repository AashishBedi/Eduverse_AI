# 🎓 EduVerse AI — Educational AI Assistant

**EduVerse AI** is a production-grade intelligent educational assistant for universities and institutions. It provides **deterministic, structured data retrieval** for admissions, fees, timetables, and regulations through a dark-themed Gen Z web interface, secured by JWT-based admin authentication.

---

## 🌟 Key Features

| Feature | Detail |
|---------|--------|
| **Multi-Mode Chat** | Admissions, Fees, Timetable, Regulations, General |
| **Hybrid Retrieval** | SQL for structured data → no LLM needed; ChromaDB + Groq for unstructured |
| **Secure Admin Panel** | JWT login, bcrypt passwords, security-question recovery |
| **Template System** | Download Excel templates, fill, upload — no manual DB entry |
| **Gen Z Dark UI** | Aurora orbs, floating tiles, glassmorphism, Space Grotesk font |
| **Groq AI** | Llama3-8b-8192 via Groq API for fast, accurate RAG responses |

---

## 📁 Project Structure

```
eduverse/
├── app/
│   ├── api/               # Route handlers
│   │   ├── auth.py        # Login, forgot/reset password
│   │   ├── chat.py        # Unified chat endpoint
│   │   ├── upload.py      # File upload (JWT protected)
│   │   ├── admissions.py / fees.py / timetable.py
│   │   └── health.py / evaluation.py / rag.py
│   ├── db/
│   │   ├── database.py    # SQLAlchemy engine
│   │   └── init_db.py     # Table creation + safe column migration
│   ├── models/            # SQLAlchemy models (User, Admission, Fee, Timetable, Document)
│   ├── services/
│   │   ├── auth_service.py        # JWT, bcrypt, admin seeding
│   │   ├── rag_service.py         # ChromaDB + Groq LLM
│   │   ├── chat_orchestrator.py   # Mode routing
│   │   ├── admissions_service.py / fees_service.py / timetable_service.py
│   │   └── ingestion_service.py   # PDF/CSV/Excel ingestion
│   ├── utils/
│   │   ├── dependencies.py        # JWT guard (get_current_admin)
│   │   ├── evaluation.py          # Query evaluation logger
│   │   └── template_generator.py  # Excel template builder
│   └── config.py / main.py
├── frontend/
│   └── src/
│       ├── App.jsx / App.css      # Dark Gen Z main interface
│       └── components/
│           ├── AdminLogin.jsx/css  # JWT login + recovery modal
│           └── AdminPanel.jsx/css  # File upload interface
├── .env.example           # ← Safe template (commit this)
├── .env                   # ← Your secrets (DO NOT commit)
├── .gitignore
├── requirements.txt
├── Requirements.md        # Setup checklist
└── SECURITY.md            # GitHub safety guide
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+, Node.js 16+
- Free Groq API key → [console.groq.com](https://console.groq.com)

### 1. Clone & configure
```bash
git clone <repo-url>
cd eduverse
copy .env.example .env   # Windows
# cp .env.example .env   # Mac/Linux
```
Edit `.env` and fill every `FILL_THIS` value (see `Requirements.md` for details).

### 2. Backend
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
**First run** auto-creates the database tables and seeds the admin account.  
Backend: `http://localhost:8000` | Docs: `http://localhost:8000/docs`

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend: `http://localhost:5173`

---

## 🔐 Admin Authentication

1. Click **🛡️ Admin Panel** in the chat interface
2. Log in with `ADMIN_DEFAULT_EMAIL` / `ADMIN_DEFAULT_PASSWORD` from your `.env`
3. Set a security question after first login (for password recovery)

### Auth Endpoints

| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/api/auth/login` | No |
| POST | `/api/auth/forgot-password` | No |
| POST | `/api/auth/verify-answer` | No |
| POST | `/api/auth/reset-password` | No |
| POST | `/api/upload/upload` | **Yes** |
| GET  | `/api/upload/download-template/{cat}` | **Yes** |

---

## 📊 Data Upload Workflow

1. Log in to Admin Panel
2. **Download Template** for each category (Admissions / Fees / Timetable)
3. Fill the Excel file
4. **Upload File** → system validates columns and stores data

For Regulations/General: upload any PDF directly (no template needed).

---

## 🏗️ Architecture

```
User Query → Chat Orchestrator → Mode Handler → Response

Admissions  │ fees  → SQL (direct, no LLM)       → Structured response
Timetable   → SQL + RAG hybrid                    → Schedule response
Regulations │ General → ChromaDB → Groq Llama3   → AI response
```

---

## 📝 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ | — | Groq API key |
| `SECRET_KEY` | ✅ | — | JWT signing secret (32+ hex chars) |
| `ADMIN_DEFAULT_EMAIL` | ✅ | — | First-run admin email |
| `ADMIN_DEFAULT_PASSWORD` | ✅ | — | First-run admin password |
| `DATABASE_URL` | No | `sqlite:///./eduverse.db` | Database path |
| `GROQ_MODEL` | No | `llama3-8b-8192` | Groq model name |
| `ALLOWED_ORIGINS` | No | `http://localhost:5173,...` | CORS origins (comma-separated) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | JWT lifetime |

---

## 🚨 Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| `bcrypt` error | Make sure `bcrypt==3.2.2` is installed (pinned in requirements.txt) |
| `ALLOWED_ORIGINS` parse error | Use comma-separated string: `http://localhost:5173,http://localhost:3000` |
| Admin login "Failed to fetch" | Backend not running — start with `uvicorn app.main:app --reload` |
| Login 401 | Wrong credentials or admin not seeded — check `.env` values |
| Upload 401 | Token missing — log in to Admin Panel first |
| First startup slow | Normal — downloads `BAAI/bge-base-en-v1.5` embedding model once |

---

## 📚 Tech Stack

**Backend:** FastAPI · SQLAlchemy · ChromaDB · Groq (Llama3) · python-jose · passlib+bcrypt==3.2.2 · PyMuPDF · Pandas  
**Frontend:** React · Vite · Vanilla CSS · Space Grotesk + Syne (Google Fonts)

---

## 📄 License

MIT License — see `LICENSE` file.

---

**Built with ❤️ for Educational Institutions**
