# Railway Multi-Service Deployment Guide

## Overview

DeepInsight now uses Railway's recommended multi-service deployment architecture with separate services for frontend and backend components. This approach eliminates configuration conflicts and provides independent deployment cycles.

## Architecture

```
DeepInsight Repository (Monorepo)
├── frontend/              # React application
│   ├── nixpacks.toml      # Frontend build configuration
│   ├── railway.toml       # Frontend deployment settings
│   ├── start.sh           # Frontend startup script
│   └── ...
├── backend/               # FastAPI application
│   ├── nixpacks.toml      # Backend build configuration
│   ├── railway.toml       # Backend deployment settings
│   ├── startup.py         # Backend initialization script
│   └── ...
└── docs/                  # Documentation
```

## Railway Services Setup

### 1. Frontend Service: `deepinsight-frontend`

**Configuration:**
- **Root Directory:** `/frontend`
- **Builder:** nixpacks
- **Start Command:** `./start.sh`

**Environment Variables Required:**
```
REACT_APP_BACKEND_URL=https://your-backend-service.railway.app
```

**Build Process:**
1. Install Node.js dependencies (`npm install`)
2. Build React application (`npm run build`)
3. Serve static files with `serve`

### 2. Backend Service: `deepinsight-backend`

**Configuration:**
- **Root Directory:** `/backend`
- **Builder:** nixpacks
- **Start Command:** `python startup.py && uvicorn main:app --host 0.0.0.0 --port $PORT`

**Environment Variables Required:**
```
SECRET_KEY=your-secret-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key
DATABASE_URL=postgresql://user:pass@host:port/db  # Optional, defaults to SQLite
```

**Build Process:**
1. Install Python dependencies (`pip install -r requirements.txt`)
2. Run startup script to initialize directories
3. Start FastAPI server with uvicorn

## Deployment Instructions

### Initial Setup

1. **Create Frontend Service:**
   ```bash
   # In Railway dashboard
   # 1. Create new service: "deepinsight-frontend"
   # 2. Connect to GitHub repository
   # 3. Set root directory: "/frontend"
   # 4. Add environment variables
   ```

2. **Create Backend Service:**
   ```bash
   # In Railway dashboard
   # 1. Create new service: "deepinsight-backend"
   # 2. Connect to GitHub repository
   # 3. Set root directory: "/backend"
   # 4. Add environment variables
   ```

### Configuration Files

#### Frontend (`frontend/nixpacks.toml`)
```toml
[phases.setup]
nixPkgs = ["nodejs-18_x"]
nixOverlays = ["https://github.com/railwayapp/nix-npm-overlay/archive/main.tar.gz"]

[phases.install]
dependsOn = ["setup"]
cmds = ["npm install"]

[phases.build]
dependsOn = ["install"]  
cmds = ["npm run build"]

[start]
dependsOn = ["build"]
cmd = "npx --yes serve -s build -l $PORT"
```

#### Frontend (`frontend/railway.toml`)
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "./start.sh"
restartPolicyType = "always"
```

#### Backend (`backend/nixpacks.toml`)
```toml
[phases.setup]
nixPkgs = ["python311"]

[phases.build]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "python startup.py && uvicorn main:app --host 0.0.0.0 --port $PORT"
```

#### Backend (`backend/railway.toml`)
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python startup.py && uvicorn main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "always"
```

## Service Communication

### Frontend to Backend
The frontend service communicates with the backend using the `REACT_APP_BACKEND_URL` environment variable:

```javascript
// In React components
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
```

### CORS Configuration
The backend should include the frontend domain in its CORS settings:

```python
# In backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-service.railway.app",
        "http://localhost:3000"  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Environment Variables Setup

### Railway Environment Variables

1. **Frontend Service:**
   ```
   REACT_APP_BACKEND_URL=https://deepinsight-backend-production.railway.app
   ```

2. **Backend Service:**
   ```
   SECRET_KEY=your-generated-secret-key-32-chars-minimum
   ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
   DATABASE_URL=postgresql://username:password@host:port/database  # Optional
   PORT=8000  # Set automatically by Railway
   ```

### Generating Secret Key
```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Deployment Process

### Manual Deployment
1. Push changes to GitHub repository
2. Railway automatically detects changes and triggers deployments
3. Each service deploys independently based on file changes

### Watch Paths (Optional)
Configure watch paths to only trigger builds when specific files change:

**Frontend watch paths:**
- `frontend/**`
- `!backend/**`

**Backend watch paths:**
- `backend/**`
- `!frontend/**`

## Troubleshooting

### Common Issues

1. **Frontend shows backend errors:**
   - Check that root directory is set to `/frontend`
   - Verify nixpacks.toml is using Node.js, not Python

2. **Backend missing environment variables:**
   - Ensure all required environment variables are set
   - Check Railway service environment variables panel

3. **CORS errors:**
   - Verify frontend domain is in backend CORS origins
   - Check that `REACT_APP_BACKEND_URL` points to correct backend service

4. **Build failures:**
   - Check service logs in Railway dashboard
   - Verify configuration files are in correct directories

### Debugging Commands

```bash
# Check Railway CLI status
railway status

# View service logs
railway logs --service deepinsight-frontend
railway logs --service deepinsight-backend

# Test local builds
cd frontend && npm run build
cd backend && pip install -r requirements.txt && python startup.py
```

## Benefits of Multi-Service Architecture

1. **Independent Deployments:** Frontend and backend deploy separately
2. **Faster Build Times:** Only changed services rebuild
3. **Better Resource Management:** Each service can be scaled independently
4. **Clear Separation:** No configuration conflicts between services
5. **Environment Isolation:** Separate environment variables per service

## Migration Notes

### Changes Made

1. **Moved Configuration Files:**
   - `nixpacks.toml` → `backend/nixpacks.toml`
   - `railway.toml` → `backend/railway.toml`
   - Removed conflicting `railway-frontend.toml`

2. **Updated Path References:**
   - Removed `backend/` and `cd backend` from commands
   - Updated startup script directory references

3. **Cleaned Up Root Directory:**
   - Removed Heroku-specific files (`Procfile`, `requirements.txt`, `runtime.txt`)
   - Root directory now has no deployment configuration conflicts

### Rollback Plan
If issues arise, the previous configuration can be restored by:
1. Moving `backend/nixpacks.toml` and `backend/railway.toml` back to root
2. Restoring the single-service Railway configuration
3. Setting root directory to `/` for the single service

---

*Last updated: 2025-09-05*  
*Architecture: Multi-service Railway deployment*