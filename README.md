# FitTrack API

A FastAPI backend for tracking gym, running, swimming, and cycling workouts, with Gemini AI integration for workout analysis and weekly plan generation. A companion Telegram bot is included as an alternative client for phone-based registration and conversational workout logging.

## Tech stack

- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Alembic
- JWT authentication (`python-jose`, `passlib[bcrypt]`)
- Gemini API integration
- Docker
- aiogram for the Telegram bot
- httpx for backend and AI requests
- python-dotenv for local environment config

## Features

- User registration and login with JWT-based auth
- Full workout CRUD across 4 sport types: gym, run, swim, cycling
- Ownership enforcement so users can only access and modify their own workouts
- Analytics endpoints for user stats, weekly summaries, and admin-only overdue user reports
- Gemini AI-powered workout analysis and weekly training plan generation
- Telegram bot flow with share-contact registration, bot-authenticated server calls, and conversational workout logging
- Separate `/bot/*` endpoints for Telegram bot server-to-server requests secured by `X-Bot-Token`

## Project structure

- `app/models/` — SQLAlchemy models for users, workouts, sessions, gym sets, and AI insights
- `app/schemas/` — Pydantic models for request and response validation
- `app/routers/` — FastAPI endpoint groups for auth, users, workouts, analytics, AI, and bot integration
- `app/services/` — Gemini client, workout formatting, and security utilities
- `bot/` — Telegram bot package using aiogram, async bot client, FSM handlers, and bot config

## Database schema

- `users` — app users with login credentials, Telegram linkage, and admin flag
- `workouts` — workout entries that belong to a user and store workout type, date, duration, and notes
- `gym_sets` — multiple gym exercise records inside a gym workout
- `run_sessions` — running-specific workout details for a workout
- `swim_sessions` — swimming-specific workout details for a workout
- `cycling_sessions` — cycling-specific workout details for a workout
- `ai_insights` — stored Gemini responses for workout analysis and weekly plan generation

## Setup instructions — Local (without Docker)

1. Clone the repo:

```bash
git clone <repo-url>
cd fittrack-api
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a root `.env` from `.env.example` and fill in your values.

5. Set up PostgreSQL locally and configure `DATABASE_URL` in `.env`.

6. Run migrations:

```bash
alembic upgrade head
```

7. Start the API server:

```bash
uvicorn app.main:app --reload
```

8. Open the interactive docs:

```text
http://localhost:8000/docs
```

## Setup instructions — Docker

1. Build and start the services:

```bash
docker-compose up --build
```

2. The compose setup starts the FastAPI app and PostgreSQL.
3. The app container runs `alembic upgrade head` automatically before launching.

## Setup instructions — Telegram bot

1. Navigate to the bot folder and create a bot-specific environment:

```bash
cd bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Create `bot/.env` from `bot/.env.example` and fill in the values.
3. Get a bot token from @BotFather.
4. Run the bot from the repo root:

```bash
python -m bot.main
```

> Run from the repository root so the bot can resolve `bot.*` imports correctly.

## API Documentation

Once running, open:

```text
http://localhost:8000/docs
```

### Main endpoint groups

- `/auth` — register and login with JWT
- `/users` — fetch, update, and delete user profiles
- `/workouts` — create, list, retrieve, update, and delete workouts
- `/analytics` — user stats, weekly summaries, and overdue user reports
- `/ai` — Gemini-powered workout analysis and weekly plan generation
- `/bot` — bot-only endpoints for Telegram integration and service-authenticated requests

## Authentication

- User registration and login are handled under `/auth`
- Endpoints use JWT Bearer tokens from login/register responses
- Use `Authorize` in Swagger UI to set `Bearer <token>`
- `/bot/*` endpoints use a separate bot service token header `X-Bot-Token` for Telegram bot server-to-server access

## Live deployment

The API is deployed on Render:

- https://fittrack-api-ww6w.onrender.com/docs

The Telegram bot is deployed on Railway and runs continuously — try it at `@fittrackYbot`.

> Note: free-tier deployments may take 30–50 seconds to wake up after inactivity.

## Environment examples

Root `.env.example` includes the API backend variables.

Bot `bot/.env.example` includes the Telegram bot variables.

## License / Author

Built by `lumis-code`.
