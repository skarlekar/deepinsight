# Security Requirements

## Overview
Comprehensive security framework for the DeepInsight system covering authentication, authorization, data protection, audit trails, and compliance requirements. This document outlines defensive security measures to protect against common threats and ensure data integrity.

## Security Principles

### Defense in Depth
- Multiple layers of security controls
- Redundant security measures
- Fail-safe defaults and secure configurations
- Principle of least privilege

### Zero Trust Architecture
- Never trust, always verify
- Verify explicitly for every request
- Assume breach and verify end-to-end
- Use least privileged access

---

## Authentication & Authorization

### User Authentication

#### Authentication Methods
```python
# JWT-based authentication with refresh tokens
class AuthenticationService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    async def create_access_token(self, user_id: str, permissions: List[str]) -> str:
        """Create JWT access token with user claims."""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "permissions": permissions,
            "token_type": "access"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("token_type") != "access":
                raise HTTPException(401, "Invalid token type")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token expired")
        except jwt.JWTError:
            raise HTTPException(401, "Invalid token")
```

#### Password Security
- **Hashing**: Argon2id for password hashing (OWASP recommended)
- **Complexity**: Minimum 12 characters, mixed case, numbers, symbols
- **Storage**: Never store plaintext passwords
- **Reset**: Secure password reset with time-limited tokens

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

class PasswordService:
    def __init__(self):
        self.hasher = PasswordHasher(
            time_cost=3,    # Number of iterations
            memory_cost=64*1024,  # Memory usage in KiB
            parallelism=1,  # Number of parallel threads
            hash_len=32,    # Hash output length
            salt_len=16     # Salt length
        )
    
    def hash_password(self, password: str) -> str:
        """Hash password using Argon2id."""
        return self.hasher.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            self.hasher.verify(hashed, password)
            return True
        except VerifyMismatchError:
            return False
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password meets security requirements."""
        checks = {
            "length": len(password) >= 12,
            "uppercase": any(c.isupper() for c in password),
            "lowercase": any(c.islower() for c in password), 
            "digits": any(c.isdigit() for c in password),
            "special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password),
            "common": password not in COMMON_PASSWORDS  # Check against common passwords list
        }
        
        return {
            "valid": all(checks.values()),
            "checks": checks,
            "score": sum(checks.values()) / len(checks)
        }
```

### Role-Based Access Control (RBAC)

#### Permission System
```python
from enum import Enum
from typing import List, Set

class Permission(str, Enum):
    # Document permissions
    DOCUMENT_CREATE = "document:create"
    DOCUMENT_READ = "document:read" 
    DOCUMENT_UPDATE = "document:update"
    DOCUMENT_DELETE = "document:delete"
    
    # Ontology permissions
    ONTOLOGY_CREATE = "ontology:create"
    ONTOLOGY_READ = "ontology:read"
    ONTOLOGY_UPDATE = "ontology:update"
    ONTOLOGY_DELETE = "ontology:delete"
    
    # Extraction permissions
    EXTRACTION_CREATE = "extraction:create"
    EXTRACTION_READ = "extraction:read"
    EXTRACTION_CANCEL = "extraction:cancel"
    
    # Database permissions
    DATABASE_CONNECT = "database:connect"
    DATABASE_IMPORT = "database:import"
    DATABASE_EXPORT = "database:export"
    
    # Admin permissions
    USER_MANAGE = "user:manage"
    SYSTEM_CONFIG = "system:config"
    AUDIT_READ = "audit:read"

class Role(str, Enum):
    ADMIN = "admin"
    POWER_USER = "power_user"
    STANDARD_USER = "standard_user"
    VIEWER = "viewer"

ROLE_PERMISSIONS = {
    Role.ADMIN: [p.value for p in Permission],  # All permissions
    Role.POWER_USER: [
        Permission.DOCUMENT_CREATE, Permission.DOCUMENT_READ, Permission.DOCUMENT_UPDATE,
        Permission.ONTOLOGY_CREATE, Permission.ONTOLOGY_READ, Permission.ONTOLOGY_UPDATE,
        Permission.EXTRACTION_CREATE, Permission.EXTRACTION_READ, Permission.EXTRACTION_CANCEL,
        Permission.DATABASE_CONNECT, Permission.DATABASE_IMPORT, Permission.DATABASE_EXPORT
    ],
    Role.STANDARD_USER: [
        Permission.DOCUMENT_CREATE, Permission.DOCUMENT_READ,
        Permission.ONTOLOGY_READ, Permission.ONTOLOGY_UPDATE,
        Permission.EXTRACTION_CREATE, Permission.EXTRACTION_READ,
        Permission.DATABASE_EXPORT
    ],
    Role.VIEWER: [
        Permission.DOCUMENT_READ, Permission.ONTOLOGY_READ, Permission.EXTRACTION_READ
    ]
}

def check_permission(user_permissions: Set[str], required_permission: Permission) -> bool:
    """Check if user has required permission."""
    return required_permission.value in user_permissions

# Dependency for FastAPI routes
async def require_permission(permission: Permission):
    """Dependency to check if current user has required permission."""
    def permission_checker(current_user: User = Depends(get_current_user)):
        if not check_permission(set(current_user.permissions), permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission.value}"
            )
        return current_user
    return permission_checker
```

## Data Protection

### Encryption

#### Data at Rest
- **Database Encryption**: AES-256 encryption for sensitive columns
- **File Storage**: Encrypted file storage using cryptography library
- **Configuration**: Encrypted environment variables and secrets

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class EncryptionService:
    def __init__(self, password: str):
        """Initialize encryption service with master password."""
        self.key = self._derive_key(password.encode())
        self.fernet = Fernet(self.key)
    
    def _derive_key(self, password: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted data."""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_file(self, file_path: str, output_path: str):
        """Encrypt file and save to output path."""
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        encrypted_data = self.fernet.encrypt(file_data)
        
        with open(output_path, 'wb') as encrypted_file:
            encrypted_file.write(encrypted_data)

# SQLAlchemy encrypted column type
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

class EncryptedText(EncryptedType):
    impl = Text
    
    def __init__(self, secret_key: str):
        super(EncryptedText, self).__init__(Text, secret_key, AesEngine, 'pkcs5')

# Usage in models
class SensitiveData(Base):
    __tablename__ = "sensitive_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    encrypted_content = Column(EncryptedText(os.getenv("DATABASE_SECRET_KEY")))
    api_key = Column(EncryptedText(os.getenv("DATABASE_SECRET_KEY")))
```

#### Data in Transit
- **HTTPS/TLS**: Mandatory TLS 1.3 for all communications
- **Certificate Validation**: Proper certificate validation and pinning
- **API Communications**: All API calls over encrypted connections

```python
# FastAPI SSL configuration
import ssl
from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' wss: https:; "
        "font-src 'self'"
    )
    
    return response

# Configure CORS securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Trusted host validation
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)
```

### Input Validation & Sanitization

#### Request Validation
```python
from pydantic import BaseModel, validator, Field
from typing import Optional, List
import bleach
import re

class SecureDocumentUpload(BaseModel):
    filename: str = Field(..., max_length=255, regex=r'^[a-zA-Z0-9._-]+$')
    content_type: str = Field(..., regex=r'^(application/pdf|text/plain|application/vnd\.openxmlformats-officedocument\.wordprocessingml\.document)$')
    size: int = Field(..., ge=1, le=100*1024*1024)  # Max 100MB
    
    @validator('filename')
    def sanitize_filename(cls, v):
        """Sanitize filename to prevent path traversal."""
        # Remove any path separators
        v = v.replace('/', '').replace('\\', '').replace('..', '')
        # Remove potentially dangerous characters
        v = re.sub(r'[<>:"|?*]', '', v)
        return v

class SecureOntologyEntry(BaseModel):
    entity_type: str = Field(..., max_length=100, regex=r'^[a-zA-Z0-9_]+$')
    type_variations: List[str] = Field(..., max_items=20)
    primitive_type: str = Field(..., regex=r'^(string|float|integer|boolean)$')
    
    @validator('type_variations')
    def sanitize_variations(cls, v):
        """Sanitize type variations."""
        sanitized = []
        for variation in v:
            # Remove HTML tags and limit length
            clean = bleach.clean(variation, tags=[], strip=True)[:50]
            if clean and re.match(r'^[a-zA-Z0-9_\s]+$', clean):
                sanitized.append(clean.strip())
        return sanitized[:20]  # Limit to 20 variations

# SQL injection prevention with parameterized queries
from sqlalchemy import text

async def secure_query_example(db: AsyncSession, user_id: str):
    """Example of secure database query with parameters."""
    # GOOD: Parameterized query
    query = text("SELECT * FROM documents WHERE user_id = :user_id AND status = :status")
    result = await db.execute(query, {"user_id": user_id, "status": "active"})
    
    # NEVER DO THIS: String concatenation (vulnerable to SQL injection)
    # query = f"SELECT * FROM documents WHERE user_id = '{user_id}'"
```

#### File Upload Security
```python
import magic
import hashlib
from pathlib import Path

class SecureFileHandler:
    ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.docx'}
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'text/plain', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """Comprehensive file validation."""
        errors = []
        
        # Check file size
        if file.size > self.MAX_FILE_SIZE:
            errors.append(f"File too large: {file.size} bytes")
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            errors.append(f"File extension not allowed: {file_ext}")
        
        # Check declared MIME type
        if file.content_type not in self.ALLOWED_MIME_TYPES:
            errors.append(f"MIME type not allowed: {file.content_type}")
        
        # Read file content for validation
        content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        # Check actual MIME type using python-magic
        actual_mime = magic.from_buffer(content, mime=True)
        if actual_mime not in self.ALLOWED_MIME_TYPES:
            errors.append(f"Actual MIME type doesn't match declared: {actual_mime}")
        
        # Check for malicious patterns
        if self._contains_malicious_patterns(content):
            errors.append("File contains potentially malicious content")
        
        # Generate file hash for integrity
        file_hash = hashlib.sha256(content).hexdigest()
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "file_hash": file_hash,
            "actual_mime_type": actual_mime
        }
    
    def _contains_malicious_patterns(self, content: bytes) -> bool:
        """Check for known malicious patterns."""
        malicious_patterns = [
            b'<script',
            b'javascript:',
            b'<?php',
            b'<%',
            b'eval(',
            b'exec(',
            b'system(',
            b'shell_exec('
        ]
        
        content_lower = content.lower()
        return any(pattern in content_lower for pattern in malicious_patterns)
    
    async def save_file_securely(self, file: UploadFile, user_id: str) -> str:
        """Save file with security measures."""
        validation_result = await self.validate_file(file)
        if not validation_result["valid"]:
            raise SecurityError(f"File validation failed: {validation_result['errors']}")
        
        # Generate secure filename
        file_ext = Path(file.filename).suffix.lower()
        secure_filename = f"{user_id}_{uuid.uuid4().hex}{file_ext}"
        file_path = self.upload_dir / secure_filename
        
        # Save file
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Set restrictive file permissions
        file_path.chmod(0o600)  # Owner read/write only
        
        return str(file_path)
```

## Logging & Audit Trail

### Security Event Logging
```python
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class SecurityEventType(str, Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_DENIED = "permission_denied"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    FILE_UPLOAD = "file_upload"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    API_RATE_LIMIT = "api_rate_limit"
    CONFIG_CHANGE = "config_change"

class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger("security_audit")
        self.logger.setLevel(logging.INFO)
        
        # Create formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler for audit logs
        file_handler = logging.FileHandler('logs/security_audit.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log_security_event(
        self,
        event_type: SecurityEventType,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ):
        """Log security event with structured data."""
        
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "resource": resource,
            "success": success,
            "details": details or {}
        }
        
        # Log at different levels based on event type
        if event_type in [SecurityEventType.LOGIN_FAILURE, SecurityEventType.PERMISSION_DENIED, 
                         SecurityEventType.SUSPICIOUS_ACTIVITY]:
            self.logger.warning(json.dumps(event_data))
        elif success:
            self.logger.info(json.dumps(event_data))
        else:
            self.logger.error(json.dumps(event_data))

# Usage in FastAPI endpoints
from fastapi import Request

audit_logger = AuditLogger()

@app.post("/api/v1/auth/login")
async def login(request: Request, credentials: LoginCredentials):
    try:
        user = await authenticate_user(credentials.username, credentials.password)
        
        # Log successful login
        audit_logger.log_security_event(
            SecurityEventType.LOGIN_SUCCESS,
            user_id=str(user.id),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
        
        return {"access_token": create_access_token(user.id)}
    
    except AuthenticationError as e:
        # Log failed login attempt
        audit_logger.log_security_event(
            SecurityEventType.LOGIN_FAILURE,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={"username": credentials.username, "error": str(e)},
            success=False
        )
        raise HTTPException(401, "Invalid credentials")
```

### Data Access Logging
```python
# Decorator for logging data access
from functools import wraps

def log_data_access(resource_type: str):
    """Decorator to log data access operations."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user and request info from context
            current_user = kwargs.get('current_user')
            request = kwargs.get('request')
            
            try:
                result = await func(*args, **kwargs)
                
                # Log successful data access
                audit_logger.log_security_event(
                    SecurityEventType.DATA_ACCESS,
                    user_id=str(current_user.id) if current_user else None,
                    ip_address=request.client.host if request else None,
                    resource=resource_type,
                    details={"operation": func.__name__, "success": True}
                )
                
                return result
            
            except Exception as e:
                # Log failed data access
                audit_logger.log_security_event(
                    SecurityEventType.DATA_ACCESS,
                    user_id=str(current_user.id) if current_user else None,
                    ip_address=request.client.host if request else None,
                    resource=resource_type,
                    details={"operation": func.__name__, "error": str(e)},
                    success=False
                )
                raise
        
        return wrapper
    return decorator

# Usage
@log_data_access("document")
async def get_document(document_id: str, current_user: User, request: Request):
    return await document_service.get_document(document_id, current_user.id)
```

## Rate Limiting & DDoS Protection

### API Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Apply rate limiting to endpoints
@app.post("/api/v1/documents/upload")
@limiter.limit("10/minute")  # Max 10 uploads per minute per IP
async def upload_document(request: Request, file: UploadFile = File(...)):
    # Implementation
    pass

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute per IP
async def login(request: Request, credentials: LoginCredentials):
    # Implementation
    pass

@app.post("/api/v1/ontologies/generate")
@limiter.limit("3/hour")  # Max 3 ontology generations per hour per IP
async def generate_ontology(request: Request, data: OntologyRequest):
    # Implementation
    pass

# User-based rate limiting
class UserRateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
    
    async def check_user_rate_limit(self, user_id: str, action: str, limit: int, window: int) -> bool:
        """Check if user has exceeded rate limit for specific action."""
        key = f"rate_limit:{user_id}:{action}"
        current = self.redis_client.get(key)
        
        if current is None:
            self.redis_client.setex(key, window, 1)
            return True
        
        if int(current) >= limit:
            return False
        
        self.redis_client.incr(key)
        return True

# Usage with dependency
async def rate_limit_user(
    action: str, 
    limit: int, 
    window: int, 
    current_user: User = Depends(get_current_user)
):
    """Dependency to enforce user-based rate limits."""
    rate_limiter = UserRateLimiter()
    
    if not await rate_limiter.check_user_rate_limit(
        str(current_user.id), action, limit, window
    ):
        audit_logger.log_security_event(
            SecurityEventType.API_RATE_LIMIT,
            user_id=str(current_user.id),
            details={"action": action, "limit": limit, "window": window}
        )
        raise HTTPException(429, "Rate limit exceeded")
    
    return current_user
```

## Session Management

### Secure Session Handling
```python
from fastapi import HTTPException, Depends, Cookie
from datetime import datetime, timedelta
import redis
import json

class SessionManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=2)
        self.session_timeout = timedelta(hours=8)  # 8 hour session timeout
        self.max_sessions_per_user = 5  # Limit concurrent sessions
    
    async def create_session(self, user_id: str, ip_address: str, user_agent: str) -> str:
        """Create new user session."""
        session_id = str(uuid.uuid4())
        session_data = {
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        # Store session
        session_key = f"session:{session_id}"
        self.redis_client.setex(
            session_key, 
            int(self.session_timeout.total_seconds()), 
            json.dumps(session_data)
        )
        
        # Track user sessions
        user_sessions_key = f"user_sessions:{user_id}"
        self.redis_client.sadd(user_sessions_key, session_id)
        self.redis_client.expire(user_sessions_key, int(self.session_timeout.total_seconds()))
        
        # Enforce session limit
        await self._enforce_session_limit(user_id)
        
        return session_id
    
    async def validate_session(
        self, 
        session_id: str, 
        ip_address: str, 
        user_agent: str
    ) -> Optional[Dict[str, Any]]:
        """Validate session and check for suspicious activity."""
        session_key = f"session:{session_id}"
        session_data = self.redis_client.get(session_key)
        
        if not session_data:
            return None
        
        session_info = json.loads(session_data)
        
        # Check for session hijacking indicators
        if session_info["ip_address"] != ip_address:
            audit_logger.log_security_event(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                user_id=session_info["user_id"],
                ip_address=ip_address,
                details={
                    "event": "ip_address_change",
                    "original_ip": session_info["ip_address"],
                    "new_ip": ip_address
                }
            )
            # Invalidate session
            await self.invalidate_session(session_id)
            return None
        
        if session_info["user_agent"] != user_agent:
            audit_logger.log_security_event(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                user_id=session_info["user_id"],
                ip_address=ip_address,
                details={
                    "event": "user_agent_change",
                    "original_ua": session_info["user_agent"],
                    "new_ua": user_agent
                }
            )
        
        # Update last activity
        session_info["last_activity"] = datetime.utcnow().isoformat()
        self.redis_client.setex(
            session_key,
            int(self.session_timeout.total_seconds()),
            json.dumps(session_info)
        )
        
        return session_info
    
    async def _enforce_session_limit(self, user_id: str):
        """Enforce maximum sessions per user."""
        user_sessions_key = f"user_sessions:{user_id}"
        sessions = self.redis_client.smembers(user_sessions_key)
        
        if len(sessions) > self.max_sessions_per_user:
            # Remove oldest sessions
            sessions_to_remove = len(sessions) - self.max_sessions_per_user
            for session_id in list(sessions)[:sessions_to_remove]:
                await self.invalidate_session(session_id.decode())
    
    async def invalidate_session(self, session_id: str):
        """Invalidate specific session."""
        session_key = f"session:{session_id}"
        session_data = self.redis_client.get(session_key)
        
        if session_data:
            session_info = json.loads(session_data)
            user_sessions_key = f"user_sessions:{session_info['user_id']}"
            self.redis_client.srem(user_sessions_key, session_id)
        
        self.redis_client.delete(session_key)
```

## Error Handling & Security

### Secure Error Responses
```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import traceback
import uuid

class SecurityError(Exception):
    """Custom security-related exception."""
    pass

@app.exception_handler(SecurityError)
async def security_error_handler(request: Request, exc: SecurityError):
    """Handle security errors without exposing sensitive information."""
    error_id = str(uuid.uuid4())
    
    # Log detailed error for internal use
    audit_logger.log_security_event(
        SecurityEventType.SUSPICIOUS_ACTIVITY,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        details={
            "error_id": error_id,
            "error_type": "SecurityError",
            "error_message": str(exc),
            "traceback": traceback.format_exc()
        },
        success=False
    )
    
    # Return generic error message to user
    return JSONResponse(
        status_code=400,
        content={
            "error": "Security validation failed",
            "error_id": error_id,
            "message": "Your request could not be processed due to security constraints."
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions securely."""
    error_id = str(uuid.uuid4())
    
    # Log error details for debugging
    logging.error(f"Unhandled exception {error_id}: {str(exc)}", exc_info=True)
    
    # Return generic error message
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_id": error_id,
            "message": "An unexpected error occurred. Please try again later."
        }
    )

# Prevent information disclosure in debug mode
from fastapi.exception_handlers import http_exception_handler

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler to control error disclosure."""
    
    # Log the exception
    audit_logger.log_security_event(
        SecurityEventType.DATA_ACCESS,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        resource=str(request.url),
        details={"status_code": exc.status_code, "detail": exc.detail},
        success=False
    )
    
    # In production, sanitize error messages
    if not settings.debug and exc.status_code >= 500:
        exc.detail = "Internal server error"
    
    return await http_exception_handler(request, exc)
```

## Environment & Configuration Security

### Secure Configuration Management
```python
from pydantic_settings import BaseSettings
from typing import Optional
import os
from cryptography.fernet import Fernet

class SecureSettings(BaseSettings):
    """Secure application settings with encrypted secrets."""
    
    # Application settings
    app_name: str = "DeepInsight"
    environment: str = Field(default="development", regex="^(development|staging|production)$")
    debug: bool = Field(default=False)
    
    # Security settings
    secret_key: str = Field(..., min_length=32)  # Required, minimum 32 chars
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    session_timeout_hours: int = 8
    
    # Database settings
    database_url: str
    database_secret_key: str = Field(..., min_length=32)  # For column encryption
    
    # External API keys (encrypted in environment)
    anthropic_api_key_encrypted: Optional[str] = None
    openai_api_key_encrypted: Optional[str] = None
    
    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    
    # Rate limiting
    rate_limit_enabled: bool = True
    default_rate_limit: str = "100/hour"
    
    # File upload settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    upload_dir: str = "./uploads"
    
    # Security features
    require_https: bool = True
    secure_cookies: bool = True
    password_min_length: int = 12
    max_login_attempts: int = 5
    account_lockout_duration_minutes: int = 15
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_security_settings()
        self._decrypt_secrets()
    
    def _validate_security_settings(self):
        """Validate security-critical settings."""
        if self.environment == "production":
            if self.debug:
                raise ValueError("Debug mode must be disabled in production")
            if not self.require_https:
                raise ValueError("HTTPS must be required in production")
            if len(self.secret_key) < 32:
                raise ValueError("Secret key must be at least 32 characters")
    
    def _decrypt_secrets(self):
        """Decrypt encrypted environment variables."""
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            if self.environment == "production":
                raise ValueError("ENCRYPTION_KEY must be set in production")
            return
        
        fernet = Fernet(encryption_key.encode())
        
        if self.anthropic_api_key_encrypted:
            self.anthropic_api_key = fernet.decrypt(
                self.anthropic_api_key_encrypted.encode()
            ).decode()
        
        if self.openai_api_key_encrypted:
            self.openai_api_key = fernet.decrypt(
                self.openai_api_key_encrypted.encode()
            ).decode()

# Secure settings initialization
settings = SecureSettings()

# Security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Apply security policies to all requests."""
    
    # Enforce HTTPS in production
    if settings.require_https and settings.environment == "production":
        if request.url.scheme != "https":
            return JSONResponse(
                status_code=400,
                content={"error": "HTTPS required"}
            )
    
    # Add security headers
    response = await call_next(request)
    
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response
```

## Compliance & Standards

### Data Privacy Compliance
- **GDPR Compliance**: Right to access, rectify, erase user data
- **Data Minimization**: Collect only necessary data
- **Consent Management**: Clear consent for data processing
- **Data Portability**: Export user data in standard formats

### Security Standards
- **OWASP Top 10**: Address all OWASP top security risks
- **NIST Framework**: Follow NIST cybersecurity framework
- **ISO 27001**: Information security management standards
- **SOC 2**: Security, availability, processing integrity controls

This comprehensive security framework ensures the DeepInsight system maintains the highest security standards while protecting user data and system integrity.