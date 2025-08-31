# DevOps Requirements

## Overview
Comprehensive DevOps strategy for the DeepInsight system covering local development setup, containerization, CI/CD pipelines, and deployment to both local environments and Heroku cloud platform. This document provides scripts and configurations for reliable, automated deployment processes.

## Development Environment Setup

### Prerequisites
- **Node.js**: 18.0+
- **Python**: 3.11+
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Git**: 2.40+

### Local Development Scripts

#### Environment Setup Script
```bash
#!/bin/bash
# scripts/setup-dev.sh

set -e  # Exit on any error

echo "🚀 Setting up DeepInsight development environment..."

# Check prerequisites
check_prerequisite() {
    local cmd=$1
    local name=$2
    local min_version=$3
    
    if ! command -v $cmd &> /dev/null; then
        echo "❌ $name is not installed. Please install $name $min_version or higher."
        exit 1
    fi
    
    echo "✅ $name is installed"
}

echo "📋 Checking prerequisites..."
check_prerequisite "node" "Node.js" "18.0"
check_prerequisite "python3" "Python" "3.11"
check_prerequisite "docker" "Docker" "24.0"
check_prerequisite "docker-compose" "Docker Compose" "2.20"

# Create environment files
create_env_files() {
    echo "📝 Creating environment configuration files..."
    
    # Backend .env
    if [ ! -f "backend/.env" ]; then
        cp backend/.env.example backend/.env
        echo "✅ Created backend/.env from template"
    fi
    
    # Frontend .env
    if [ ! -f "frontend/.env" ]; then
        cp frontend/.env.example frontend/.env
        echo "✅ Created frontend/.env from template"
    fi
    
    echo "⚠️  Please update the .env files with your API keys and configuration"
}

# Setup backend
setup_backend() {
    echo "🐍 Setting up Python backend..."
    cd backend
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Created Python virtual environment"
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo "✅ Installed Python dependencies"
    cd ..
}

# Setup frontend
setup_frontend() {
    echo "⚛️  Setting up React frontend..."
    cd frontend
    
    # Install dependencies
    npm install
    
    echo "✅ Installed Node.js dependencies"
    cd ..
}

# Setup database
setup_database() {
    echo "🗄️  Setting up database..."
    
    # Start PostgreSQL and Redis containers
    docker-compose -f docker-compose.dev.yml up -d postgres redis
    
    # Wait for database to be ready
    echo "⏳ Waiting for database to be ready..."
    sleep 10
    
    # Run database migrations
    cd backend
    source venv/bin/activate
    alembic upgrade head
    
    echo "✅ Database setup complete"
    cd ..
}

# Main setup flow
main() {
    create_env_files
    setup_backend
    setup_frontend
    setup_database
    
    echo ""
    echo "🎉 Development environment setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Update your .env files with API keys"
    echo "2. Run 'npm run dev' to start the development server"
    echo "3. Open http://localhost:3000 in your browser"
}

main
```

#### Development Server Script
```bash
#!/bin/bash
# scripts/dev-server.sh

set -e

echo "🚀 Starting DeepInsight development servers..."

# Function to cleanup background processes
cleanup() {
    echo "🛑 Shutting down servers..."
    jobs -p | xargs -r kill
    docker-compose -f docker-compose.dev.yml down
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start infrastructure services
echo "🗄️  Starting database and cache services..."
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Start backend server
echo "🐍 Starting Python backend..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend server  
echo "⚛️  Starting React frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Start background worker (if using Celery)
echo "👷 Starting background worker..."
cd backend
source venv/bin/activate
celery -A app.worker worker --loglevel=info &
WORKER_PID=$!
cd ..

echo ""
echo "🎉 All services started successfully!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for any background job to finish
wait
```

### Docker Configuration

#### Development Docker Compose
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: deepinsight_dev
      POSTGRES_USER: deepinsight
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U deepinsight"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Optional: Neo4j for development
  neo4j:
    image: neo4j:5-community
    environment:
      NEO4J_AUTH: neo4j/dev_password
      NEO4J_PLUGINS: '["graph-data-science"]'
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs

volumes:
  postgres_data:
  redis_data:
  neo4j_data:
  neo4j_logs:
```

#### Production Dockerfile - Backend
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Create and set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Create directories for uploads and logs
RUN mkdir -p /app/uploads /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
```

#### Production Dockerfile - Frontend
```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create nginx user
RUN addgroup -g 101 -S nginx && \
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

#### Nginx Configuration
```nginx
# frontend/nginx.conf
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log  /var/log/nginx/error.log warn;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    server {
        listen 80;
        server_name _;
        
        root /usr/share/nginx/html;
        index index.html;
        
        # Handle client-side routing
        location / {
            try_files $uri $uri/ /index.html;
        }
        
        # API proxy
        location /api/ {
            proxy_pass http://backend:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }
        
        # WebSocket proxy
        location /ws/ {
            proxy_pass http://backend:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Static assets with caching
        location /static/ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

## Continuous Integration/Continuous Deployment

### GitHub Actions Workflow
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test-backend:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_USER: test_user
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
          
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
            
      - name: Install dependencies
        run: |
          cd backend
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          
      - name: Run linting
        run: |
          cd backend
          black --check .
          isort --check-only .
          flake8 .
          
      - name: Run type checking
        run: |
          cd backend
          mypy app/
          
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd backend
          pytest --cov=app --cov-report=xml tests/
          
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: backend

  test-frontend:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
          
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          
      - name: Run linting
        run: |
          cd frontend
          npm run lint
          
      - name: Run type checking
        run: |
          cd frontend
          npm run type-check
          
      - name: Run unit tests
        run: |
          cd frontend
          npm run test -- --coverage
          
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./frontend/coverage/lcov.info
          flags: frontend

  security-scan:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
          
      - name: Upload Trivy scan results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
          
      - name: Run Snyk security scan
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

  build-and-push:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend, security-scan]
    if: github.ref == 'refs/heads/main'
    
    permissions:
      contents: read
      packages: write
      
    strategy:
      matrix:
        service: [backend, frontend]
        
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/${{ matrix.service }}
          tags: |
            type=ref,event=branch
            type=sha
            type=raw,value=latest,enable={{is_default_branch}}
            
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./${{ matrix.service }}
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-heroku:
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: ${{ secrets.HEROKU_APP_NAME }}
          heroku_email: ${{ secrets.HEROKU_EMAIL }}
          dockerfile: Dockerfile.heroku
          
      - name: Run post-deployment tests
        run: |
          sleep 30  # Wait for deployment
          curl -f https://${{ secrets.HEROKU_APP_NAME }}.herokuapp.com/health || exit 1
```

## Heroku Deployment

### Heroku Configuration

#### heroku.yml
```yaml
# heroku.yml
build:
  docker:
    web: Dockerfile.heroku
    worker: Dockerfile.heroku
    
release:
  image: web
  command:
    - python manage.py migrate

run:
  web: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
  worker: celery -A app.worker worker --loglevel=info
```

#### Heroku Dockerfile
```dockerfile
# Dockerfile.heroku
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy backend requirements and install dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --upgrade pip && \
    pip install -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy frontend build (assuming built in CI)
COPY frontend/dist/ ./frontend/dist/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Command to run
CMD cd backend && gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

#### Heroku Deployment Script
```bash
#!/bin/bash
# scripts/deploy-heroku.sh

set -e

echo "🚀 Deploying DeepInsight to Heroku..."

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is logged in
if ! heroku auth:whoami &> /dev/null; then
    echo "❌ Please login to Heroku first: heroku login"
    exit 1
fi

# Configuration
APP_NAME=${1:-deepinsight-app}
REGION=${2:-us}

echo "📋 App Name: $APP_NAME"
echo "🌍 Region: $REGION"

# Create Heroku app if it doesn't exist
if ! heroku apps:info --app $APP_NAME &> /dev/null; then
    echo "📱 Creating Heroku app..."
    heroku create $APP_NAME --region $REGION
    echo "✅ App created successfully"
else
    echo "✅ App already exists"
fi

# Set stack to container
echo "🐳 Setting stack to container..."
heroku stack:set container --app $APP_NAME

# Configure environment variables
echo "🔧 Setting up environment variables..."
heroku config:set \
    ENVIRONMENT=production \
    DEBUG=false \
    SECRET_KEY=$(openssl rand -base64 32) \
    --app $APP_NAME

# Add required add-ons
echo "🔌 Adding Heroku add-ons..."
heroku addons:create heroku-postgresql:essential-0 --app $APP_NAME
heroku addons:create heroku-redis:mini --app $APP_NAME

# Configure buildpacks (if not using Docker)
# heroku buildpacks:add heroku/nodejs --app $APP_NAME
# heroku buildpacks:add heroku/python --app $APP_NAME

# Deploy the application
echo "🚀 Deploying application..."
git push heroku main

# Run database migrations
echo "🗄️  Running database migrations..."
heroku run python backend/alembic upgrade head --app $APP_NAME

# Scale dynos
echo "📊 Scaling dynos..."
heroku ps:scale web=1 worker=1 --app $APP_NAME

# Open the application
echo "🌐 Opening application..."
heroku open --app $APP_NAME

echo "✅ Deployment completed successfully!"
echo "📱 App URL: https://$APP_NAME.herokuapp.com"
echo "📊 Logs: heroku logs --tail --app $APP_NAME"
```

### Environment Configuration

#### Environment Variables Script
```bash
#!/bin/bash
# scripts/setup-env-vars.sh

set -e

APP_NAME=${1:-deepinsight-app}

echo "🔧 Setting up environment variables for $APP_NAME..."

# Required environment variables
heroku config:set \
    ENVIRONMENT=production \
    DEBUG=false \
    SECRET_KEY=$(openssl rand -base64 32) \
    JWT_ALGORITHM=HS256 \
    ACCESS_TOKEN_EXPIRE_MINUTES=30 \
    --app $APP_NAME

# Database configuration (auto-configured by Heroku addon)
echo "✅ Database URL will be auto-configured by Heroku PostgreSQL addon"

# Redis configuration (auto-configured by Heroku addon)  
echo "✅ Redis URL will be auto-configured by Heroku Redis addon"

# API Keys (set these manually with your keys)
echo "⚠️  Please set your API keys manually:"
echo "heroku config:set ANTHROPIC_API_KEY=your_key --app $APP_NAME"
echo "heroku config:set OPENAI_API_KEY=your_key --app $APP_NAME"

# File upload configuration
heroku config:set \
    MAX_FILE_SIZE=104857600 \
    UPLOAD_DIR=/tmp/uploads \
    --app $APP_NAME

# Security configuration
heroku config:set \
    REQUIRE_HTTPS=true \
    SECURE_COOKIES=true \
    PASSWORD_MIN_LENGTH=12 \
    MAX_LOGIN_ATTEMPTS=5 \
    --app $APP_NAME

echo "✅ Environment variables configured"
```

## Monitoring & Logging

### Application Monitoring
```python
# backend/app/monitoring.py
import logging
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

# Structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.WriteLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Update metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(process_time)
        
        # Structured logging
        logger.info(
            "http_request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=process_time,
            user_agent=request.headers.get("user-agent"),
            remote_addr=request.client.host
        )
        
        return response

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("APP_VERSION", "unknown")
    }

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### Log Management Script
```bash
#!/bin/bash
# scripts/logs-management.sh

set -e

APP_NAME=${1:-deepinsight-app}
ACTION=${2:-tail}

case $ACTION in
    "tail")
        echo "📋 Tailing logs for $APP_NAME..."
        heroku logs --tail --app $APP_NAME
        ;;
    "download")
        echo "⬇️  Downloading logs for $APP_NAME..."
        heroku logs --num 1500 --app $APP_NAME > logs_$(date +%Y%m%d_%H%M%S).txt
        echo "✅ Logs saved to logs_$(date +%Y%m%d_%H%M%S).txt"
        ;;
    "errors")
        echo "❌ Showing error logs for $APP_NAME..."
        heroku logs --tail --app $APP_NAME | grep -i error
        ;;
    "performance")
        echo "📊 Showing performance logs for $APP_NAME..."
        heroku logs --tail --app $APP_NAME | grep -E "(duration|memory|cpu)"
        ;;
    *)
        echo "Usage: $0 <app-name> [tail|download|errors|performance]"
        exit 1
        ;;
esac
```

## Backup & Recovery

### Database Backup Script
```bash
#!/bin/bash
# scripts/backup-db.sh

set -e

APP_NAME=${1:-deepinsight-app}
BACKUP_NAME=${2:-backup_$(date +%Y%m%d_%H%M%S)}

echo "💾 Creating database backup for $APP_NAME..."

# Create backup
heroku pg:backups:capture --app $APP_NAME

# Download backup
heroku pg:backups:download --app $APP_NAME

# Rename backup file
mv latest.dump "${BACKUP_NAME}.dump"

echo "✅ Database backup saved as ${BACKUP_NAME}.dump"

# Optional: Upload to cloud storage
# aws s3 cp "${BACKUP_NAME}.dump" s3://your-backup-bucket/
```

### Restore Script
```bash
#!/bin/bash
# scripts/restore-db.sh

set -e

APP_NAME=${1}
BACKUP_FILE=${2}

if [ -z "$APP_NAME" ] || [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <app-name> <backup-file>"
    exit 1
fi

echo "⚠️  This will restore the database for $APP_NAME from $BACKUP_FILE"
echo "⚠️  This action is DESTRUCTIVE and cannot be undone!"
read -p "Are you sure? (yes/no): " -r
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo "🔄 Restoring database..."

# Reset database
heroku pg:reset DATABASE_URL --confirm $APP_NAME --app $APP_NAME

# Restore from backup
heroku pg:psql --app $APP_NAME < $BACKUP_FILE

echo "✅ Database restored successfully"
```

## Troubleshooting Scripts

### Health Check Script
```bash
#!/bin/bash
# scripts/health-check.sh

set -e

APP_NAME=${1:-deepinsight-app}
BASE_URL="https://${APP_NAME}.herokuapp.com"

echo "🔍 Health checking $APP_NAME..."

# Test main health endpoint
echo "🏥 Testing health endpoint..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health")

if [ "$HEALTH_STATUS" -eq 200 ]; then
    echo "✅ Health endpoint is responding"
else
    echo "❌ Health endpoint returned status: $HEALTH_STATUS"
    exit 1
fi

# Test API endpoint
echo "🔌 Testing API endpoint..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/v1/")

if [ "$API_STATUS" -eq 200 ] || [ "$API_STATUS" -eq 404 ]; then
    echo "✅ API endpoint is accessible"
else
    echo "❌ API endpoint returned status: $API_STATUS"
fi

# Test database connectivity
echo "🗄️  Testing database connectivity..."
heroku run python -c "
import os
import asyncpg
import asyncio

async def test_db():
    try:
        conn = await asyncpg.connect(os.environ['DATABASE_URL'])
        await conn.execute('SELECT 1')
        await conn.close()
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        exit(1)

asyncio.run(test_db())
" --app $APP_NAME

echo "🎉 All health checks passed!"
```

This comprehensive DevOps setup provides automated, reliable deployment pipelines for both local development and production environments on Heroku, with proper monitoring, logging, and recovery procedures.