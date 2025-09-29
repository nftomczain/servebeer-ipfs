# 📘 ServeBeer IPFS API Documentation

**Version:** 1.0.0  
**Base URL:** `https://cda.servebeer.com:5000` (Production) / `http://localhost:5000` (Development)  
**Authentication:** Session-based (Cookie) or API Key

---

## 🎯 Overview

ServeBeer provides a RESTful API for IPFS content pinning and management. The service operates in two modes:
- **Beta Mode** (`TESTING_MODE=True`): All features unlocked, no storage limits
- **Production Mode** (`TESTING_MODE=False`): Tiered service with storage limits

### Key Features

- ✅ Session-based authentication
- ✅ IPFS CID pinning
- ✅ Direct file upload to IPFS
- ✅ Real-time dashboard with statistics
- ✅ Audit logging for security
- ✅ GDPR-compliant request logging

---

## 🔐 Authentication

### Session-Based Authentication (Primary Method)

All API endpoints use **session cookies** after login. The application uses Flask sessions with secure cookie configuration.

#### Session Configuration
```python
SESSION_COOKIE_SECURE=False      # Set to True for HTTPS in production
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE='Lax'
PERMANENT_SESSION_LIFETIME=30 days
```

### API Key Authentication (Available but not actively used)

Users have API keys stored in database, but current implementation doesn't use Bearer token authentication. Keys can be generated but are not required for API access.

---

## 📋 API Endpoints

### 🏠 Public Endpoints

#### `GET /`
Landing page with project information

**Response:** HTML page

---

#### `GET /health`
Health check endpoint for monitoring

**Response:**
```json
{
  "status": "healthy",
  "ipfs": "ok",
  "database": "ok",
  "testing_mode": true,
  "timestamp": "2025-01-27T15:30:00.123456"
}
```

**Status Codes:**
- `200 OK` - System healthy
- Service returns status even if degraded

---

#### `GET /status`
System status dashboard with real-time statistics

**Response:** HTML page with:
- Total users, pins, storage
- Recent activity feed
- System uptime
- IPFS node status

**Also available as JSON:**
```bash
GET /api/status
```

---

#### `GET /sponsors`
Sponsor tiers and community funding page

**Response:** HTML page

---

### 🔑 Authentication Endpoints

#### `POST /register`
Register new user account

**Form Data:**
```
email: user@example.com
password: your_secure_password
agree_terms: on
```

**Success Response:**
- Redirects to `/dashboard`
- Sets session cookie
- Logs `REGISTER_SUCCESS` event

**Error Response:**
- Flash message: "Email already exists"
- Returns to registration page

---

#### `POST /login`
User login

**Form Data:**
```
email: user@example.com
password: your_password
```

**Success Response:**
- Redirects to `/dashboard`
- Sets session cookie with `user_id`
- Logs `LOGIN_SUCCESS` event

**Error Response:**
- Flash message: "Invalid email or password"
- Logs `LOGIN_FAILED` event

---

#### `GET /logout`
User logout

**Response:**
- Clears session
- Redirects to `/`

---

### 📌 IPFS Operations

#### `GET /api/pin` or `GET /pin`
Display pin form

**Response:** HTML form for pinning CID

---

#### `POST /api/pin`
Pin existing IPFS CID to node

**Authentication:** Required (session)

**Form Data:**
```
cid: QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco
filename: my-file.jpg (optional)
```

**Success Response:**
- Redirects to `/dashboard`
- Logs `CID_PINNED` event

**Error Responses:**
- `400 Bad Request` - Missing CID
- `401 Unauthorized` - Not logged in
- `404 Not Found` - CID not found in IPFS network
- `409 Conflict` - CID already pinned by user
- `413 Payload Too Large` - Storage limit exceeded (production mode)
- `500 Internal Server Error` - IPFS pin operation failed

**Process:**
1. Validates CID exists in IPFS network
2. Gets content size via `ipfs object/stat`
3. Checks user storage limits (skipped in beta mode)
4. Pins content via `ipfs pin/add`
5. Updates database and user storage quota

---

#### `GET /upload`
Display file upload form

**Authentication:** Required (session)

**Response:** HTML upload form

---

#### `POST /upload`
Upload file directly to IPFS

**Authentication:** Required (session)

**Form Data (multipart/form-data):**
```
file: [binary file]
description: "My awesome file" (optional)
```

**Success Response:**
```html
<!-- upload_success.html -->
Upload successful!
CID: QmNewHash...
Filename: uploaded-file.jpg
Size: 1048576 bytes
```

**Error Responses:**
- `400 Bad Request` - No file selected
- `401 Unauthorized` - Not logged in
- `413 Payload Too Large` - Storage limit exceeded (production mode)
- `500 Internal Server Error` - Upload failed

**Process:**
1. Receives file via multipart upload
2. Uploads to IPFS via `ipfs add`
3. Gets CID and size from IPFS response
4. Checks storage limits (skipped in beta mode)
5. Saves pin record with `upload_type='upload'`
6. Logs `FILE_UPLOADED` event

---

### 📊 Dashboard API Endpoints

All dashboard endpoints require active session (`user_id` in session).

#### `GET /dashboard`
Main dashboard interface (v2)

**Authentication:** Required

**Response:** HTML dashboard with real-time data loading

---

#### `GET /api/dashboard/stats`
Get user statistics

**Authentication:** Required (session)

**Response:**
```json
{
  "storage_used_mb": 18.4,
  "storage_limit_mb": 250,
  "storage_available_mb": 231.6,
  "storage_growth_percent": 12.3,
  "total_pins": 15,
  "today_pins": 3,
  "bandwidth_gb": 0.013,
  "bandwidth_growth": "+0.3",
  "uptime_percent": 99.7,
  "upload_count": 8,
  "pin_count": 7,
  "failed_count": 0,
  "user_email": "user@example.com",
  "user_tier": "free"
}
```

---

#### `GET /api/dashboard/network`
Get IPFS network health data

**Authentication:** Required (session)

**Response:**
```json
{
  "ipfs_version": "go-ipfs v0.18.1",
  "peers_connected": 42,
  "repo_size_mb": 1247.3,
  "bandwidth_in_mb": 856.2,
  "bandwidth_out_mb": 342.8,
  "blocks_stored": 15642,
  "node_status": "online",
  "last_check": "2025-01-27T15:30:00Z"
}
```

---

#### `GET /api/dashboard/files`
Get user's pinned files

**Authentication:** Required (session)

**Query Parameters:**
- `search` (optional) - Filter by filename or CID

**Request:**
```bash
GET /api/dashboard/files?search=photo
```

**Response:**
```json
{
  "files": [
    {
      "filename": "photo.jpg",
      "cid": "QmXoypizjW3Wk...",
      "cid_short": "QmXoypizjW3Wk...6uco",
      "size_kb": 2048,
      "upload_type": "upload",
      "pinned_at": "2025-01-27 14:23:15"
    }
  ]
}
```

**Limits:**
- Returns max 50 most recent files
- Sorted by `pinned_at DESC`

---

#### `GET /api/dashboard/activity`
Get recent user activity

**Authentication:** Required (session)

**Response:**
```json
{
  "activities": [
    {
      "icon": "upload",
      "message": "Uploaded file to IPFS",
      "time": "Recently",
      "timestamp": "2025-01-27 15:30:00"
    },
    {
      "icon": "pin",
      "message": "Pinned content to IPFS",
      "time": "Recently",
      "timestamp": "2025-01-27 14:15:22"
    }
  ]
}
```

**Event Types:**
- `CID_PINNED` → icon: "pin"
- `FILE_UPLOADED` → icon: "upload"
- `LOGIN_SUCCESS` → icon: "login"

**Limits:**
- Returns 10 most recent activities

---

#### `GET /api/dashboard/analytics`
Get analytics data for charts

**Authentication:** Required (session)

**Response:**
```json
{
  "storage_usage": {
    "labels": ["2025-01-25", "2025-01-26", "2025-01-27"],
    "data": [5.2, 12.8, 18.4]
  },
  "pin_activity": {
    "labels": ["2025-01-25", "2025-01-26", "2025-01-27"],
    "uploads": [2, 1, 3],
    "pins": [1, 2, 1]
  },
  "bandwidth_usage": {
    "labels": ["2025-01-25", "2025-01-26", "2025-01-27"],
    "data": [3.6, 9.0, 12.9]
  }
}
```

**Data Period:** Last 30 days, grouped by date

---

### 📧 Contact & Legal

#### `POST /contact`
Send contact form email

**Form Data:**
```
name: John Doe
email: john@example.com
subject: Technical Support
message: Your message here...
```

**Success Response:**
```html
<!-- Success page with confirmation -->
✅ Email wysłany pomyślnie!
```

**Email Destination:** `tmpnft@gmail.com`

**SMTP Configuration:**
- Server: `smtp.gmail.com:587`
- Uses STARTTLS
- App-specific password required

---

#### `GET /terms`
Terms of Service page

---

#### `GET /cookies`
Cookie Policy page

---

### 🔧 System Status Endpoints

#### `GET /api/status`
JSON system status

**Response:**
```json
{
  "total_users": 42,
  "total_pins": 156,
  "total_storage_mb": 1247.3,
  "recent_events": 23,
  "uptime_percent": 99.7,
  "mode": "BETA",
  "versions": {
    "ipfs": "go-ipfs v0.18.1",
    "flask": "v2.3.0"
  }
}
```

---

#### `GET /api/status/activity`
Recent system activity

**Response:**
```json
{
  "activities": [
    {
      "type": "FILE_UPLOADED",
      "user": "user@example.com",
      "timestamp": "2025-01-27T15:30:00Z",
      "details": "CID: Qm..."
    }
  ]
}
```

---

#### `GET /api/status/export`
Export complete status data

**Response:**
```json
{
  "total_users": 42,
  "total_pins": 156,
  "total_storage_mb": 1247.3,
  "recent_activity": [...],
  "export_timestamp": "2025-01-27T15:30:00Z",
  "version": "1.0"
}
```

---

## 🗄️ Database Schema

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
)
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
)
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
)
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
)
```

---

## 🔒 Security Features

### Authentication
- ✅ Session-based with secure cookies
- ✅ Password hashing (SHA-256)
- ✅ API key generation (SHA-256)
- ✅ Email uniqueness validation

### Audit Logging
All critical events are logged:
- `LOGIN_SUCCESS` / `LOGIN_FAILED`
- `REGISTER_SUCCESS` / `REGISTER_FAILED`
- `CID_PINNED`
- `FILE_UPLOADED`
- `UPLOAD_FAILED`
- `CONTACT_FORM`

### GDPR Compliance
- ✅ Request logging (IP, endpoint, user agent)
- ✅ Before request middleware logs all API calls
- ✅ Cookie consent required
- ✅ Data export available

### Input Validation
- ✅ CID existence check before pinning
- ✅ Storage limit enforcement (production mode)
- ✅ Duplicate pin prevention
- ✅ File upload validation

---

## 🚀 IPFS Integration

### IPFS API Calls

The application uses `requests` library to communicate with local IPFS daemon:

```python
IPFS_API_URL = 'http://localhost:5001/api/v0'
```

### Supported IPFS Operations

#### Pin CID
```python
ipfs_api_call('pin/add', params={'arg': cid}, method='POST')
```

#### Upload File
```python
ipfs_api_call('add', files={'file': (filename, stream, mimetype)}, method='POST')
```

#### Check CID Stats
```python
ipfs_api_call('object/stat', params={'arg': cid}, method='POST')
```

#### Get IPFS Version
```python
ipfs_api_call('version', method='POST')
```

---

## 📊 Storage Limits

### Beta Mode (`TESTING_MODE=True`)
- ✅ **No storage limits**
- ✅ **No rate limits**
- ✅ **All features unlocked**

### Production Mode (`TESTING_MODE=False`)

#### Free Tier
- **Storage Limit:** 250 MB (`FREE_TIER_LIMIT`)
- **Enforcement:** Active
- **Upgrade:** Required for more storage

#### Paid Tier
- **Storage Limit:** 1 GB (`PAID_TIER_LIMIT`)
- **Enforcement:** Active
- **Features:** Priority support

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Application
SECRET_KEY=your-secret-key-change-in-production
TESTING_MODE=True

# SSL/TLS
SSL_ENABLED=false
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem

# IPFS
IPFS_API_URL=http://localhost:5001/api/v0

# Database
DATABASE_PATH=database/servebeer.db

# Storage Limits (bytes)
FREE_TIER_LIMIT=262144000   # 250MB
PAID_TIER_LIMIT=1073741824  # 1GB
```

---

## 🐛 Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Operation completed |
| 400 | Bad Request | Missing required field |
| 401 | Unauthorized | Not logged in |
| 404 | Not Found | CID not in IPFS network |
| 409 | Conflict | CID already pinned |
| 413 | Payload Too Large | Storage limit exceeded |
| 500 | Server Error | IPFS operation failed |

### Error Response Format

**HTML Errors:**
```html
Error: CID not found in IPFS network
```

**JSON Errors:**
```json
{
  "error": "Authentication required"
}
```

---

## 🧪 Testing

### Manual Testing Endpoints

```bash
# Health check
curl http://localhost:5000/health

# System status
curl http://localhost:5000/api/status

# Test dashboard (requires login)
curl http://localhost:5000/test-dashboard-api

# GDPR logs (admin)
curl http://localhost:5000/admin/check-logs
```

### Database Testing

```bash
# Check audit logs
sqlite3 database/servebeer.db "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10"

# Check request logs
sqlite3 database/servebeer.db "SELECT * FROM request_log ORDER BY timestamp DESC LIMIT 10"

# Check user storage
sqlite3 database/servebeer.db "SELECT email, storage_used, storage_limit FROM users"
```

---

## 📞 Support

- **Live Demo:** https://cda.servebeer.com:5000
- **Email:** tmpnft@gmail.com
- **GitHub:** https://github.com/nftomczain/servebeer-ipfs
- **Project:** pi-grade.nftomczain.eth.limo

---

## 🔄 Version History

**v1.0.0** - Current Version
- Session-based authentication
- IPFS pin and upload functionality
- Real-time dashboard with analytics
- GDPR-compliant logging
- Beta testing mode
- Contact form with email integration
- SSL/TLS support

---

## 📝 Notes

### Important Implementation Details

1. **Authentication:** Currently uses **session cookies only**. API keys are generated but not actively used for Bearer authentication.

2. **Storage Calculation:** File sizes are safely handled with fallbacks:
   - IPFS returns size in `CumulativeSize` or `Size` field
   - Fallback to `0` if size unavailable
   - Production mode enforces limits, beta mode skips checks

3. **CID Validation:** Before pinning, system checks if CID exists in IPFS network via `object/stat` endpoint.

4. **Email Integration:** Contact form sends real emails via Gmail SMTP with app-specific password.

5. **SSL Support:** Optional HTTPS on port 443 (requires root access).

---

*ServeBeer IPFS CDN - Guerrilla Infrastructure*  
*"Fire beneath the ashes, code as memory" | 0x660C*  
*© 2025 NFTomczain Universe*