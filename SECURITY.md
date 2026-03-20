# 🔒 Security Policy — EduVerse AI

## ⚠️ Before Pushing to GitHub

Go through this checklist **every time** before `git push`:

- [ ] `.env` is listed in `.gitignore` ← already done
- [ ] Run `git status` — confirm `.env` does **not** appear
- [ ] Run `git log --all -- .env` — if it returns anything, the file was committed before; see "Accidentally Committed" below
- [ ] Run `git status` — confirm `*.db` files are not staged
- [ ] `.env.example` has **no real values** — only `FILL_THIS` placeholders

---

## 🔑 Sensitive Files (Never Commit)

| File | Contains |
|------|----------|
| `.env` | Groq API key, JWT secret, admin credentials |
| `eduverse.db` | All user data, hashed passwords |
| `data/chroma_db/` | Embedded document vectors |
| `uploads/` | User-uploaded files |

All of these are covered in `.gitignore`.

---

## 🚨 If You Accidentally Committed `.env`

If `.env` was ever committed (even in a previous commit), the secret is **permanently in your history** and must be rotated:

1. **Rotate all secrets immediately:**
   - Generate a new `SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Revoke and regenerate your **Groq API key** at [console.groq.com](https://console.groq.com)
   - Change your admin password

2. **Remove from git history:**
   ```bash
   git filter-repo --invert-paths --path .env
   # or BFG Repo Cleaner:
   bfg --delete-files .env
   git push --force
   ```

3. **Verify it's gone:**
   ```bash
   git log --all --full-history -- .env
   # Should return nothing
   ```

---

## 🛡️ Production Hardening

| Setting | Action |
|---------|--------|
| `DEBUG=False` | Set in `.env` before deploying |
| `SECRET_KEY` | Use 32+ random hex chars, never reuse |
| `ADMIN_DEFAULT_PASSWORD` | Change on first login |
| `ALLOWED_ORIGINS` | Set to your actual domain only |
| `GROQ_API_KEY` | Stored only in `.env` — never hardcode |
| HTTPS | Always use HTTPS in production |
| Admin password | Minimum 12 chars, mixed case + symbols |

---

## 📣 Reporting Vulnerabilities

If you discover a security vulnerability, please open a **private** GitHub issue or contact the maintainer directly. Do not post vulnerabilities publicly.
