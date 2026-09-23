# First Deployment

## 1. Configure and Log In

```bash
# Point the CLI at the panel API (default http://localhost:3001)
export IPILOT_API_URL=http://localhost:3001
ipilot login <your-api-key>
```

## 2. Create a Server

```bash
ipilot server create my-first-server --image nginx:latest --memory 2048
```

## 3. Check Status and Use It

```bash
ipilot server status <server-id>
ipilot server start <server-id>
ipilot server stop <server-id>
ipilot server restart <server-id>
ipilot logs fetch <server-id> --lines 50
```

You'll see `running` when it's ready.

## 4. Clean Up

```bash
ipilot server delete <server-id>
```

## Via the Web Panel

Open http://localhost:5173 and click **"Server erstellen"**.

Not sure what to expect? Preview the dashboard, monitoring, and
application views in `docs/screenshots/` of the repository.

---

*See [CLI Reference](05-CLI-Reference) for full command details.*
