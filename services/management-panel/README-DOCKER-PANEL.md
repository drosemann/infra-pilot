# docker panel - getting started

this is a self-hosted docker management panel with personal mode (simple) and hosting business mode (full-featured) support.

## quick start

### requirements

- node.js 18+ and npm
- docker and docker daemon (running locally or remotely)
- supabase (self-hosted via docker compose recommended)

### installation

• clone and install dependencies
   ```bash
   cd services/management-panel
   npm install
   ```

• set up environment
   ```bash
   cp .env.local.example .env.local
   ```

• configure supabase (optional if using self-hosted)
   
   the easiest way is to use supabase docker compose:
   ```bash
   # Pull docker-compose from https://github.com/supabase/supabase/tree/master/docker
   # Edit docker-compose.yml with your JWT secret
   docker-compose -f docker-compose.yml up -d
   ```

   then connect to the local instance:
   ```
   VITE_SUPABASE_URL=http://localhost:54321
   VITE_SUPABASE_ANON_KEY=<your-anon-key>
   ```

• initialize database
   ```bash
   # Login to Supabase dashboard (http://localhost:3000) with default credentials
   # Navigate to SQL Editor
   # Copy contents from db/schema.sql and execute
   ```

• start development servers
   ```bash
   npm run dev
   ```

   this starts:
   - frontend: http://localhost:5173
   - backend api: http://localhost:3001

• first-time setup
   - visit http://localhost:5173
   - select personal mode (or business mode)
   - create your admin account
   - done! you're ready to manage docker apps

### production deployment

• build
   ```bash
   npm run build
   ```

• environment setup
   ```bash
   # Point to your production Supabase instance
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_ANON_KEY=<production-key>
   VITE_API_URL=https://api.yourdomain.com
   ```

• run backend
   ```bash
   node server/index.ts  # Daemonize with PM2, systemd, or Docker
   ```

• serve frontend
   ```bash
   npx serve dist/  # Or use Nginx, Vercel, etc.
   ```

## project structure

```
services/management-panel/
├── public/                  # Static assets
├── src/
│   ├── pages/              # Page components (Setup, Dashboard, AppForm, AppDetail)
│   ├── components/         # Reusable components (MainLayout, etc.)
│   ├── lib/
│   │   ├── api.ts         # API client
│   │   ├── auth.ts        # Supabase auth helpers
│   │   └── types.ts       # Types and feature gates
│   ├── App.tsx            # Main app with routing
│   └── main.tsx           # React entry point
├── server/
│   └── index.ts           # Express backend API
├── db/
│   └── schema.sql         # PostgreSQL schema for Supabase
├── docs/
│   └── PERSONAL_MODE.md   # Mode architecture documentation
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## features

### personal mode (default)

• docker app management
- create, read, update, delete docker applications
- pull images from docker hub or custom registries
- port mapping (host ↔ container)
- environment variable configuration
- volume/mount management
- memory and cpu limits

• container controls
- start/stop/restart containers
- view container status in real-time
- stream logs (paginated retrieval)
- container health polling

• dashboard
- quick overview of app status
- total, running, stopped, error counts
- click-to-manage app list
- user avatar (identicon): deterministisches profilbild aus der user-id via jdenticon

### hosting business mode (coming soon)

• customer account management
• plans and pricing tiers
• billing integration hooks
• white-label branding
• team and staff rbac
• audit logging

for details, see [personal mode](docs/PERSONAL_MODE.md)

## api overview

all api calls require bearer token in `authorization` header after setup.

### setup endpoints

```
GET  /api/setup/status         # Check if initialized
POST /api/setup/init           # Initialize with mode + admin account
```

### docker app endpoints

```
GET    /api/apps               # List user's apps
POST   /api/apps               # Create new app
GET    /api/apps/:appId        # Get app details
PATCH  /api/apps/:appId        # Update app settings
DELETE /api/apps/:appId        # Delete app
```

### container control

```
POST   /api/apps/:appId/start      # Start container
POST   /api/apps/:appId/stop       # Stop container
POST   /api/apps/:appId/restart    # Restart container
GET    /api/apps/:appId/logs       # Get logs (paginated)
```

### user & config

```
GET    /api/user               # Get current user profile
GET    /api/config/mode        # Get setup mode
GET    /health                 # Health check
```

## docker integration (todo)

currently, the backend stores app configurations but doesn't actually pull/run containers yet.

to add docker integration:

• install docker sdk
   ```bash
   npm install dockerode
   ```

• update backend to actually interact with docker api:
   ```typescript
   // server/index.ts
   import Docker from 'dockerode';
   
   const docker = new Docker({
     socketPath: process.env.DOCKER_SOCKET || '/var/run/docker.sock'
   });
   ```

• implement container operations in start/stop/restart/create routes

see [docker integration](docs/DOCKER_INTEGRATION.md) for detailed implementation guide (todo).

## mode architecture

### personal mode
- single-user self-hosting focus
- simple, minimal ui
- no customer/billing features
- perfect for hobby projects and home labs

### business mode
- multi-customer hosting platform
- full admin panel with business features
- billing hooks and white-label support
- professional hosting company ready

you can start in personal mode and upgrade to business mode later without losing data.

see [personal mode](docs/PERSONAL_MODE.md) for complete architecture details.

## development

### run tests (todo)
```bash
npm run test
```

### linting
```bash
npm run lint
```

### build
```bash
npm run build
```

### preview production build
```bash
npm run preview
```

## troubleshooting

### "failed to check setup status"
- ensure backend api is running on `http://localhost:3001`
- check `vite_api_url` in `.env.local`

### "connection refused" to supabase
- verify supabase is running (`docker ps`)
- check `vite_supabase_url` points to correct instance
- ensure jwt secret is configured

### "not authenticated" after setup
- token might have expired; reload page
- check localstorage has `sb_access_token`
- verify backend validates token correctly

### docker operations fail
- ensure docker daemon is running
- check `docker_host` environment variable
- verify permissions on docker.sock (if using unix socket)

## contributing

see [contributing](../../../CONTRIBUTING.md) in repository root.

## license

mit - see [license](../../../LICENSE) in repository root.

## support

- [mode architecture docs](docs/PERSONAL_MODE.md)
- [github issues](https://github.com/DaaanielTV/infra-pilot/issues)
- [discussions](https://github.com/DaaanielTV/infra-pilot/discussions)
