# 🏃 FitTrack API

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139-009688)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED)](https://www.docker.com/)
[![Live API](https://img.shields.io/badge/API-live-brightgreen)](https://fittrack-api-ww6w.onrender.com/docs)

A FastAPI backend for tracking gym, running, swimming, and cycling workouts — with Gemini AI-powered workout analysis and weekly training plans. Includes a companion Telegram bot so people can log workouts and get AI feedback without ever touching an API client.

**Why this exists:** most fitness trackers force you into one sport. FitTrack lets you log gym sessions, runs, swims, and rides in one place, with proper relational data instead of a flat "workouts" table, and gets an AI coach's opinion on your training. Built as a course final project, then extended past the course scope with JWT auth, a Telegram bot, and cloud deployment.

**🔗 Live API:** https://fittrack-api-ww6w.onrender.com/docs
**🤖 Live bot:** [@fittrackYbot](https://t.me/fittrackYbot) on Telegram — running 24/7 on Railway

> Free-tier API may take 30–50s to wake up after inactivity — that's Render's free plan sleeping, not a bug.

---

## Table of contents

- [Screenshots](#screenshots)
- [Features](#features)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Database schema](#database-schema)
- [Quick start](#quick-start)
- [API reference](#api-reference)
- [Authentication](#authentication)
- [Example requests](#example-requests)
- [Deployment](#deployment)

---

## Screenshots

<!-- Add a screenshot of Swagger UI here, e.g.: -->
<!-- ![Swagger UI](docs/screenshot-swagger.png) -->
<!-- Add a screenshot/GIF of the Telegram bot flow here, e.g.: -->
<!-- ![Telegram bot](docs/screenshot-bot.png) -->

> *(Screenshots coming soon — or add your own from `/docs` and the Telegram bot!)*

## Features

- 🔐 **JWT authentication** — register/login, bcrypt-hashed passwords, protected endpoints return `401` without a valid token
- 🏋️ **Multi-sport workout tracking** — gym (multiple exercises per session), running, swimming, cycling, each with sport-specific fields
- 🔒 **Ownership enforcement** — users can only read/edit/delete their own data; verified at the endpoint level, not just by hiding UI
- 📊 **Analytics** — per-user stats, weekly summaries, admin-only "overdue users" report (role-based access)
- 🤖 **AI coaching** — Gemini-powered analysis of a single workout, and AI-generated weekly training plans based on recent history
- 💬 **Telegram bot** — phone-number registration, conversational multi-step workout logging (FSM), inline AI features — talk to your data instead of filling forms
- 🐳 **Dockerized** — one command spins up the API + Postgres, migrations run automatically
- ☁️ **Deployed** — API on Render, bot on Railway, both live and publicly usable right now

## Tech stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| ORM | SQLAlchemy 2.0 (typed, `Mapped`/`mapped_column`) |
| Database | PostgreSQL |
| Migrations | Alembic |
| Auth | JWT (`python-jose`) + `passlib[bcrypt]` |
| AI | Gemini API (direct REST, `httpx`) |
| Bot | aiogram 3.x (async, FSM-based) |
| Containerization | Docker + docker-compose |
| Deployment | Render (API + Postgres), Railway (bot) |

## Project structure

```
fittrack-api/
├── app/
│   ├── models/       # SQLAlchemy models (User, Workout, GymSet, RunSession, SwimSession, CyclingSession, AiInsight)
│   ├── schemas/       # Pydantic request/response schemas
│   ├── routers/       # auth, users, workouts, analytics, ai, bot
│   ├── services/       # Gemini client, workout formatter, JWT/password security
│   └── database.py     # engine, session, Base
├── alembic/            # migrations
├── bot/                 # Telegram bot (aiogram) — separate deployable service
│   ├── handlers/         # registration, workout FSM, stats, AI
│   ├── services/          # API client, security helpers
│   └── main.py
├── Dockerfile           # API image
├── bot/Dockerfile        # bot image
└── docker-compose.yml
```

## Database schema

6 tables, relationally connected (not a flat schema):

```
users ──┬──< workouts ──┬──< gym_sets        (1 workout → many sets)
        │               ├──1 run_session     (1-to-1)
        │               ├──1 swim_session    (1-to-1)
        │               └──1 cycling_session (1-to-1)
        └──< ai_insights
```

- **`users`** — credentials, phone/Telegram linkage, `is_admin` flag
- **`workouts`** — type, date, duration; owns the sport-specific detail row
- **`gym_sets` / `run_sessions` / `swim_sessions` / `cycling_sessions`** — one table per sport, cascade-deleted with their workout
- **`ai_insights`** — stored Gemini responses (workout analysis or weekly plan), linked to a user and optionally a workout

## Quick start

### Option A — Docker (fastest)

```bash
git clone https://github.com/lumis-code/fittrack-api.git
cd fittrack-api
cp .env.example .env   # fill in your values
docker-compose up --build
```

API is live at `http://localhost:8000/docs`. Migrations run automatically on container start.

### Option B — Local (no Docker)

```bash
git clone https://github.com/lumis-code/fittrack-api.git
cd fittrack-api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your values, incl. a local PostgreSQL DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload
```

### Option C — Telegram bot

```bash
cd bot
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # BOT_TOKEN from @BotFather, API_BASE_URL, BOT_SERVICE_TOKEN
cd ..
python -m bot.main   # run from repo root — bot uses `bot.*` package imports
```

## API reference

Full interactive docs (Swagger UI) at `/docs` once running. Main groups:

| Prefix | Purpose |
|---|---|
| `/auth` | Register, login (returns JWT) |
| `/users` | View/update/delete your profile |
| `/workouts` | Full CRUD on workouts (JWT-protected, owner-only) |
| `/analytics` | Personal stats, weekly summaries, admin overdue report |
| `/ai` | Analyze a workout, generate a weekly plan (Gemini) |
| `/bot` | Server-to-server endpoints for the Telegram bot (`X-Bot-Token`-protected) |

## Authentication

1. `POST /auth/register` → returns a JWT immediately
2. `POST /auth/login` (OAuth2 password form) → returns a JWT
3. Send `Authorization: Bearer <token>` on protected requests, or click **Authorize** in Swagger UI
4. Every workout/analytics/AI endpoint checks that the resource belongs to the authenticated user — a 403, not a 200 with someone else's data
5. The Telegram bot doesn't use JWT (it isn't a human logging in) — it authenticates as a trusted service via a shared `X-Bot-Token` header, and passes `telegram_id` explicitly to act on behalf of the right user

## Example requests

**Register + get a token:**

```bash
curl -X POST https://fittrack-api-ww6w.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alex", "email": "alex@example.com", "password": "secret123"}'
```

**Log a run (with your token):**

```bash
curl -X POST https://fittrack-api-ww6w.onrender.com/workouts/ \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "run",
    "date": "2026-07-31T10:00:00",
    "duration_min": 32,
    "run_session": {"distance_km": 5, "avg_pace_min_km": 6.4, "elevation_m": 40}
  }'
```

**Get an AI take on it:**

```bash
curl -X POST https://fittrack-api-ww6w.onrender.com/ai/analyze/1 \
  -H "Authorization: Bearer <your_token>"
```

## Deployment

- **API + PostgreSQL** → Render (free tier)
- **Telegram bot** → Railway (runs continuously, not tied to a local machine)
- Both deploy automatically on push to `main`

---

Built by [**lumis-code**](https://github.com/lumis-code).
