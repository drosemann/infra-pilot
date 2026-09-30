# Management Panel Docker guide

This is the container-oriented companion to [README.md](README.md). The repository root Compose file is the supported
way to run the panel with its PostgreSQL and Redis dependencies.

## Start the complete local stack

```bash
# From the repository root
cp .env.example .env
bash scripts/generate-env.sh
docker compose up -d management-panel
```

Compose starts dependencies declared for `management-panel` and publishes the Vite frontend on `http://localhost:5173`
and the backend on `http://localhost:3001`. Confirm readiness with:

```bash
docker compose ps
docker compose logs -f management-panel
curl --fail http://localhost:3001/health
```

## Configuration boundary

Use the root `.env.example` for Compose values, especially `POSTGRES_PASSWORD`, `MANAGEMENT_FRONTEND_PORT`,
`MANAGEMENT_BACKEND_PORT`, and `CORS_ORIGINS`. The service-local `.env.example` is for running `npm run dev` without
Compose.

Supabase values (`VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`) are optional hosted-feature settings. They are not a
substitute for the PostgreSQL service started by this Compose project.

## Production notes

Build and deploy the production target with your normal container pipeline, set explicit non-placeholder secrets, and
terminate TLS at a reverse proxy or ingress. Do not expose a Docker socket or database port to untrusted users. The
backend health endpoint is `GET /health`; current API documentation is at `GET /api/openapi.json` and `GET /api/docs`.

## Related documentation

- [Panel development README](README.md)
- [Repository installation guide](../../wiki/01-Installation.md)
- [Configuration](../../wiki/03-Configuration.md)
- [Architecture](../../wiki/06-Architecture.md)
