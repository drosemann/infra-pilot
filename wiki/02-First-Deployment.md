# First Deployment

## 1. Configure and Log In

```bash
# Point the CLI at the panel API (default http://localhost:3001)
export INFRA_PASSENGER_API_URL=http://localhost:3001
infra-passenger login <your-api-key>
```

## 2. Create a Server

```bash
infra-passenger server create my-first-server --image nginx:latest --memory 2048
```

## 3. Check Status and Use It

```bash
infra-passenger server status <server-id>
infra-passenger server start <server-id>
infra-passenger server stop <server-id>
infra-passenger server restart <server-id>
infra-passenger logs fetch <server-id> --lines 50
```

You'll see `running` when it's ready.

## 4. Clean Up

```bash
infra-passenger server delete <server-id>
```

## Via the Web Panel

Open http://localhost:5173 and click **"Server erstellen"**.

Not sure what to expect? Preview the dashboard, monitoring, and
application views in `docs/screenshots/` of the repository.

---

*See [CLI Reference](05-CLI-Reference) for full command details.*
