# Backend Technical Requirements

## Overview
The DeepInsight backend is a high-performance FastAPI-based Python application that leverages LangGraph agents to create ontologies and extract structured data from unstructured documents. It provides comprehensive RESTful APIs, real-time WebSocket communication, and enterprise-grade security, resilience, and monitoring capabilities.

## Technology Stack

### Core Technologies
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **ASGI Server**: Uvicorn 0.24+ with Gunicorn for production
- **Dependency Injection**: FastAPI's built-in DI system with custom providers

### AI/ML Technologies
- **Agent Framework**: LangGraph 0.0.62+
- **LLM Integration**: LangChain 0.1.0+ with pluggable providers
- **Graph Extraction**: LangChain LLMGraphTransformer
- **Default LLM**: Claude Sonnet 4 (claude-sonnet-4-20250514)
- **Supported LLMs**: Anthropic Claude, OpenAI GPT-4, Cohere, local models

### Data & Validation
- **Validation**: Pydantic v2.5+ with custom validators
- **Database ORM**: SQLAlchemy 2.0+ with async support
- **Graph Databases**: Neo4j driver 5.14+, boto3 for Neptune
- **File Processing**: python-multipart, aiofiles, python-magic
- **Document Processing**: pymupdf, python-docx, markdown, beautifulsoup4

### Background Processing & Caching
- **Task Queue**: Celery 5.3+ with Redis/RabbitMQ broker
- **Caching**: Redis 5.0+ with clustering support
- **Scheduling**: APScheduler for periodic tasks
- **Job Monitoring**: Flower for Celery monitoring

### Monitoring & Observability
- **Metrics**: Prometheus client with custom metrics
- **Logging**: Structlog with JSON formatting
- **Tracing**: OpenTelemetry with Jaeger integration
- **Health Checks**: Custom health check framework
- **APM**: Integration with DataDog/New Relic (optional)

## Application Architecture

### Project Structure
```
backend/
├── app/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py              # Base agent class
│   │   ├── ontology_agent.py    # Ontology creation agent
│   │   ├── extraction_agent.py  # Data extraction agent
│   │   ├── chunking_agent.py    # Document chunking agent
│   │   └── deduplication_agent.py
│   ├── api/
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── documents.py
│   │   │   ├── ontologies.py
│   │   │   ├── extractions.py
│   │   │   ├── databases.py
│   │   │   └── health.py
│   │   ├── websocket.py
│   │   └── middleware.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Enhanced configuration
│   │   ├── security.py          # Security utilities
│   │   ├── dependencies.py      # Dependency injection
│   │   ├── exceptions.py        # Custom exceptions
│   │   ├── circuit_breaker.py   # Circuit breaker implementation
│   │   ├── monitoring.py        # Metrics and observability
│   │   └── rate_limiter.py      # Advanced rate limiting
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py              # Base model with audit fields
│   │   ├── user.py
│   │   ├── document.py
│   │   ├── ontology.py
│   │   ├── extraction.py
│   │   └── audit_log.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── base.py              # Base schemas with validation
│   │   ├── auth.py
│   │   ├── document.py
│   │   ├── ontology.py
│   │   ├── extraction.py
│   │   └── database.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base_service.py      # Base service with common patterns
│   │   ├── auth_service.py
│   │   ├── document_service.py
│   │   ├── ontology_service.py
│   │   ├── extraction_service.py
│   │   ├── database_service.py
│   │   └── llm_service.py       # Enhanced LLM abstraction
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_processing.py
│   │   ├── chunking.py
│   │   ├── deduplication.py
│   │   ├── export_utils.py
│   │   ├── validation.py
│   │   └── crypto.py
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── ontology_tasks.py
│   │   ├── extraction_tasks.py
│   │   └── maintenance_tasks.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── llm_provider.py      # Pluggable LLM providers
│   │   ├── anthropic_provider.py
│   │   ├── openai_provider.py
│   │   └── local_provider.py
│   ├── prompts.py               # Externalized prompts
│   ├── llm_config.py            # LLM configuration
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── alembic/
├── docker/
├── scripts/
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Core Components

### 1. Enhanced LLM Service with Pluggable Providers

#### LLM Provider Abstraction
```python
# providers/llm_provider.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class LLMResponse(BaseModel):
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str
    response_time: float

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model")
        self.api_key = config.get("api_key")
        
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        """Generate response from messages."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name."""
        pass

# providers/anthropic_provider.py
class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=self.api_key)
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        
        response = await self.client.messages.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return LLMResponse(
            content=response.content[0].text,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            model=self.model,
            finish_reason=response.stop_reason,
            response_time=time.time() - start_time
        )
    
    @property
    def provider_name(self) -> str:
        return "anthropic"

# Enhanced LLM Service
class LLMService:
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.primary_provider = None
        self.fallback_providers: List[BaseLLMProvider] = []
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured LLM providers."""
        settings = get_settings()
        
        # Primary provider (Anthropic Claude)
        if settings.anthropic_api_key:
            anthropic_provider = AnthropicProvider({
                "model": settings.llm_model_id,
                "api_key": settings.anthropic_api_key
            })
            self.providers["anthropic"] = anthropic_provider
            if not self.primary_provider:
                self.primary_provider = anthropic_provider
        
        # Fallback providers
        if settings.openai_api_key:
            openai_provider = OpenAIProvider({
                "model": "gpt-4-turbo-preview",
                "api_key": settings.openai_api_key
            })
            self.providers["openai"] = openai_provider
            self.fallback_providers.append(openai_provider)
    
    async def generate_with_fallback(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Generate response with automatic fallback to secondary providers."""
        
        # Try primary provider first
        try:
            return await self._generate_with_circuit_breaker(
                self.primary_provider, messages, **kwargs
            )
        except Exception as e:
            logger.warning(f"Primary provider failed: {e}")
            
            # Try fallback providers
            for provider in self.fallback_providers:
                try:
                    return await self._generate_with_circuit_breaker(
                        provider, messages, **kwargs
                    )
                except Exception as fe:
                    logger.warning(f"Fallback provider {provider.provider_name} failed: {fe}")
                    continue
            
            raise Exception("All LLM providers failed")
```

### 2. Circuit Breaker Implementation

```python
# core/circuit_breaker.py
import asyncio
import time
from enum import Enum
from typing import Callable, Any
from functools import wraps

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open" 
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self._failure_count = 0
        self._last_failure_time = None
        self._state = CircuitState.CLOSED
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker is OPEN. Last failure: {self._last_failure_time}"
                    )
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            
            except self.expected_exception as e:
                self._on_failure()
                raise e
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        return (
            time.time() - self._last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        self._failure_count = 0
        self._state = CircuitState.CLOSED
    
    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN

# Usage in LLM Service
class LLMService:
    @CircuitBreaker(failure_threshold=3, recovery_timeout=60)
    async def _generate_with_circuit_breaker(
        self,
        provider: BaseLLMProvider,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        return await provider.generate(messages, **kwargs)
```

### 3. Advanced Background Task Management

```python
# workers/celery_app.py
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
import structlog

logger = structlog.get_logger()

celery_app = Celery(
    "deepinsight",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.ontology_tasks",
        "app.workers.extraction_tasks", 
        "app.workers.maintenance_tasks"
    ]
)

# Enhanced Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Advanced routing
    task_routes={
        'app.workers.ontology_tasks.*': {'queue': 'ontology'},
        'app.workers.extraction_tasks.*': {'queue': 'extraction'},
        'app.workers.maintenance_tasks.*': {'queue': 'maintenance'},
    },
    
    # Retry configuration
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Dead letter queue
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    logger.info("Task started", task_id=task_id, task_name=task.name)

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    logger.info("Task completed", task_id=task_id, task_name=task.name, state=state)

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    logger.error("Task failed", task_id=task_id, exception=str(exception), traceback=traceback)

# Enhanced task with retry logic
from celery import Task
from celery.exceptions import Retry

class CallbackTask(Task):
    """Base task with callback support and enhanced error handling."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Execute callback on task failure."""
        callback_url = kwargs.get('failure_callback')
        if callback_url:
            # Send failure notification via webhook
            self.send_callback(callback_url, {
                'task_id': task_id,
                'status': 'failed',
                'error': str(exc)
            })
    
    def on_success(self, retval, task_id, args, kwargs):
        """Execute callback on task success."""
        callback_url = kwargs.get('success_callback') 
        if callback_url:
            self.send_callback(callback_url, {
                'task_id': task_id,
                'status': 'completed',
                'result': retval
            })
```

### 4. Enhanced Configuration Management

```python
# core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List, Dict, Any
from functools import lru_cache
import os

class DatabaseSettings(BaseSettings):
    url: str = Field(..., env="DATABASE_URL")
    pool_size: int = Field(10, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(20, env="DATABASE_MAX_OVERFLOW")
    pool_timeout: int = Field(30, env="DATABASE_POOL_TIMEOUT")
    pool_recycle: int = Field(3600, env="DATABASE_POOL_RECYCLE")

class RedisSettings(BaseSettings):
    url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    max_connections: int = Field(20, env="REDIS_MAX_CONNECTIONS")
    retry_on_timeout: bool = Field(True, env="REDIS_RETRY_ON_TIMEOUT")
    
class LLMSettings(BaseSettings):
    provider: str = Field("anthropic", env="LLM_PROVIDER")
    model_id: str = Field("claude-sonnet-4-20250514", env="LLM_MODEL_ID")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    max_tokens: int = Field(4000, env="LLM_MAX_TOKENS")
    temperature: float = Field(0.1, env="LLM_TEMPERATURE")
    request_timeout: int = Field(120, env="LLM_REQUEST_TIMEOUT")
    rate_limit_per_minute: int = Field(60, env="LLM_RATE_LIMIT_PER_MINUTE")

class SecuritySettings(BaseSettings):
    secret_key: str = Field(..., env="SECRET_KEY", min_length=32)
    algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    bcrypt_rounds: int = Field(12, env="BCRYPT_ROUNDS")
    
    # Rate limiting
    rate_limit_enabled: bool = Field(True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(3600, env="RATE_LIMIT_WINDOW")  # seconds
    
    # CORS
    allowed_origins: List[str] = Field(["http://localhost:3000"], env="ALLOWED_ORIGINS")
    allowed_hosts: List[str] = Field(["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")

class MonitoringSettings(BaseSettings):
    prometheus_enabled: bool = Field(True, env="PROMETHEUS_ENABLED")
    jaeger_enabled: bool = Field(False, env="JAEGER_ENABLED")
    jaeger_endpoint: Optional[str] = Field(None, env="JAEGER_ENDPOINT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    structured_logging: bool = Field(True, env="STRUCTURED_LOGGING")

class Settings(BaseSettings):
    # Application
    app_name: str = "DeepInsight API"
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    api_v1_str: str = "/api/v1"
    
    # Component settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    llm: LLMSettings = LLMSettings()
    security: SecuritySettings = SecuritySettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    
    # File handling
    max_file_size: int = Field(100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    upload_dir: str = Field("./uploads", env="UPLOAD_DIR")
    
    # Processing
    default_chunk_size: int = Field(1000, env="DEFAULT_CHUNK_SIZE")
    default_overlap_percentage: float = Field(0.1, env="DEFAULT_OVERLAP_PERCENTAGE")
    max_concurrent_extractions: int = Field(3, env="MAX_CONCURRENT_EXTRACTIONS")
    
    # Celery
    celery_broker_url: str = Field("redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field("redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_nested_delimiter = "__"  # Allows DATABASE__URL format
        
    @validator('environment')
    def validate_environment(cls, v):
        if v not in ['development', 'staging', 'production']:
            raise ValueError('Environment must be development, staging, or production')
        return v
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_critical_settings()
    
    def _validate_critical_settings(self):
        """Validate critical settings based on environment."""
        if self.environment == "production":
            if self.debug:
                raise ValueError("Debug mode must be disabled in production")
            
            if not self.llm.anthropic_api_key and not self.llm.openai_api_key:
                raise ValueError("At least one LLM API key must be configured")
            
            if len(self.security.secret_key) < 32:
                raise ValueError("Secret key must be at least 32 characters in production")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 5. Comprehensive Monitoring & Observability

```python
# core/monitoring.py
import time
import psutil
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from typing import Dict, Any
import asyncio

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'websocket_active_connections',
    'Number of active WebSocket connections'
)

LLM_REQUEST_COUNT = Counter(
    'llm_requests_total',
    'Total LLM API requests',
    ['provider', 'model', 'status']
)

LLM_REQUEST_DURATION = Histogram(
    'llm_request_duration_seconds',
    'LLM API request duration',
    ['provider', 'model']
)

EXTRACTION_JOBS = Gauge(
    'extraction_jobs_active',
    'Number of active extraction jobs'
)

SYSTEM_INFO = Info(
    'system_info',
    'System information'
)

# System metrics
CPU_USAGE = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('system_memory_usage_bytes', 'Memory usage in bytes')
DISK_USAGE = Gauge('system_disk_usage_bytes', 'Disk usage in bytes')

class PrometheusMetrics:
    def __init__(self):
        self.logger = structlog.get_logger()
        self._setup_system_info()
        self._start_system_metrics_collector()
    
    def _setup_system_info(self):
        """Set up system information metrics."""
        import platform
        SYSTEM_INFO.info({
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'architecture': platform.architecture()[0]
        })
    
    def _start_system_metrics_collector(self):
        """Start background task to collect system metrics."""
        asyncio.create_task(self._collect_system_metrics())
    
    async def _collect_system_metrics(self):
        """Collect system metrics periodically."""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                CPU_USAGE.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                MEMORY_USAGE.set(memory.used)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                DISK_USAGE.set(disk.used)
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                self.logger.error("Failed to collect system metrics", error=str(e))
                await asyncio.sleep(60)  # Wait longer on error

class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract endpoint pattern (removing IDs)
        endpoint = self._normalize_endpoint(request.url.path)
        
        try:
            response = await call_next(request)
            
            # Record successful request
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(time.time() - start_time)
            
            return response
            
        except Exception as e:
            # Record failed request
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=500
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(time.time() - start_time)
            
            raise e
    
    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path by replacing IDs with placeholders."""
        import re
        # Replace UUIDs and numeric IDs with placeholders
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)
        path = re.sub(r'/\d+', '/{id}', path)
        return path

# Enhanced structured logging
logger = structlog.get_logger()

def setup_logging():
    """Configure structured logging."""
    import logging
    import sys
    
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Metrics endpoint
from fastapi import APIRouter
metrics_router = APIRouter()

@metrics_router.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@metrics_router.get("/health")
async def health_check():
    """Comprehensive health check."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Database health
    try:
        # Simple database query
        from app.core.database import get_db
        async with get_db() as db:
            await db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis health
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url(get_settings().redis.url)
        await redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # LLM provider health
    try:
        llm_service = LLMService()
        await llm_service.primary_provider.health_check()
        health_status["checks"]["llm_provider"] = "healthy"
    except Exception as e:
        health_status["checks"]["llm_provider"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status
```

### 6. Enhanced Input Validation & Sanitization

```python
# utils/validation.py
import re
import bleach
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator, Field
from fastapi import HTTPException
import magic
import hashlib

class FileValidationResult(BaseModel):
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    mime_type: str
    file_hash: str
    file_size: int

class AdvancedFileValidator:
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'text/plain',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/markdown'
    }
    
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    SUSPICIOUS_PATTERNS = [
        rb'<script[^>]*>',
        rb'javascript:',
        rb'vbscript:',
        rb'<?php',
        rb'<%',
        rb'exec\(',
        rb'system\(',
        rb'shell_exec\(',
        rb'eval\(',
        rb'\x00',  # Null bytes
        rb'\xff\xd8\xff',  # JPEG header in non-image file
    ]
    
    async def validate_file(self, file_content: bytes, filename: str, declared_mime_type: str) -> FileValidationResult:
        """Comprehensive file validation."""
        errors = []
        warnings = []
        
        # File size check
        file_size = len(file_content)
        if file_size > self.MAX_FILE_SIZE:
            errors.append(f"File size {file_size} exceeds maximum {self.MAX_FILE_SIZE}")
        
        # Filename validation
        if not self._validate_filename(filename):
            errors.append(f"Invalid filename: {filename}")
        
        # MIME type detection
        actual_mime_type = magic.from_buffer(file_content, mime=True)
        if actual_mime_type != declared_mime_type:
            warnings.append(f"MIME type mismatch: declared {declared_mime_type}, detected {actual_mime_type}")
        
        # Check against allowed types
        if actual_mime_type not in self.ALLOWED_MIME_TYPES:
            errors.append(f"File type {actual_mime_type} not allowed")
        
        # Malicious pattern detection
        suspicious_patterns = self._scan_for_malicious_patterns(file_content)
        if suspicious_patterns:
            errors.append(f"Suspicious patterns detected: {', '.join(suspicious_patterns)}")
        
        # Generate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        return FileValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            mime_type=actual_mime_type,
            file_hash=file_hash,
            file_size=file_size
        )
    
    def _validate_filename(self, filename: str) -> bool:
        """Validate filename for security."""
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9._-]+$', filename):
            return False
        
        # Check length
        if len(filename) > 255:
            return False
        
        return True
    
    def _scan_for_malicious_patterns(self, content: bytes) -> List[str]:
        """Scan file content for malicious patterns."""
        found_patterns = []
        
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern.decode('utf-8', errors='ignore'))
        
        return found_patterns

class SecureInputValidator:
    """Enhanced input validation and sanitization."""
    
    @staticmethod
    def sanitize_string(
        value: str,
        max_length: int = 1000,
        allow_html: bool = False,
        allowed_tags: List[str] = None
    ) -> str:
        """Sanitize string input."""
        if not value:
            return ""
        
        # Truncate to max length
        value = value[:max_length]
        
        if allow_html:
            # Allow specific HTML tags
            allowed_tags = allowed_tags or ['b', 'i', 'u', 'em', 'strong']
            value = bleach.clean(value, tags=allowed_tags, strip=True)
        else:
            # Remove all HTML tags
            value = bleach.clean(value, tags=[], strip=True)
        
        # Remove null bytes and other control characters
        value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', value)
        
        return value.strip()
    
    @staticmethod
    def validate_ontology_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize ontology entry."""
        validated = {}
        
        # Validate subject
        if 'subject' in entry:
            validated['subject'] = {
                'entity_type': SecureInputValidator.sanitize_string(
                    entry['subject'].get('entity_type', ''), 
                    max_length=100
                ),
                'type_variations': [
                    SecureInputValidator.sanitize_string(variation, max_length=100)
                    for variation in entry['subject'].get('type_variations', [])[:20]
                ],
                'primitive_type': entry['subject'].get('primitive_type', 'string')
            }
        
        # Similar validation for relationship and object...
        
        return validated

# Enhanced Pydantic models with validation
class SecureOntologyEntry(BaseModel):
    entity_type: str = Field(..., max_length=100, regex=r'^[a-zA-Z0-9_\s]+$')
    type_variations: List[str] = Field(default_factory=list, max_items=20)
    primitive_type: str = Field(..., regex=r'^(string|float|integer|boolean)$')
    
    @validator('entity_type', 'type_variations', pre=True)
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            return SecureInputValidator.sanitize_string(v)
        elif isinstance(v, list):
            return [SecureInputValidator.sanitize_string(item) for item in v]
        return v
```

This enhanced backend specification addresses all the reviewer's feedback with improved LLM abstraction, circuit breakers, comprehensive monitoring, advanced background task management, and robust input validation while maintaining high performance and security standards.