# Teacher Assistant — AI-Powered Classroom Tool

A full-stack web application that helps teachers manage live classes through an AI assistant integrated with Telegram. Teachers can upload presentations, run live class sessions, receive real-time student questions via a Telegram bot, and get AI-generated answers, analogies, and examples using Google Gemini.

## Features

- **Live Class Sessions** — Start and manage class instances tied to uploaded presentations
- **Telegram Bot Integration** — Students interact with the bot to ask questions during class
- **AI-Powered Responses** — Google Gemini generates answers, analogies, and examples in context
- **Real-Time Sync** — WebSocket-based synchronization between teacher dashboard and student view
- **Presentation Viewer** — Slide-by-slide navigation with Telegram bot awareness of current slide
- **Firebase Authentication** — Google Sign-In and email/password login for teachers
- **REST API** — Fully documented endpoints for classes, instances, questions, and sync

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask, SQLAlchemy, Gunicorn |
| Database | PostgreSQL 15 |
| Frontend | React 19, Vite, Tailwind CSS |
| Auth | Firebase Admin SDK + Firebase Auth |
| AI | Google Gemini API via Google AI Studio (GCP) |
| Bot | python-telegram-bot 21 (webhook mode) |
| Real-Time | Flask-SocketIO, Redis |
| Containerization | Docker, Docker Compose |
| Cloud | AWS EC2 (app server), GCP (Gemini AI Studio) |
| Web Server | Nginx (frontend reverse proxy) |

## Architecture

```
┌─────────────────────────────────────────┐
│              React Frontend             │
│   (Vite + Tailwind + Socket.IO client) │
└──────────────────┬──────────────────────┘
                   │ HTTP / WebSocket
┌──────────────────▼──────────────────────┐
│            Flask Backend (API)          │
│  ┌─────────────┐  ┌──────────────────┐ │
│  │  REST API   │  │  Telegram Webhook│ │
│  └──────┬──────┘  └────────┬─────────┘ │
│         │                  │           │
│  ┌──────▼──────────────────▼─────────┐ │
│  │         Service Layer             │ │
│  │  GeminiService  PresentationSvc   │ │
│  │  SocketEmitter  TelegramBot       │ │
│  └──────┬────────────────────────────┘ │
│         │                              │
│  ┌──────▼──────┐   ┌────────────────┐ │
│  │ PostgreSQL  │   │  Redis (pub/sub)│ │
│  └─────────────┘   └────────────────┘ │
└─────────────────────────────────────────┘
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development without Docker)
- Python 3.11+ (for local backend development without Docker)

### Environment Variables

Copy the example files and fill in your credentials:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Key variables to configure:

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Token from @BotFather |
| `GEMINI_API_KEY` | Google AI Studio API key |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase service account JSON |
| `VITE_FIREBASE_API_KEY` | Firebase web app config |
| `POSTGRES_PASSWORD` | Database password |
| `SECRET_KEY` | Flask secret key (random string) |

### Run with Docker (recommended)

```bash
# Start all services (backend, database, frontend)
docker compose up -d

# Rebuild images after code changes
docker compose up --build

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

Services available at:
- Frontend: `http://localhost:80` (Nginx) or `http://localhost:5173` (dev)
- Backend API: `http://localhost:5000`
- PostgreSQL: `localhost:5432`

### Run Without Docker

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── controllers/     # Request handlers (auth, classes, instances, questions, sync, telegram)
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routes/          # Flask Blueprints
│   │   ├── services/        # Business logic (Gemini, Telegram bot, Socket.IO, presentations)
│   │   └── middleware/      # Firebase auth middleware
│   ├── Dockerfile
│   ├── requirements.txt
│   └── docker-compose.yml
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Route-level views
│   │   ├── services/        # API client (api.js)
│   │   ├── contexts/        # Firebase & Socket.IO React contexts
│   │   └── lib/             # Firebase initialization
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── docker-compose.prod.yml
└── setup_webhook_render.py  # Helper script to register Telegram webhook
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register teacher account |
| POST | `/api/auth/login` | Login |
| GET | `/api/classes` | List all classes |
| POST | `/api/classes` | Create class (upload PDF) |
| GET | `/api/classes/:id/instances` | List class instances |
| POST | `/api/classes/:id/instances` | Start new instance |
| POST | `/api/classes/:id/instances/:id/end` | End instance |
| GET | `/api/sync/:code/status` | Get live session status (no auth) |
| POST | `/api/sync/:code/control` | Control presentation (no auth) |
| POST | `/api/telegram/webhook` | Telegram webhook receiver |

## Database

Connect to the running PostgreSQL container:

```bash
docker exec -it pds_postgres psql -U postgres -d teacher_assistant_db
```

Backup and restore:

```bash
# Backup
docker exec pds_postgres pg_dump -U postgres teacher_assistant_db > backup.sql

# Restore
cat backup.sql | docker exec -i pds_postgres psql -U postgres -d teacher_assistant_db
```

## Telegram Webhook Setup

For production deployments, register the webhook using the included script:

```bash
# Set environment variables first
export TELEGRAM_BOT_TOKEN=your_token
export BACKEND_URL=https://your-server.com

python setup_webhook_render.py
```

## Useful Commands

```bash
# Check running containers
docker compose ps

# Restart a single service
docker compose restart backend

# Rebuild and restart from scratch (clears volumes)
docker compose down -v && docker compose up --build

# Frontend linting
cd frontend && npm run lint

# Production build
cd frontend && npm run build
```

## Cloud Infrastructure

The production deployment uses two cloud providers:

- **AWS EC2** — Hosts the entire application stack (Flask backend, PostgreSQL, Redis, and Nginx-served React frontend) via Docker Compose on a Linux instance.
- **GCP — Google AI Studio** — Provides the Gemini API used to generate AI responses, analogies, and examples in real time during class sessions.
