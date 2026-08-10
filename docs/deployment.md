# FactGuard AI Deployment Documentation

## Local Development Setup

### 1. Backend Setup
```powershell
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Run uvicorn server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```powershell
# Navigate to frontend
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server
npm run dev
```

## Production Docker Deployment

Use the root `docker-compose.yml` to build and launch backend, frontend, PostgreSQL, and ChromaDB:

```powershell
docker-compose up --build -d
```
