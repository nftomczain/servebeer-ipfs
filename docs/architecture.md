# 🏗️ ServeBeer IPFS - Architecture Documentation

**Version:** 1.0.0  
**Last Updated:** January 2025

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Components](#components)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [IPFS Integration](#ipfs-integration)
7. [Authentication & Security](#authentication--security)
8. [Storage Management](#storage-management)
9. [API Design](#api-design)
10. [Deployment Architecture](#deployment-architecture)

---

## Overview

ServeBeer is a Flask-based IPFS pinning service designed to run on resource-constrained hardware (Raspberry Pi). The architecture prioritizes simplicity, reliability, and ease of deployment while maintaining security and scalability.

### Core Principles

- **Simplicity First**: Minimal dependencies, straightforward code
- **Resource Efficient**: Optimized for Raspberry Pi hardware
- **Security Focused**: Audit logging, GDPR compliance, secure sessions
- **IPFS Native**: Direct integration with IPFS daemon
- **Community Driven**: Transparent, open-source, community-funded

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Browser  │  │  Mobile  │  │   API    │             │
│  │  Client  │  │  Client  │  │  Client  │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
└───────┼─────────────┼─────────────┼────────────────────┘
        │             │             │
        └─────────────┴─────────────┘
                      │
┌─────────────────────▼─────────────────────────────────┐
│              Application Layer                         │
│  ┌──────────────────────────────────────────────┐     │
│  │         Flask Application (app.py)           │     │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────────┐  │     │
│  │  │  Auth   │ │   API    │ │  Dashboard   │  │     │
│  │  │ System  │ │ Handlers │ │   Manager    │  │     │
│  │  └─────────┘ └──────────┘ └──────────────┘  │     │
│  │  ┌──────────────────────────────────────┐   │     │
│  │  │      Session Management              │   │     │
│  │  └──────────────────────────────────────┘   │     │
│  └──────────────────┬───────────────────────────┘     │
└─────────────────────┼─────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼──────┐           ┌────────▼────────┐
│   Data Layer │           │  Storage Layer  │
│              │           │                 │
│  ┌────────┐  │           │  ┌───────────┐ │
│  │SQLite  │  │           │  │IPFS Daemon│ │
│  │Database│  │           │  │  (Kubo)   │ │
│  └────────┘  │           │  └─────┬─────┘ │
│              │           │        │       │
│  ┌────────┐  │           │  ┌─────▼─────┐ │
│  │ Audit  │  │           │  │IPFS       │ │
│  │  Logs  │  │           │  │Network    │ │
│  └────────┘  │           │  └───────────┘ │
└──────────────┘           └─────────────────┘
```

### Technology Stack

**Backend:**
- Python 3.11
- Flask 2.3.3 (Web framework)
- SQLite (Database)
- Requests (HTTP client)

**Storage:**
- IPFS Kubo (go-ipfs)
- Local filesystem (logs, database)

**Frontend:**
- HTML5 + CSS3
- Vanilla JavaScript
- No heavy frameworks (lightweight)

**Infrastructure:**
- Raspberry Pi 400 (current)
- Debian 12 Bookworm
- Optional: Docker containers

---

## Components

### 1. Flask Application (`app.py`)

Main application file containing:

**Core Modules:**
```python
app.py                          # Main application
├── Authentication System       # Login, register, logout
├── API Handlers               # Pin, upload endpoints
├── Dashboard Manager          # User statistics, file management
├── IPFS Integration          # Communication with IPFS daemon
├── Security Layer            # Audit logging, GDPR compliance
└── Helper Functions          # Database, utilities
```

**Supporting Files:**
```python
flask_network_endpoint.py      # IPFS network status helpers
status_data.py                 # System status data aggregation
```

### 2. Database Layer

**SQLite Database** (`database/servebeer.db`)

Four main tables:
- `users` - User accounts and storage quotas
- `pins` - Pinned content records
- `audit_log` - Security event logging
- `request_log` - GDPR-compliant request tracking

### 3. IPFS Integration

**Communication:**
- HTTP API calls to local IPFS daemon
- Default endpoint: `http://localhost:5001/api/v0`
- Stateless communication (no persistent connections)

**Operations:**
- `pin/add` - Pin content by CID
- `add` - Upload file to IPFS
- `object/stat` - Get content information
- `version` - Health check

### 4. Authentication System

**Method:** Session-based authentication
- Flask sessions with secure cookies
- SHA-256 password hashing
- 30-day session lifetime
- Automatic session cleanup

**No JWT or Bearer tokens** - keeps it simple.

### 5. Storage Management

**Quota System:**
- Per-user storage tracking
- Real-time quota enforcement (production mode)
- Safe size calculation with fallbacks
- Beta mode bypasses all limits

### 6. Logging & Monitoring

**Audit Log:**
- All security-relevant events
- User actions (login, pin, upload)
- IP address tracking
- Timestamp recording

**Request Log (GDPR):**
- HTTP method and endpoint
- User agent strings
- IP addresses
- User association

---

## Data Flow

### 1. User Registration Flow

```
User Browser
    │
    ├─► POST /register (email, password)
    │
    ▼
Flask Application
    │
    ├─► Validate input
    ├─► Hash password (SHA-256)
    ├─► Generate API key
    │
    ▼
SQLite Database
    │
    ├─► INSERT INTO users
    ├─► Create session
    │
    ▼
Redirect to Dashboard
```

### 2. CID Pinning Flow

```
User Dashboard
    │
    ├─► POST /api/pin (cid, filename)
    │
    ▼
Authentication Check
    │
    ├─► Session validation
    │
    ▼
CID Validation
    │
    ├─► IPFS: object/stat
    ├─► Check if CID exists
    ├─► Get content size
    │
    ▼
Quota Check (if TESTING_MODE=false)
    │
    ├─► Check user storage_used
    ├─► Verify size + current < limit
    │
    ▼
Duplicate Check
    │
    ├─► Query pins table
    ├─► Check if (user_id, cid) exists
    │
    ▼
IPFS Pin Operation
    │
    ├─► IPFS: pin/add
    ├─► Wait for confirmation
    │
    ▼
Database Update
    │
    ├─► INSERT INTO pins
    ├─► UPDATE users.storage_used
    ├─► INSERT INTO audit_log
    │
    ▼
Response to User
```

### 3. File Upload Flow

```
User Browser
    │
    ├─► POST /upload (multipart file)
    │
    ▼
Authentication Check
    │
    ├─► Session validation
    │
    ▼
File Reception
    │
    ├─► Receive multipart data
    ├─► Extract filename, mimetype
    │
    ▼
IPFS Upload
    │
    ├─► IPFS: add (file stream)
    ├─► Receive CID + size
    │
    ▼
Quota Check (if TESTING_MODE=false)
    │
    ├─► Verify size + current < limit
    │
    ▼
Database Update
    │
    ├─► INSERT INTO pins (upload_type='upload')
    ├─► UPDATE users.storage_used
    ├─► INSERT INTO audit_log
    │
    ▼
Success Page (CID, IPFS URLs)
```

### 4. Dashboard Data Flow

```
User Request /dashboard
    │
    ├─► GET /api/dashboard/stats
    ├─► GET /api/dashboard/files
    ├─► GET /api/dashboard/activity
    ├─► GET /api/dashboard/analytics
    │
    ▼
Parallel Data Fetching
    │
    ├─► Query users table (storage info)
    ├─► Query pins table (file list)
    ├─► Query audit_log (recent activity)
    ├─► Aggregate analytics (30 days)
    │
    ▼
JSON Response
    │
    ├─► storage_used_mb, storage_limit_mb
    ├─► total_pins, today_pins
    ├─► files[] with CID, size, date
    ├─► activities[] with events
    ├─► analytics charts data
    │
    ▼
Frontend Rendering
    │
    ├─► Update DOM with stats
    ├─► Populate file table
    ├─► Render charts (Chart.js)
    └─► Display activity feed
```

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password_hash TEXT,
    wallet_address TEXT UNIQUE,
    auth_method TEXT DEFAULT 'email',
    tier TEXT DEFAULT 'free',
    storage_used INTEGER DEFAULT 0,
    storage_limit INTEGER DEFAULT 262144000,  -- 250MB
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    api_key TEXT UNIQUE,
    CHECK (email IS NOT NULL OR wallet_address IS NOT NULL)
);
```

**Indexes:**
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_wallet ON users(wallet_address);
CREATE INDEX idx_users_api_key ON users(api_key);
```

### Pins Table

```sql
CREATE TABLE pins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    cid TEXT NOT NULL,
    filename TEXT,
    size INTEGER NOT NULL,
    upload_type TEXT DEFAULT 'pin',  -- 'pin' or 'upload'
    pinned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active',
    FOREIGN KEY(user_id) REFERENCES users(id),
    UNIQUE(user_id, cid)
);
```

**Indexes:**
```sql
CREATE INDEX idx_pins_user_id ON pins(user_id);
CREATE INDEX idx_pins_cid ON pins(cid);
CREATE INDEX idx_pins_pinned_at ON pins(pinned_at);
CREATE INDEX idx_pins_status ON pins(status);
```

### Audit Log Table

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    user_id INTEGER,
    ip_address TEXT,
    cid TEXT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

**Indexes:**
```sql
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_event_type ON audit_log(event_type);
```

### Request Log Table (GDPR)

```sql
CREATE TABLE request_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    method TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

**Indexes:**
```sql
CREATE INDEX idx_request_timestamp ON request_log(timestamp);
CREATE INDEX idx_request_ip ON request_log(ip_address);
```

### Entity Relationship Diagram

```
┌─────────────┐
│    users    │
│─────────────│
│ id (PK)     │
│ email       │
│ password_   │◄──────┐
│   hash      │       │
│ storage_    │       │
│   used      │       │
│ storage_    │       │
│   limit     │       │
└─────────────┘       │
       │              │
       │ 1:N          │ 1:N
       │              │
       ▼              │
┌─────────────┐       │
│    pins     │       │
│─────────────│       │
│ id (PK)     │       │
│ user_id(FK) │───────┤
│ cid         │       │
│ size        │       │
│ upload_type │       │
└─────────────┘       │
                      │
┌─────────────┐       │
│ audit_log   │       │
│─────────────│       │
│ id (PK)     │       │
│ user_id(FK) │───────┤
│ event_type  │       │
│ ip_address  │       │
└─────────────┘       │
                      │
┌─────────────┐       │
│request_log  │       │
│─────────────│       │
│ id (PK)     │       │
│ user_id(FK) │───────┘
│ endpoint    │
│ ip_address  │
└─────────────┘
```

---

## IPFS Integration

### Architecture

```
ServeBeer Application
        │
        │ HTTP API Calls
        │
        ▼
┌───────────────────┐
│   IPFS Daemon     │
│   (Kubo/go-ipfs)  │
│                   │
│  Port: 5001 (API) │
│  Port: 8080 (GW)  │
│  Port: 4001 (P2P) │
└─────────┬─────────┘
          │
          │ P2P Protocol
          │
          ▼
┌───────────────────┐
│   IPFS Network    │
│  (Global P2P)     │
└───────────────────┘
```

### API Communication

**Base Configuration:**
```python
IPFS_API_URL = 'http://localhost:5001/api/v0'
```

**Request Pattern:**
```python
def ipfs_api_call(endpoint, params=None, files=None, method='POST'):
    url = f"{IPFS_API_URL}/{endpoint}"
    
    if method == 'POST':
        response = requests.post(url, params=params, files=files)
    else:
        response = requests.get(url, params=params)
    
    return response.json()
```

### Key Operations

**1. Pin CID:**
```python
ipfs_api_call('pin/add', params={'arg': cid})
# Response: {'Pins': [cid]}
```

**2. Upload File:**
```python
files = {'file': (filename, file_stream, mimetype)}
ipfs_api_call('add', files=files)
# Response: {'Hash': cid, 'Size': size}
```

**3. Check CID:**
```python
ipfs_api_call('object/stat', params={'arg': cid})
# Response: {'CumulativeSize': size, ...}
```

**4. Get Version:**
```python
ipfs_api_call('version')
# Response: {'Version': '0.18.1', ...}
```

### Error Handling

```python
try:
    result = ipfs_api_call('pin/add', params={'arg': cid})
    if not result.get('success'):
        # Handle IPFS error
        return {"error": result.get('error')}
except requests.exceptions.RequestException as e:
    # Handle network error
    return {"error": str(e)}
```

### Content Addressing

**CID Format:**
- Base58 encoded (v0): `QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco`
- CIDv1 format: `bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi`

**CID Validation:**
- Length check (46+ characters for v0)
- Prefix check (`Qm` for v0, `bafy` for v1)
- Existence check via `object/stat`

---

## Authentication & Security

### Session Management

**Flask Sessions:**
```python
# Configuration
SESSION_COOKIE_SECURE = False  # True for HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 30 days
```

**Session Data:**
```python
session['user_id'] = user.id  # Only user ID stored
# No sensitive data in session
```

### Password Security

**Hashing:**
```python
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
```

**Note:** SHA-256 is used for simplicity. For production enhancement, consider:
- bcrypt
- argon2
- PBKDF2

### API Key Generation

```python
def generate_api_key(user_id):
    data = f"{user_id}-{datetime.now().isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()
```

### Audit Logging

**Logged Events:**
- `LOGIN_SUCCESS` / `LOGIN_FAILED`
- `REGISTER_SUCCESS` / `REGISTER_FAILED`
- `CID_PINNED`
- `FILE_UPLOADED`
- `UPLOAD_FAILED`
- `CONTACT_FORM`

**Log Function:**
```python
def log_security_event(event_type, user_id, ip_address, details):
    logging.info(f"SECURITY: {event_type} | {user_id} | {ip_address}")
    
    conn.execute('''
        INSERT INTO audit_log 
        (event_type, user_id, ip_address, details)
        VALUES (?, ?, ?, ?)
    ''', (event_type, user_id, ip_address, details))
```

### GDPR Compliance

**Request Logging:**
```python
@app.before_request
def gdpr_logging():
    conn.execute('''
        INSERT INTO request_log 
        (ip_address, method, endpoint, user_agent, user_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        request.remote_addr,
        request.method,
        request.endpoint,
        request.headers.get('User-Agent'),
        session.get('user_id')
    ))
```

**Data Retention:**
- Logs retained indefinitely (consider implementing rotation)
- Users can request data export
- Users can request account deletion

---

## Storage Management

### Quota System

**Free Tier:**
```python
FREE_TIER_LIMIT = 250 * 1024 * 1024  # 250MB
```

**Paid Tier:**
```python
PAID_TIER_LIMIT = 1024 * 1024 * 1024  # 1GB
```

### Storage Calculation

**Safe Size Handling:**
```python
# Get size from IPFS
size = upload_result.get('Size', '0')

# Safe conversion with fallback
try:
    size = int(size) if size else 0
except (ValueError, TypeError):
    size = 0

# Fallback to file size if IPFS size is 0
if size == 0 and hasattr(file, 'content_length'):
    size = int(file.content_length)
```

### Quota Enforcement

**Beta Mode (TESTING_MODE=True):**
```python
if TESTING_MODE:
    # Skip all quota checks
    pass
```

**Production Mode:**
```python
if not TESTING_MODE:
    current_storage = user['storage_used']
    if current_storage + size > user['storage_limit']:
        return "Error: Storage limit exceeded", 413
```

### Storage Updates

```sql
UPDATE users 
SET storage_used = storage_used + ?
WHERE id = ?
```

**Atomic operation** - no race conditions with single-user SQLite.

---

## API Design

### RESTful Principles

**Resource-Based URLs:**
- `/api/pin` - Pin operations
- `/upload` - Upload operations
- `/api/dashboard/*` - Dashboard data

**HTTP Methods:**
- `GET` - Retrieve data
- `POST` - Create/modify data

**Status Codes:**
- `200` - Success
- `400` - Bad request
- `401` - Unauthorized
- `404` - Not found
- `409` - Conflict
- `413` - Payload too large
- `500` - Server error

### Response Format

**Success:**
```json
{
  "success": true,
  "cid": "QmXoypizjW3...",
  "size": 2097152
}
```

**Error:**
```json
{
  "error": "Storage limit exceeded",
  "code": 413
}
```

Or plain text:
```
Error: CID not found in IPFS network
```

### Authentication Flow

```
1. User → POST /login
2. Server validates credentials
3. Server creates session
4. Server sets cookie
5. User → GET /dashboard (with cookie)
6. Server validates session
7. Server returns protected content
```

---

## Deployment Architecture

### Single-Node Deployment (Current)

```
┌──────────────────────────────────────┐
│      Raspberry Pi 400                │
│  ┌────────────────────────────────┐  │
│  │  Debian 12 Bookworm            │  │
│  │                                │  │
│  │  ┌──────────┐  ┌───────────┐  │  │
│  │  │  Flask   │  │   IPFS    │  │  │
│  │  │   App    │  │  Daemon   │  │  │
│  │  │ :5000    │  │  :5001    │  │  │
│  │  └──────────┘  └───────────┘  │  │
│  │                                │  │
│  │  ┌──────────┐                 │  │
│  │  │ SQLite   │                 │  │
│  │  │ Database │                 │  │
│  │  └──────────┘                 │  │
│  └────────────────────────────────┘  │
│                                      │
│  Internet (Fiber)                    │
└──────────────────────────────────────┘
```

### Docker Deployment (Planned)

```
┌───────────────────────────────────────────┐
│           Docker Host                     │
│  ┌─────────────────────────────────────┐  │
│  │  docker-compose.yml                 │  │
│  │                                     │  │
│  │  ┌─────────┐  ┌────────┐          │  │
│  │  │ServeBeer│  │  IPFS  │          │  │
│  │  │Container│  │Container│          │  │
│  │  └────┬────┘  └───┬────┘          │  │
│  │       │           │               │  │
│  │       └───────┬───┘               │  │
│  │               │                   │  │
│  │         ┌─────▼─────┐             │  │
│  │         │  Volumes  │             │  │
│  │         │ (database)│             │  │
│  │         └───────────┘             │  │
│  └─────────────────────────────────────┘  │
└───────────────────────────────────────────┘
```

### Production Deployment (Future)

```
┌──────────────────────────────────────────────┐
│              Load Balancer                   │
│         (nginx / HAProxy)                    │
└─────────┬──────────────────┬─────────────────┘
          │                  │
    ┌─────▼──────┐    ┌──────▼──────┐
    │ServeBeer #1│    │ServeBeer #2 │
    │  + IPFS    │    │  + IPFS     │
    └─────┬──────┘    └──────┬──────┘
          │                  │
          └────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │   PostgreSQL      │
         │   (Shared DB)     │
         └───────────────────┘
```

---

## Performance Considerations

### Raspberry Pi Constraints

**Hardware Limits:**
- 4GB RAM (Pi 400)
- ARM CPU (limited processing power)
- SD Card storage (slower I/O)
- Network bandwidth

**Optimizations:**
- Lightweight Flask (no heavy frameworks)
- SQLite (no database server overhead)
- Direct IPFS API calls (no middleware)
- Minimal frontend JavaScript
- No client-side build process

### Scaling Strategies

**Vertical Scaling:**
- Upgrade to Raspberry Pi 5
- Add USB SSD for database
- Increase RAM allocation

**Horizontal Scaling:**
- Multiple Pi nodes
- IPFS Cluster for coordination
- Shared PostgreSQL database
- Load balancer

### Bottlenecks

1. **IPFS Operations** - I/O bound
2. **Database Writes** - Sequential on SQLite
3. **Network Bandwidth** - Residential connection
4. **Storage Space** - SD card capacity

---

## Security Architecture

### Defense Layers

**1. Input Validation**
- CID format checking
- File size validation
- SQL injection prevention (prepared statements)
- XSS prevention (template escaping)

**2. Authentication**
- Session-based auth
- Secure cookie flags
- Password hashing
- Rate limiting (to be added)

**3. Authorization**
- User-specific data isolation
- Storage quota enforcement
- Pin ownership validation

**4. Audit Trail**
- All actions logged
- IP address tracking
- Timestamp recording
- Event type categorization

**5. GDPR Compliance**
- Request logging
- User consent tracking
- Data export capability
- Right to deletion

---

## Future Enhancements

### Planned Improvements

**Short Term:**
- Rate limiting implementation
- Better password hashing (bcrypt)
- API key authentication (Bearer tokens)
- Webhook notifications

**Medium Term:**
- Redis caching layer
- PostgreSQL migration
- Multi-node support
- IPFS Cluster integration

**Long Term:**
- Microservices architecture
- Message queue (RabbitMQ/Redis)
- Distributed tracing
- Advanced analytics

---

## Maintenance & Operations

### Monitoring Points

**Application Health:**
- `/health` endpoint
- Session count
- Active users
- Error rates

**IPFS Health:**
- Daemon status
- Peer count
- Repo size
- Pin count

**Database Health:**
- Connection pool
- Query performance
- Disk usage
- Backup status

### Backup Strategy

**What to Backup:**
- SQLite database
- IPFS repository (optional)
- Configuration files
- SSL certificates

**Backup Schedule:**
- Daily automated backups
- 30-day retention
- Off-site storage (S3)

### Upgrade Process

1. Backup everything
2. Stop services
3. Update code
4. Run migrations
5. Test thoroughly
6. Start services
7. Verify health

---

## Conclusion

ServeBeer's architecture balances simplicity with functionality, optimized for resource-constrained hardware while maintaining security and scalability. The monolithic Flask application provides ease of deployment, while the modular code structure allows for future enhancements.

**Key Strengths:**
- Simple, understandable codebase
- Minimal dependencies
- Resource efficient
- IPFS native
- Security focused

**Areas for Growth:**
- Horizontal scaling
- Advanced monitoring
- Rate limiting
- Enhanced authentication

---

*ServeBeer IPFS CDN - Guerrilla Infrastructure*  
*Architecture Documentation v1.0*  
*© 2025 NFTomczain Universe*