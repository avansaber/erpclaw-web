# ERPClaw Web — Browser Dashboard for ERPClaw

A modern web dashboard for [ERPClaw](https://github.com/avansaber/erpclaw), the AI-native ERP built on [OpenClaw](https://openclaw.org). Provides a full browser-based interface for managing all ERP entities — customers, sales orders, invoices, inventory, payments, HR, and more.

## Features

- **Universal data tables** — auto-generated from ERPClaw's SKILL.md definitions, no per-module configuration
- **Live data** — real-time entity lists with pagination, filtering, and status indicators
- **Detail panels** — SAP Fiori-style side panels for viewing and acting on records
- **Action execution** — submit, cancel, and create derived documents directly from the UI
- **AI chat** — natural language queries against your ERP data (e.g., "show me overdue invoices")
- **Multi-vertical** — supports all 44 ERPClaw modules including Healthcare, Education, Retail, Construction, and more
- **Dark/light themes** — automatic theme switching with accent color customization
- **WebSocket updates** — live data refresh when records change
- **JWT authentication** — secure login with token refresh and role-based access

## Architecture

```
Browser (SvelteKit)     FastAPI Backend        ERPClaw Skills
┌──────────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ SvelteKit 5      │──▶│ /api/action/*   │──▶│ db_query.py      │
│ Tailwind CSS 4   │   │ /api/layout/*   │   │ --action {name}  │
│ TypeScript        │   │ /api/chat       │   │                  │
│ adapter-static   │   │ /ws             │   │ SQLite DB        │
└──────────────────┘   └─────────────────┘   └──────────────────┘
     Static files          Python 3.10+         ~/.openclaw/erpclaw/
     served by nginx       uvicorn               data.sqlite
```

**Frontend**: SvelteKit 5 with Svelte 5 runes, compiled to static files via `adapter-static`, served by nginx.

**Backend**: FastAPI application that proxies action calls to ERPClaw skill scripts, handles authentication, and provides real-time WebSocket updates.

**Data**: All data lives in ERPClaw's single SQLite database. The web dashboard reads and writes through ERPClaw's action system — it never touches the database directly.

## Prerequisites

- [ERPClaw](https://github.com/avansaber/erpclaw) installed via OpenClaw (`clawhub install erpclaw`)
- Node.js 18+ (for building the frontend)
- Python 3.10+ (for the API backend)

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/avansaber/erpclaw-web.git
cd erpclaw-web
npm install
pip install -r api/requirements.txt
```

### 2. Run in development

```bash
# Terminal 1: Frontend (hot reload)
npm run dev

# Terminal 2: API backend
uvicorn api.main:app --host 0.0.0.0 --port 8100 --reload
```

The frontend runs on `http://localhost:5173` and proxies API calls to the backend on port 8100.

### 3. First login

On first visit, you'll be prompted to create an admin account. This sets up JWT authentication for all subsequent access.

## Production Deployment

See `deploy/` for production configuration:

- **`nginx-erpclaw-web.conf`** — nginx config for serving static files + reverse proxying to the API
- **`erpclaw-web-api.service`** — systemd service for the FastAPI backend
- **`setup.sh`** — automated deployment script

### Build for production

```bash
npm run build   # Outputs to build/
```

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ERPCLAW_ENV` | `development` | Set to `production` to disable Swagger docs |
| `ALLOWED_ORIGINS` | `http://localhost:5173,...` | Comma-separated CORS origins |
| `JWT_SECRET` | (auto-generated) | Secret key for JWT tokens |

## Project Structure

```
erpclaw-web/
├── src/                    # SvelteKit frontend
│   ├── routes/             # Pages: dashboard, entity lists, login, setup
│   ├── lib/                # Components, stores, API client, auth, WebSocket
│   └── app.css             # Tailwind CSS entry
├── api/                    # FastAPI backend
│   ├── main.py             # App entry, CORS, middleware
│   ├── auth/               # JWT auth, login, passwords
│   ├── chat.py             # AI chat endpoint
│   ├── layout.py           # Dynamic layout generation from SKILL.md
│   ├── db.py               # Database connection helpers
│   ├── ws.py               # WebSocket handler
│   └── layouts/            # UI.yaml layout definitions per vertical
├── deploy/                 # Production deployment configs
├── schema/                 # Schema definitions
└── scripts/                # Build and utility scripts
```

## How It Works with ERPClaw

ERPClaw Web is a **companion** to the core ERPClaw skill. It does not replace the conversational AI interface — it adds a visual dashboard on top.

1. **ERPClaw** handles all business logic: creating customers, posting invoices, GL entries, inventory moves, payroll runs
2. **ERPClaw Web** provides a browser UI that calls ERPClaw's actions through the API backend
3. Both interfaces share the same database — changes made via chat or web UI are immediately visible in both

You can use ERPClaw purely through chat (Telegram, CLI), purely through the web dashboard, or both simultaneously.

## Related Projects

- **[ERPClaw](https://github.com/avansaber/erpclaw)** — Core ERP skill (371+ actions, 14 domains)
- **[WebClaw](https://github.com/avansaber/webclaw)** — Alternative web dashboard (universal OpenClaw skill viewer)
- **[OpenClaw](https://openclaw.org)** — The AI bot platform ERPClaw runs on
- **[All modules](https://github.com/avansaber)** — 44 modules across 14 repos

## License

MIT License — Copyright (c) 2026 AvanSaber
