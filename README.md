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
| **Groq AI** | llama-3.1-70b-versatile (with auto-fallback) for fast, accurate RAG responses |
| **Intelligent Fallback** | Automatically tries multiple LLM models if one is unavailable |

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
│   │   ├── rag_service.py         # ChromaDB + Groq LLM with intelligent fallback
│   │   ├── chat_orchestrator.py   # Mode routing
│   │   ├── admissions_service.py / fees_service.py / timetable_service.py
│   │   ├── ingestion_service.py   # PDF/CSV/Excel ingestion
│   └── utils/
│       ├── dependencies.py        # JWT guard (get_current_admin)
│       ├── evaluation.py          # Query evaluation logger
│       └── template_generator.py  # Excel template builder
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
└── README.md              # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+, Node.js 16+
- Free Groq API key → [console.groq.com](https://console.groq.com)

### 1. Clone & Configure
```bash
git clone <repo-url>
cd eduverse
copy .env.example .env   # Windows
# cp .env.example .env   # Mac/Linux
```

### 2. Setup Environment Variables

Fill every `FILL_THIS` value in `.env`:

| Variable | How to get |
|----------|-----------|
| `SECRET_KEY` | Run: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_DEFAULT_EMAIL` | Your email address |
| `ADMIN_DEFAULT_PASSWORD` | A strong password (8+ chars) |
| `GROQ_API_KEY` | From [console.groq.com](https://console.groq.com) → API Keys → Create |

**Note:** Leave other variables as-is — they have sensible defaults.

### 3. Backend Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

**Note:** `bcrypt==4.0.1` is pinned — do not upgrade it.

### 4. Start Backend
```bash
# from project root
uvicorn app.main:app --reload
```

**First run** auto-creates the database and seeds the admin account.  
✅ Backend: `http://localhost:8000` | Docs: `http://localhost:8000/docs`

### 5. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

✅ Frontend: `http://localhost:5173`

### 6. First Admin Login
1. Click **🛡️ Admin Panel** in the chat interface
2. Log in with `ADMIN_DEFAULT_EMAIL` / `ADMIN_DEFAULT_PASSWORD` from `.env`
3. **Set a security question** immediately (for password recovery)

---

## 📊 Data Upload Workflow

1. **Log in** to Admin Panel
2. **Download Template** for each category (Admissions / Fees / Timetable)
3. **Fill the Excel file** with your data
4. **Upload File** → System validates columns and stores data

**For Regulations/General:** Upload any PDF directly (no template needed).

### Required Columns by Category

| Category | Required Columns |
|----------|-----------------|
| **Admissions** | program_name, eligibility, duration, intake, admission_process, contact_email, department, academic_year |
| **Fees** | program_name, tuition_fee, hostel_fee, exam_fee, other_fee, total_fee, academic_year, department |
| **Timetable** | teacher_uid, teacher_name, subject, day, start_time, end_time, classroom, department |
| **Regulations** | Upload PDF directly — no template needed |
| **General** | Upload PDF or paste text directly — RAG will handle it |

---

## 🔐 Security & Admin Authentication

### Before Deploying to GitHub

- [ ] `.env` is in `.gitignore` ✅
- [ ] Run `git status` — `.env` should **NOT** appear
- [ ] `.env.example` has **only** `FILL_THIS` placeholders — **no real keys**

### If You Accidentally Committed `.env`

⚠️ The secret is permanently in the git history. You **must** rotate all secrets:

1. **Generate new secrets immediately:**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Revoke your Groq API key:**
   - Go to [console.groq.com](https://console.groq.com) → API Keys
   - Delete the old key
   - Generate a new one

3. **Remove from git history:**
   ```bash
   git filter-repo --invert-paths --path .env
   git push --force
   ```

4. **Verify it's gone:**
   ```bash
   git log --all --full-history -- .env
   # Should return nothing
   ```

### Production Hardening

| Setting | Action |
|---------|--------|
| `DEBUG=False` | Set in `.env` before deploying |
| `SECRET_KEY` | Use 32+ random hex chars, never reuse |
| `ADMIN_DEFAULT_PASSWORD` | Change on first login to something 12+ chars |
| `ALLOWED_ORIGINS` | Set to your actual domain only (not localhost) |
| `GROQ_API_KEY` | Stored only in `.env` — never hardcode |
| HTTPS | Always use HTTPS in production |

### Auth Endpoints

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/auth/login` | No | Authenticate user |
| POST | `/api/auth/forgot-password` | No | Initiate password reset |
| POST | `/api/auth/verify-answer` | No | Verify security answer |
| POST | `/api/auth/reset-password` | No | Complete password reset |
| POST | `/api/upload/upload` | **Yes** | Upload files (admin only) |
| POST | `/api/upload/text` | **Yes** | Ingest text (admin only) |
| GET | `/api/upload/download-template/{cat}` | **Yes** | Download template |

---

## 🏗️ Architecture

```
User Query (Chat) 
    ↓
Chat Orchestrator (Determines mode)
    ↓
┌─────────────────────────────────────────────┐
│ Mode Handler                                │
├─────────────────────────────────────────────┤
│ Admissions / Fees / Timetable               │
│   → SQL query (direct database)             │
│   → Structured response (no LLM)            │
│                                             │
│ Regulations / General                       │
│   → RAG Service (ChromaDB retrieval)        │
│   → Groq LLM (llama-3.1-70b-versatile)     │
│   → Intelligent Fallback (tries alt models) │
│   → AI-generated response                   │
└─────────────────────────────────────────────┘
    ↓
Chat Response (to user)
```

### Intelligent Model Fallback

The RAG service attempts models in this order:
1. `llama-3.1-70b-versatile` (primary)
2. `llama-3.1-8b-instant` (fast backup)
3. `mixtral-8x7b-32768` (secondary)
4. `llama-2-70b-4096` (legacy)

If primary model is unavailable, the system automatically tries the next one without user intervention.

---

## 📝 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ | — | Groq API key from console.groq.com |
| `SECRET_KEY` | ✅ | — | JWT signing secret (32+ hex chars) |
| `ADMIN_DEFAULT_EMAIL` | ✅ | — | First-run admin email |
| `ADMIN_DEFAULT_PASSWORD` | ✅ | — | First-run admin password |
| `DATABASE_URL` | No | `sqlite:///./eduverse.db` | SQLite database path |
| `GROQ_MODEL` | No | `llama-3.1-70b-versatile` | Primary Groq model (with auto-fallback) |
| `ALLOWED_ORIGINS` | No | `http://localhost:5173` | CORS origins (comma-separated) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | JWT token lifetime |
| `EMBEDDING_MODEL` | No | `BAAI/bge-base-en-v1.5` | HuggingFace embedding model |
| `VECTOR_STORE_PATH` | No | `./data/chroma_db` | ChromaDB storage path |
| `RAG_TOP_K` | No | `5` | Number of chunks to retrieve from ChromaDB |
| `RAG_SIMILARITY_THRESHOLD` | No | `0.4` | Minimum similarity score for chunks |

---

## 🚨 Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `bcrypt` auth error | Verify `bcrypt==4.0.1` is installed: `pip list \| grep bcrypt` |
| `ALLOWED_ORIGINS` parse error | Use comma-separated string: `http://localhost:5173,http://localhost:3000` |
| Admin login "Failed to fetch" | Backend not running — restart with `uvicorn app.main:app --reload` |
| Login returns 401 | Wrong credentials or admin not seeded — check `.env` values |
| Upload returns 401 | Token missing — log in to Admin Panel first |
| "No suitable Groq model" error | Check `GROQ_API_KEY` in `.env` — system will try fallback models |
| First startup slow | Normal — downloads `BAAI/bge-base-en-v1.5` embedding model (~120MB) once |
| ChromaDB schema errors | Clear `./data/chroma_db/` folder and re-upload documents |

---

## 📚 Tech Stack

**Backend:**
- FastAPI (async web framework)
- SQLAlchemy (ORM)
- ChromaDB (vector database for RAG)
- Groq API (LLM provider)
- python-jose & passlib & bcrypt (authentication)
- PyMuPDF & Pandas (file processing)

**Frontend:**
- React 18 (UI framework)
- Vite (build tool)
- Vanilla CSS (styling)
- Space Grotesk + Syne (Google Fonts)

**Infrastructure:**
- SQLite (local database)
- Chroma (persistent vector store)

---

## 📄 License

MIT License — see `LICENSE` file.

---

**Built with ❤️ for Educational Institutions**

---

## Recent Updates

### Version 1.1.0
✅ **Smart Model Fallback System**
- Automatically tries alternative Groq models if primary is unavailable
- Prevents service interruptions during model deprecations
- Caches working models for performance

✅ **Metadata Schema Fix**
- Added `topic` field to ChromaDB metadata for better document filtering
- Resolved schema inconsistencies in document ingestion

✅ **Text Ingestion Fix**
- Changed from Form data to JSON body for text uploads
- Added `TextIngestionRequest` Pydantic model

✅ **Graceful Error Handling**
- Returns user-friendly error messages instead of crashing
- Better debugging with detailed logs

### Version 1.0.0
- Initial release with all 5 chat modes
- Admin panel with file uploads
- RAG system with ChromaDB
