# Theo Anold Control System

Campus access control: two-factor student entry, single-factor exit,
vehicle plate recognition, visitor passes, live guard dashboard,
offline-capable edge service, append-only audit log.

## Stack
FastAPI + PostgreSQL + Redis + React (Vite/TS) + Docker Compose.

## Run locally
```bash
cp .env.example .env      # then edit JWT_SECRET
docker compose up --build
Update the checkboxes as you finish each piece — it doubles as your implementation-plan tracker.

---

## Step 5 — Guardrails before you push real work

A few things worth knowing given this project's nature:

- **Never commit `.env`.** The `ENROLLMENT_SHARED_SECRET` and `JWT_SECRET` must stay out of git. Rotate them if they ever leak.
- **This is biometric-adjacent code.** The design stores *template hashes*, not raw images — keep it that way in every branch. If you ever add test fixtures, use synthetic hashes, never real student data (the doc explicitly says "do not use real student data" for demos).
- **Private repo is the safer default** for a university security system. You can flip to public later if the university agrees.
- **Add a `LICENSE`** only if the university tells you what license they want (many use proprietary/internal). Don't add MIT/GPL blindly.
- **GitHub Actions**: your doc mentions CI on every push. Add `.github/workflows/ci.yml` once tests exist — I can generate that too.

---

## TL;DR

1. **Ask me to finish the code first** (I'm mid-file) — or push as explicit WIP.
2. Create `.gitignore` + `.env.example` **before** `git add .`
3. `git status` → confirm no secrets/pycache → commit → push to a **private** repo.

Want me to continue the build now so you can push a complete, runnable repo in one go? Just say **"continue the build"** and I'll finish dashboard/reports/main/alembic/frontend/edge/simulator/tests in the same format.
