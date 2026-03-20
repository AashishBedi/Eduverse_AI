# EduVerse AI – Setup Checklist

> Fill every `FILL_THIS` value before running. See `.env.example` for the full template.

---

## Step 1 — Copy environment file

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Mac/Linux
```

Then open `.env` and fill in:

| Variable | What to put |
|----------|-------------|
| `SECRET_KEY` | Run: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_DEFAULT_EMAIL` | Your email address |
| `ADMIN_DEFAULT_PASSWORD` | A strong password (8+ chars) |
| `GROQ_API_KEY` | From [console.groq.com](https://console.groq.com) → API Keys |

Everything else has sensible defaults and can be left as-is.

---

## Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `bcrypt==3.2.2` is pinned — do not upgrade it, it breaks `passlib`.

---

## Step 3 — Install frontend dependencies

```bash
cd frontend
npm install
```

---

## Step 4 — Start the backend

```bash
# from project root
uvicorn app.main:app --reload
```

First run will:
1. Create `eduverse.db` with all tables
2. Seed your admin account using `ADMIN_DEFAULT_EMAIL` / `ADMIN_DEFAULT_PASSWORD`
3. Print: `✅ EduVerse AI is ready → http://127.0.0.1:8000/docs`

---

## Step 5 — Start the frontend

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173**

---

## Step 6 — First login (Admin Panel)

1. Click **🛡️ Admin Panel**
2. Log in with your email and password from `.env`
3. **Set a security question** immediately (for password recovery)

---

## Step 7 — Upload your data

Download templates from Admin Panel → fill → upload:

| Category | Key columns |
|----------|-------------|
| **Admissions** | program_name, eligibility, duration, intake, admission_process, contact_email, department, academic_year |
| **Fees** | program_name, tuition_fee, hostel_fee, exam_fee, other_fee, total_fee, academic_year, department |
| **Timetable** | teacher_uid, teacher_name, subject, day, start_time, end_time, classroom, department |
| **Regulations** | Upload PDF directly — no template needed |

---

## GitHub Safety Checklist

Before `git push`:
- [ ] `.env` is in `.gitignore` ✅
- [ ] Run `git status` — `.env` should NOT appear
- [ ] `.env.example` has only `FILL_THIS` placeholders — no real keys

See `SECURITY.md` for full guidance including how to fix accidentally committed secrets.
