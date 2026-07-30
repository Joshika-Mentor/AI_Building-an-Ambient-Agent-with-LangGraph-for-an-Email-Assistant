# 🛡️ ThreatLens AI

**AI-Powered Malware Classification & Threat Detection Platform**

ThreatLens AI analyzes suspicious files, classifies malware using machine learning, and provides real-time threat intelligence for security operations.

## 🏗️ Architecture

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15 + Tailwind CSS + TypeScript |
| **Backend** | FastAPI (Python 3.12) |
| **PostgreSQL** | Users, roles, analyses, alerts |
| **MongoDB** | Detection logs, threat reports |
| **Redis** | Cache, sessions, rate limiting |
| **ML Engine** | Scikit-learn (Random Forest) |
| **File Analysis** | pefile, YARA rules |

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16
- MongoDB 7 (optional)
- Redis 7 (optional)

### Option 1: Docker Compose (Recommended)

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
cp .env.example .env           # Edit with your database URLs
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
threatlens-ai/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/      # REST endpoints
│   │   ├── core/     # Config, security, database
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   ├── ml/       # ML pipeline
│   │   ├── yara_rules/ # YARA detection rules
│   │   └── utils/    # Utilities
│   └── uploads/      # File storage
├── frontend/         # Next.js frontend
│   ├── app/          # Pages (App Router)
│   ├── components/   # React components
│   ├── hooks/        # Custom hooks
│   ├── lib/          # API client, utilities
│   └── types/        # TypeScript types
└── docker-compose.yml
```

## 🔐 Roles & Permissions

| Role | Upload | Analyze | Monitor | Manage Users |
|------|:---:|:---:|:---:|:---:|
| Security Analyst | ✅ | ✅ | ✅ | ❌ |
| SOC Team Member | ❌ | ❌ | ✅ | ❌ |
| Administrator | ✅ | ✅ | ✅ | ✅ |
| Researcher | ✅ | ✅ | ✅ | ❌ |

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Authenticate user |
| POST | `/api/v1/files/upload` | Upload & analyze file |
| GET | `/api/v1/files/{id}` | Get analysis results |
| GET | `/api/v1/analytics/overview` | Dashboard stats |

Full API documentation available at `/docs` when the backend is running.

## 🛠️ Tech Stack

- **FastAPI** — High-performance async Python API
- **SQLAlchemy** — Async ORM for PostgreSQL
- **Pydantic** — Data validation and serialization
- **JWT** — Stateless authentication
- **pefile** — PE executable analysis
- **YARA** — Pattern matching for malware detection
- **Scikit-learn** — Machine learning classification
- **Next.js** — React framework with App Router
- **Tailwind CSS** — Utility-first CSS
- **Recharts** — Data visualization
- **Zustand** — State management
- **Docker** — Containerized deployment
