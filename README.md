# PickleBuddy API

FastAPI backend for the PickleBuddy booking platform.

This repo is designed to work with the separate frontend repo, `picklebuddzy`, in one shared local workspace.

## Expected folder layout

Clone both repos into the same parent folder and keep these folder names:

```text
picklebuddy-workspace/
  picklebuddy-api/
  picklebuddzy/
```

The tracked Docker handoff file in this repo assumes that sibling layout.

## Run with Docker

From inside `picklebuddy-api`, run:

```powershell
docker compose -f docker-compose.workspace.yml up --build -d
```

Apps:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8001`
- Health: `http://localhost:8001/health`

Stop:

```powershell
docker compose -f docker-compose.workspace.yml down
```

Reset Docker database:

```powershell
docker compose -f docker-compose.workspace.yml down -v
```

## Run backend only without Docker

1. Create a virtual environment
2. Install dependencies
3. Copy `.env.example` to `.env`
4. Point `.env` at your MySQL server
5. Start the API

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## Environment

Example values are in [.env.example](./.env.example).

Important values:

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `ALLOWED_ORIGINS`

## Current scope

- Auth, roles, and token-based login
- Owner venue and court management
- Player venue browsing and booking flows
- Open play and whole-gym booking support
- Manual payment proof submission and owner-side approval review
- Admin and owner transaction/reporting endpoints currently used by the frontend

## Teammate handoff

Use [TEAM_SETUP.md](./TEAM_SETUP.md) for the exact GitHub handoff flow.
