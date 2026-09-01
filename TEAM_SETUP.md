# Team Setup

This is the exact handoff flow for the current split-repo setup.

## Repos

Your teammate needs both repositories:

- frontend repo: `picklebuddzy`
- backend repo: `picklebuddy-api`

They must be cloned into the same parent folder with those folder names.

## Clone

Example:

```powershell
mkdir C:\React\picklebuddy-workspace
cd C:\React\picklebuddy-workspace
git clone <backend-repo-url> picklebuddy-api
git clone <frontend-repo-url> picklebuddzy
```

## Start everything with Docker

From the backend repo:

```powershell
cd C:\React\picklebuddy-workspace\picklebuddy-api
docker compose -f docker-compose.workspace.yml up --build -d
```

Open:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8001`

## Development options

### Option 1: standard dev mode

Use this for faster UI work and normal local development:

Frontend:

```powershell
cd C:\React\picklebuddy-workspace\picklebuddzy
npm install
npm run dev
```

That command starts the frontend and the backend workflow currently wired for development.

### Option 2: Docker mode

Use this when the teammate needs the full stack exactly as deployed locally:

```powershell
cd C:\React\picklebuddy-workspace\picklebuddy-api
docker compose -f docker-compose.workspace.yml up --build -d
```

## Stop and reset

Stop containers:

```powershell
docker compose -f docker-compose.workspace.yml down
```

Reset Docker database:

```powershell
docker compose -f docker-compose.workspace.yml down -v
```

## Notes

- Docker MySQL is intentionally not exposed on Windows port `3306`, so it will not conflict with an existing local MySQL server.
- The SQL seed import runs when the Docker MySQL volume is first created.
- If folder names change, `docker-compose.workspace.yml` must be updated because the frontend build context is `../picklebuddzy`.
