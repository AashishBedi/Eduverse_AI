# 🎓 EduVerse AI - Educational AI Assistant

**EduVerse AI** is a production-grade, intelligent educational assistant designed for universities and educational institutions. It provides **deterministic, structured data retrieval** for admissions, fees, timetables, and regulations through a clean, modern web interface.

---

## 🌟 Key Features

### ✅ Multi-Mode Intelligence
- **Admissions Mode**: Structured database queries for admission requirements, eligibility, and processes
- **Fees Mode**: Direct fee structure retrieval with detailed breakdowns
- **Timetable Mode**: Hybrid routing (SQL + RAG) for teacher schedules and class timings
- **Regulations Mode**: RAG-based retrieval for academic policies and regulations
- **General Mode**: General educational queries using RAG

### ✅ Production-Ready Architecture
- **Deterministic Retrieval**: Structured data (admissions, fees, timetables) stored in SQLite with direct SQL queries
- **No LLM Dependency**: Admissions and fees queries don't require LLM processing
- **Clean Responses**: No debug information, no "According to Document X", no relevance scores
- **Template System**: Excel templates with sample data for all modules
- **Strict Validation**: Column validation before file upload prevents bad data

### ✅ Modern Tech Stack
- **Backend**: FastAPI, SQLAlchemy, ChromaDB, Groq LLM
- **Frontend**: React, Vite
- **Database**: SQLite (structured data) + ChromaDB (vector embeddings)
- **AI**: Groq API with Llama models for RAG queries

---

## 📁 Project Structure

```
eduverse/
├── app/
│   ├── api/              # API endpoints
│   │   ├── admissions.py # Admissions API
│   │   ├── fees.py       # Fees API
│   │   ├── timetable.py  # Timetable API
│   │   ├── chat.py       # Chat orchestration
│   │   └── upload.py     # File upload & templates
│   ├── db/               # Database setup
│   │   ├── database.py   # SQLAlchemy setup
│   │   └── init_db.py    # Database initialization
│   ├── models/           # SQLAlchemy models
│   │   ├── admission.py  # Admission model
│   │   ├── fee.py        # Fee model
│   │   ├── timetable.py  # Timetable model
│   │   └── document.py   # Document model
│   ├── services/         # Business logic
│   │   ├── admissions_service.py    # Admissions queries
│   │   ├── fees_service.py          # Fees queries
│   │   ├── timetable_service.py     # Timetable queries
│   │   ├── chat_orchestrator.py     # Mode routing
│   │   ├── hybrid_router.py         # Timetable hybrid routing
│   │   ├── rag_service.py           # RAG with ChromaDB
│   │   └── ingestion_service.py     # File processing
│   ├── utils/            # Utilities
│   │   └── template_generator.py    # Excel template generation
│   ├── config.py         # Configuration
│   └── main.py           # FastAPI app
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── AdminPanel.jsx  # Admin upload interface
│   │   ├── services/
│   │   │   └── api.js          # API client
│   │   ├── App.jsx             # Main app
│   │   └── App.css             # Styling
│   └── package.json
├── chroma_db/            # ChromaDB vector storage
├── requirements.txt      # Python dependencies
└── README.md
```

---

## 🚀 Setup Instructions

### Prerequisites
- **Python 3.9+**
- **Node.js 16+**
- **Groq API Key** (get from [console.groq.com](https://console.groq.com))

### 1. Clone Repository
```bash
git clone <repository-url>
cd eduverse
```

### 2. Backend Setup

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment
Create `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

#### Initialize Database
```bash
python -m app.db.init_db
```

#### Start Backend Server
```bash
uvicorn app.main:app --reload
```

Backend will run at: `http://localhost:8000`

### 3. Frontend Setup

#### Install Dependencies
```bash
cd frontend
npm install
```

#### Start Development Server
```bash
npm run dev
```

Frontend will run at: `http://localhost:5173`

---

## 📊 Data Upload Workflow

### Step 1: Access Admin Panel
Click **"Admin Panel"** button in the top-right corner

### Step 2: Download Templates
1. Select category (Admissions, Fees, Timetable, Regulations)
2. Click **"Download Template"** button
3. Template includes sample data and required columns

### Step 3: Fill Template
- **Admissions Template**: program_name, eligibility, duration, intake, admission_process, contact_email, department, academic_year
- **Fees Template**: program_name, tuition_fee, hostel_fee, exam_fee, other_fee, total_fee, academic_year, department
- **Timetable Template**: teacher_uid, teacher_name, subject, day, start_time, end_time, classroom, department

### Step 4: Upload File
1. Select filled Excel/CSV file
2. Choose category
3. Enter department and academic year
4. Click **"Upload File"**

### Step 5: Validation
- System validates required columns
- Rejects files with missing columns
- Shows clear error messages

---

## 💬 Using the Chat Interface

### Quick Actions (Home Screen)
- **🎓 Admission Info**: Fetches all admission programs
- **📅 Today's Schedule**: Shows today's timetable
- **💰 Fee Details**: Displays fee structures

### Mode Selection
Select mode from dropdown before querying:

#### Admissions Mode
**Example Queries**:
- "What are the admission requirements for B.Tech Computer Science?"
- "M.Tech Data Science admission process"
- "Show me all admission programs"

**Response Format**:
```
🎓 B.Tech Computer Science

Eligibility:
10+2 with Physics, Chemistry, Mathematics (60% minimum)

Duration:
4 years

Intake Capacity:
120 seats

Admission Process:
JEE Main score based counseling

Contact:
admissions@example.edu
```

#### Fees Mode
**Example Queries**:
- "What is the fee structure for B.Tech Computer Science?"
- "Show me all fee structures"

**Response Format**:
```
💰 B.Tech Computer Science - Fee Structure

Tuition Fee:
₹1,50,000

Hostel Fee:
₹50,000

Total Fee:
₹2,15,000
```

#### Timetable Mode
**Example Queries**:
- "Show me T002's schedule" (Teacher ID query)
- "What classes are on Monday?"
- "When does Dr. John Doe teach?"

#### Regulations Mode
**Example Queries**:
- "What is the attendance policy?"
- "Tell me about exam regulations"

---

## 🏗️ Architecture Overview

### Mode Routing Strategy

```
User Query → Chat Orchestrator → Mode-Specific Handler → Response

Admissions Mode → admissions_service → SQL Query → Clean Response
Fees Mode → fees_service → SQL Query → Clean Response
Timetable Mode → hybrid_router → SQL or RAG → Formatted Response
Regulations Mode → rag_service → LLM + ChromaDB → Answer
```

### Data Flow

#### Structured Data (Admissions, Fees, Timetable)
```
Upload → Validation → Parser → SQLite Database → Direct SQL Query → Response
```

#### Unstructured Data (Regulations, General)
```
Upload → Text Extraction → Chunking → Embedding → ChromaDB → RAG Query → LLM Response
```

### Database Schema

#### Admissions Table
- `id`, `program_name`, `eligibility`, `duration`, `intake`, `admission_process`, `contact_email`, `department`, `academic_year`

#### Fees Table
- `id`, `program_name`, `tuition_fee`, `hostel_fee`, `exam_fee`, `other_fee`, `total_fee`, `academic_year`, `department`

#### Timetable Table
- `id`, `teacher_uid`, `teacher_name`, `subject`, `day`, `start_time`, `end_time`, `classroom`, `department`

---

## 🔧 API Endpoints

### Chat
- `POST /api/chat/` - Send chat message

### Admissions
- `GET /api/admissions` - Get all admissions
- `GET /api/admissions/{program_name}` - Get specific program

### Fees
- `GET /api/fees` - Get all fees
- `GET /api/fees/{program_name}` - Get specific program fees

### Timetable
- `GET /api/timetable/today` - Get today's schedule
- `GET /api/timetable/teacher/{teacher_uid}` - Get teacher's schedule
- `GET /api/timetable/day/{day}` - Get day's schedule

### Upload
- `POST /api/upload/upload` - Upload file
- `GET /api/upload/download-template/{category}` - Download template
- `GET /api/upload/template-info/{category}` - Get template info

### Documentation
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc UI

---

## 🎯 Key Design Decisions

### 1. Hybrid Architecture
- **Structured data** (admissions, fees, timetables) → SQL for deterministic retrieval
- **Unstructured data** (regulations, policies) → RAG for semantic search

### 2. No LLM for Structured Queries
- Admissions and fees queries use direct database lookups
- Faster response times
- Guaranteed accuracy
- No hallucinations

### 3. Template-Driven Ingestion
- Excel templates enforce schema
- Sample data provides clear examples
- Column validation prevents errors

### 4. Clean Response Format
- No debug information
- No "According to Document X"
- No relevance scores
- Professional, user-friendly formatting

---

## 🧪 Testing

### Backend Tests
```bash
# Test database
python check_db.py

# Test admissions
python -c "from app.db.database import SessionLocal; from app.models.admission import Admission; db = SessionLocal(); print(f'Admissions: {db.query(Admission).count()}'); db.close()"

# Test API
curl http://localhost:8000/api/admissions
```

### Frontend Tests
1. Open `http://localhost:5173`
2. Test quick action buttons
3. Upload sample templates
4. Query in different modes

---

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM | Yes |
| `DATABASE_URL` | SQLite database path | No (defaults to `sqlite:///./eduverse.db`) |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | No (defaults to `./chroma_db`) |

---

## 🚨 Troubleshooting

### Backend Issues

**Issue**: `ModuleNotFoundError`
```bash
pip install -r requirements.txt
```

**Issue**: Database not initialized
```bash
python -m app.db.init_db
```

**Issue**: GROQ_API_KEY not set
```bash
# Add to .env file
GROQ_API_KEY=your_key_here
```

### Frontend Issues

**Issue**: `npm install` fails
```bash
rm -rf node_modules package-lock.json
npm install
```

**Issue**: Backend connection error
- Ensure backend is running on `http://localhost:8000`
- Check CORS settings in `app/config.py`

---

## 📚 Tech Stack Details

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **ChromaDB**: Vector database for embeddings
- **Groq**: LLM API (Llama models)
- **PyMuPDF**: PDF text extraction
- **Pandas**: Excel/CSV parsing
- **Pydantic**: Data validation

### Frontend
- **React**: UI library
- **Vite**: Build tool
- **CSS**: Custom styling with gradients and animations

---

## 🎨 Features Highlights

### ✅ Quick Actions
- One-click access to common queries
- Pre-configured API calls
- Instant results display

### ✅ Template System
- Downloadable Excel templates for all modules
- Sample data included
- Clear column requirements

### ✅ Admin Panel
- Easy file upload interface
- Template downloads
- Validation feedback

### ✅ Clean UI
- Modern gradient design
- Smooth animations
- Responsive layout
- Professional appearance

---

## 📄 License

This project is licensed under the MIT License.

---

## 👥 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📧 Support

For issues or questions, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for Educational Institutions**
