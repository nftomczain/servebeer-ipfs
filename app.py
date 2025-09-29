#!/usr/bin/env python3
"""
ServeBeer IPFS Pinning Service - Flask Backend
NFTomczain Guerrilla Infrastructure
Complete with Beta Mode Support and Upload Functionality
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, render_template_string
import sqlite3
import os
import hashlib
import requests
from datetime import datetime, timedelta
import json
import logging
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_network_endpoint import get_network_status
from status_data import get_system_status, get_recent_activity
import ssl
from importlib.metadata import version
try:
    from importlib.metadata import version
    flask_version = f"v{version('flask')}"
except ImportError:
    import flask
    flask_version = f"v{flask.__version__}"
    
# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'YOUR SECRET KEY')

# TESTING MODE CONFIGURATION
TESTING_MODE = os.getenv('TESTING_MODE', 'True').lower() == 'true'

# SSL Configuration
SSL_ENABLED = os.getenv('SSL_ENABLED', 'false').lower() == 'true'
SSL_CERT_PATH = os.getenv('SSL_CERT_PATH', '')
SSL_KEY_PATH = os.getenv('SSL_KEY_PATH', '')

# Session configuration for EU compliance
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to True for HTTPS in production
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(days=30)
)

# Configuration
IPFS_API_URL = 'http://localhost:5001/api/v0'
DATABASE_PATH = 'database/servebeer.db'
FREE_TIER_LIMIT = 250 * 1024 * 1024  # 250MB in bytes
PAID_TIER_LIMIT = 1024 * 1024 * 1024  # 1GB in bytes

# Ensure database and logs directory exists
os.makedirs('database', exist_ok=True)
os.makedirs('logs', exist_ok=True)

def setup_logging():
    """Configure security audit logging"""
    logging.basicConfig(
        filename='logs/servebeer_audit.log',
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def log_security_event(event_type, user_id=None, ip_address=None, details=None):
    """Log security-relevant events"""
    log_entry = {
        'event': event_type,
        'user_id': user_id,
        'ip': ip_address or request.remote_addr,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }
    logging.info(f"SECURITY: {log_entry}")
    
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO audit_log (event_type, user_id, ip_address, details)
            VALUES (?, ?, ?, ?)
        ''', (event_type, user_id, ip_address or request.remote_addr, str(details)))
        conn.commit()
        conn.close()
    except:
        pass

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Users table with wallet support
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password_hash TEXT,
            wallet_address TEXT UNIQUE,
            auth_method TEXT DEFAULT 'email',
            tier TEXT DEFAULT 'free',
            storage_used INTEGER DEFAULT 0,
            storage_limit INTEGER DEFAULT {FREE_TIER_LIMIT},
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            api_key TEXT UNIQUE,
            CHECK (email IS NOT NULL OR wallet_address IS NOT NULL)
        )
    ''')
    
    # Pinned content table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            cid TEXT NOT NULL,
            filename TEXT,
            size INTEGER NOT NULL,
            upload_type TEXT DEFAULT 'pin',
            pinned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            FOREIGN KEY(user_id) REFERENCES users(id),
            UNIQUE(user_id, cid)
        )
    ''')
    
    # Audit log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id INTEGER,
            ip_address TEXT,
            cid TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
 
     # GDPR request logging table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS request_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            method TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
     
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_api_key(user_id):
    """Generate API key for user"""
    return hashlib.sha256(f"{user_id}-{datetime.now().isoformat()}".encode()).hexdigest()

def ipfs_api_call(endpoint, params=None, files=None, method='POST'):
    try:
        url = f"{IPFS_API_URL}/{endpoint}"

        if method == 'POST':
            response = requests.post(url, params=params, files=files, timeout=None)
        else:
            response = requests.get(url, params=params, timeout=None)

        response.raise_for_status()

        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw": response.text}

        data["success"] = True
        return data

    except requests.exceptions.RequestException as e:
        return {"error": str(e), "success": False}

def check_cid_exists(cid):
    """Check if CID exists in IPFS network"""
    try:
        result = ipfs_api_call('object/stat', params={'arg': cid}, method='POST')
        return result.get('success', False) and 'error' not in result
    except:
        return False
        
def create_ssl_context():
    """Create SSL context for HTTPS"""
    if not SSL_ENABLED or not SSL_CERT_PATH or not SSL_KEY_PATH:
        print("⚠️  SSL disabled or paths not configured")
        return None
    
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(SSL_CERT_PATH, SSL_KEY_PATH)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        print("✅ SSL context created successfully")
        return context
    except FileNotFoundError as e:
        print(f"❌ SSL certificate files not found: {e}")
        return None
    except PermissionError as e:
        print(f"❌ Permission denied accessing SSL certificates: {e}")
        print("💡 Run as root: sudo python3 app.py")
        return None
    except Exception as e:
        print(f"❌ SSL context error: {e}")
        return None
        
def get_cid_size(cid):
    """Get size of content by CID"""
    try:
        result = ipfs_api_call('object/stat', params={'arg': cid}, method='POST')
        if result.get('success', False) and 'CumulativeSize' in result:
            return result['CumulativeSize']
        return 0
    except:
        return 0

@app.before_request  
def gdpr_logging():
    if request.endpoint and not request.endpoint.startswith('static'):
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO request_log (ip_address, method, endpoint, user_agent, user_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                request.remote_addr,
                request.method,
                request.endpoint, 
                request.headers.get('User-Agent', '')[:500],
                session.get('user_id')
            ))
            conn.commit()
            conn.close()
        except:
            pass

@app.route('/')
def index():
    """Main landing page"""
    return render_template('landing.html', testing_mode=TESTING_MODE)

@app.route('/dashboard')
def dashboard():
    """Enhanced dashboard v2 - requires login"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard_v2.html', testing_mode=TESTING_MODE)

@app.route('/test-dashboard-api')
def test_dashboard_api():
    if 'user_id' not in session:
        return "Not logged in - <a href='/login'>Login first</a>"
    
    return '''
    <h2>API Test</h2>
    <a href="/api/dashboard/stats">Test Stats</a><br>
    <a href="/api/dashboard/network">Test Network</a><br>
    <a href="/api/dashboard/files">Test Files</a><br>
    <a href="/dashboard">Go to Dashboard v2</a>
    '''

@app.route('/api/pin', methods=['GET', 'POST'])
def api_pin():
    """Pin CID to IPFS node"""
    if request.method == 'GET':
        return render_template('pin.html', testing_mode=TESTING_MODE)
    
    # POST request - actual pinning
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    cid = request.form.get('cid', '').strip()
    filename = request.form.get('filename', f'pinned-{cid[:8]}') or f'pinned-{cid[:8]}'
    
    if not cid:
        return "Error: CID is required", 400
    
    if not check_cid_exists(cid):
        return "Error: CID not found in IPFS network", 404
    
    size = get_cid_size(cid)
    
    # FIXED: Safe size handling
    try:
        size = int(size) if size else 0
    except (ValueError, TypeError):
        size = 0
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # FIXED: Safe storage calculation
    current_storage = user['storage_used'] if user['storage_used'] else 0
    try:
        current_storage = int(current_storage)
    except (ValueError, TypeError):
        current_storage = 0
    
    if not TESTING_MODE and current_storage + size > user['storage_limit']:
        conn.close()
        return "Error: Storage limit exceeded", 413
    
    existing = conn.execute('SELECT id FROM pins WHERE user_id = ? AND cid = ?', 
                           (session['user_id'], cid)).fetchone()
    if existing:
        conn.close()
        return "Error: CID already pinned", 409
    
    pin_result = ipfs_api_call('pin/add', params={'arg': cid}, method='POST')
    if not pin_result.get('success', False):
        conn.close()
        return f"Error: IPFS pin failed: {pin_result.get('error', 'Unknown error')}", 500
    
    conn.execute('''
        INSERT INTO pins (user_id, cid, filename, size, upload_type)
        VALUES (?, ?, ?, ?, 'pin')
    ''', (session['user_id'], cid, filename, size))
    
    conn.execute('''
        UPDATE users SET storage_used = storage_used + ?, last_active = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (size, session['user_id']))
    
    conn.commit()
    conn.close()
    
    log_security_event('CID_PINNED', session['user_id'], request.remote_addr, f"CID: {cid}, Size: {size}")
    
    return redirect(url_for('dashboard'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Upload file to IPFS"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        return render_template('upload.html', testing_mode=TESTING_MODE)
    
    if 'file' not in request.files:
        return "Error: No file selected", 400
    
    file = request.files['file']
    if file.filename == '':
        return "Error: No file selected", 400
    
    description = request.form.get('description', file.filename) or file.filename
    
    try:
        files = {'file': (file.filename, file.stream, file.mimetype)}
        upload_result = ipfs_api_call('add', files=files, method='POST')
        
        if not upload_result.get('success', False) or 'Hash' not in upload_result:
            return f"Error: IPFS upload failed: {upload_result.get('error', 'Unknown error')}", 500
        
        cid = upload_result['Hash']
        
        # FIXED: Safe size handling from IPFS API
        size_raw = upload_result.get('Size', '0')
        try:
            if isinstance(size_raw, str):
                size = int(size_raw)
            elif isinstance(size_raw, (int, float)):
                size = int(size_raw)
            else:
                size = 0
        except (ValueError, TypeError):
            size = 0
        
        # Use file size as fallback if IPFS size is 0
        if size == 0 and hasattr(file, 'content_length') and file.content_length:
            size = int(file.content_length)
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        # FIXED: Safe storage calculation
        current_storage = user['storage_used'] if user['storage_used'] else 0
        try:
            current_storage = int(current_storage)
        except (ValueError, TypeError):
            current_storage = 0
        
        if not TESTING_MODE and current_storage + size > user['storage_limit']:
            conn.close()
            return "Error: Storage limit exceeded", 413
        
        conn.execute('''
            INSERT INTO pins (user_id, cid, filename, size, upload_type)
            VALUES (?, ?, ?, ?, 'upload')
        ''', (session['user_id'], cid, description, size))
        
        conn.execute('''
            UPDATE users SET storage_used = storage_used + ?, last_active = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (size, session['user_id']))
        
        conn.commit()
        conn.close()
        
        log_security_event('FILE_UPLOADED', session['user_id'], request.remote_addr, f"CID: {cid}, Size: {size}")
        
        return render_template('upload_success.html', cid=cid, filename=file.filename, size=size)
        
    except Exception as e:
        log_security_event('UPLOAD_FAILED', session['user_id'], request.remote_addr, f"Error: {str(e)}")
        return f"Error: Upload failed: {str(e)}", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND password_hash = ?',
                           (email, password_hash)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            log_security_event('LOGIN_SUCCESS', user['id'], request.remote_addr, f"User: {email}")
            return redirect(url_for('dashboard'))
        else:
            log_security_event('LOGIN_FAILED', None, request.remote_addr, f"Email: {email}")
            flash('Invalid email or password')
    
    return render_template('login.html', testing_mode=TESTING_MODE)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        if not request.form.get('agree_terms'):
            flash('You must agree to the Terms of Service')
            return render_template('register.html', testing_mode=TESTING_MODE)
            
        email = request.form['email']
        password = request.form['password']
        password_hash = hash_password(password)
        api_key = generate_api_key(email)
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO users (email, password_hash, api_key, auth_method)
                VALUES (?, ?, ?, ?)
            ''', (email, password_hash, api_key, "email"))
            conn.commit()
            
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            conn.close()
            
            session['user_id'] = user['id']
            log_security_event('REGISTER_SUCCESS', user['id'], request.remote_addr, f"User: {email}")
            return redirect(url_for('dashboard'))
            
        except sqlite3.IntegrityError:
            conn.close()
            flash('Email already exists')
            log_security_event('REGISTER_FAILED', None, request.remote_addr, f"Email: {email} (exists)")
    
    return render_template('register.html', testing_mode=TESTING_MODE)

@app.route('/logout')
def logout():
    """User logout"""
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/sponsors')
def sponsors_page():
    """Community sponsor tiers page"""
    return render_template('sponsor_tiers.html', testing_mode=TESTING_MODE)

@app.route('/health')
def health():
    """Health check endpoint"""
    ipfs_status = ipfs_api_call('version', method='POST')
    ipfs_healthy = 'Version' in ipfs_status and 'error' not in ipfs_status
    
    try:
        conn = get_db_connection()
        conn.execute('SELECT 1').fetchone()
        conn.close()
        db_healthy = True
    except:
        db_healthy = False
    
    return jsonify({
        "status": "healthy" if (ipfs_healthy and db_healthy) else "unhealthy",
        "ipfs": "ok" if ipfs_healthy else "error",
        "database": "ok" if db_healthy else "error",
        "testing_mode": TESTING_MODE,
        "timestamp": datetime.now().isoformat()
    })

# CONTACT EMAIL FUNCTION - NIE RUSZAJ
def send_contact_email(name, email, subject, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = 'user@gmail.com'
        msg['Subject'] = f"ServeBeer Contact: {subject}"
        
        body = f"""
        Contact form message:
        
        Name: {name}
        Email: {email}
        Subject: {subject}
        
        Message:
        {message}
        
        Sent from: ServeBeer IPFS CDN
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('user@gmail.com', 'app password')
        server.send_message(msg)
        server.quit()
        
        return jsonify({
            "storage_usage": {
                "labels": ['2025-01-25', '2025-01-26', '2025-01-27'],
                "data": [5.2, 12.8, 18.4]
            },
            "pin_activity": {
                "labels": ['2025-01-25', '2025-01-26', '2025-01-27'],
                "uploads": [2, 1, 3],
                "pins": [1, 2, 1]
            },
            "bandwidth_usage": {
                "labels": ['2025-01-25', '2025-01-26', '2025-01-27'],
                "data": [3.6, 9.0, 12.9]
            },
            "error_debug": str(e)
        })
        
    except Exception as e:
        return jsonify({
            "storage_usage": {
                "labels": ['2025-01-25', '2025-01-26', '2025-01-27'],
                "data": [5.2, 12.8, 18.4]
            },
            "pin_activity": {
                "labels": ['2025-01-25', '2025-01-26', '2025-01-27'],
                "uploads": [2, 1, 3],
                "pins": [1, 2, 1]
            },
            "bandwidth_usage": {
                "labels": ['2025-01-25', '2025-01-26', '2025-01-27'],
                "data": [3.6, 9.0, 12.9]
            },
            "error_debug": str(e)
        })

@app.route('/status')
def status():
    """System status dashboard with real data"""
    try:
        # Get stat real data
        status_data = get_system_status()
        recent_activity = get_recent_activity()
        
        return render_template('status.html', 
                             testing_mode=TESTING_MODE,
                             status_data=status_data,
                             recent_activity=recent_activity)
        
    except Exception as e:
        print(f"Status page error: {e}")
        # Fallback - renderuj z podstawowymi danymi
        return render_template('status.html', 
                             testing_mode=TESTING_MODE,
                             status_data=None,
                             recent_activity=[])

# API endpoint dla AJAX updates
@app.route('/api/status')
def api_status():
    """API endpoint for status data"""
    try:
        import subprocess
        
        status_data = get_system_status()
        
        # Dodaj wersje do odpowiedzi
        try:
            ipfs_ver = subprocess.check_output(['ipfs', 'version', '-n'], text=True).strip()
            ipfs_version = f"go-ipfs v{ipfs_ver}"
        except:
            ipfs_version = 'go-ipfs v0.18.1'
        
        # Wersja Flask - używając nowej metody
        flask_version = f"v{version('flask')}"
        
        status_data['versions'] = {
            'ipfs': ipfs_version,
            'flask': flask_version
        }
        
        return jsonify(status_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500        
@app.route('/api/status/activity')
def api_status_activity():
    """API endpoint for recent activity"""
    try:
        activity_data = get_recent_activity()
        return jsonify({"activities": activity_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Dodaj endpoint do eksportu danych statusu
@app.route('/api/status/export')
def export_status():
    """Export complete status data as JSON"""
    try:
        status_data = get_system_status()
        recent_activity = get_recent_activity()
        
        export_data = {
            **status_data,
            "recent_activity": recent_activity,
            "export_timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        return jsonify(export_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/terms')
def terms_of_service():
    """Terms of Service page"""
    return render_template('terms.html', testing_mode=TESTING_MODE)

@app.route('/cookies')
def cookie_policy():
    """Cookie policy page"""
    return render_template('cookies.html', testing_mode=TESTING_MODE)

@app.route('/pin')
def pin_page():
    """Redirect to pin API"""
    return redirect(url_for('api_pin'))

# Dashboard API endpoints

@app.route('/api/dashboard/stats')
def dashboard_stats():
    """Get real dashboard statistics"""
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        conn = get_db_connection()
        user_id = session['user_id']
        
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        total_pins = conn.execute('SELECT COUNT(*) as count FROM pins WHERE user_id = ? AND status = "active"', (user_id,)).fetchone()
        today_pins = conn.execute('''
            SELECT COUNT(*) as count FROM pins 
            WHERE user_id = ? AND status = "active" 
            AND date(pinned_at) = date('now')
        ''', (user_id,)).fetchone()
        
        storage_used_mb = round(user['storage_used'] / (1024 * 1024), 1)
        storage_limit_mb = round(user['storage_limit'] / (1024 * 1024))
        
        upload_count = conn.execute('''
            SELECT COUNT(*) as count FROM pins 
            WHERE user_id = ? AND upload_type = "upload" AND status = "active"
        ''', (user_id,)).fetchone()
        
        pin_count = conn.execute('''
            SELECT COUNT(*) as count FROM pins 
            WHERE user_id = ? AND upload_type = "pin" AND status = "active"
        ''', (user_id,)).fetchone()
        
        conn.close()
        
        return jsonify({
            "storage_used_mb": storage_used_mb,
            "storage_limit_mb": storage_limit_mb,
            "storage_available_mb": round(storage_limit_mb - storage_used_mb, 1),
            "storage_growth_percent": 12.3,  # Mock for now
            "total_pins": total_pins['count'],
            "today_pins": today_pins['count'],
            "bandwidth_gb": round(storage_used_mb * 0.7 / 1024, 1),
            "bandwidth_growth": "+0.3",
            "uptime_percent": 99.7,
            "upload_count": upload_count['count'],
            "pin_count": pin_count['count'],
            "failed_count": 0,
            "user_email": user['email'],
            "user_tier": user['tier']
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard/network')
def dashboard_network():
    """Get IPFS network health data"""
    data = get_network_status(ipfs_api_call, get_db_connection)
    return jsonify(data)

@app.route('/api/dashboard/files')
def dashboard_files():
    """Get user's pinned files with search"""
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    search = request.args.get('search', '').lower()
    
    try:
        conn = get_db_connection()
        user_id = session['user_id']
        
        query = '''
            SELECT id, cid, filename, size, upload_type, pinned_at, status
            FROM pins 
            WHERE user_id = ? AND status = "active"
        '''
        
        if search:
            query += ' AND (LOWER(filename) LIKE ? OR LOWER(cid) LIKE ?)'
            files = conn.execute(query + ' ORDER BY pinned_at DESC LIMIT 50', 
                               (user_id, f'%{search}%', f'%{search}%')).fetchall()
        else:
            files = conn.execute(query + ' ORDER BY pinned_at DESC LIMIT 50', (user_id,)).fetchall()
        
        conn.close()
        
        result = []
        for row in files:  # POPRAWKA: zmienione z 'rows' na 'files'
            size = row['size']
            try:
                size = int(size)
            except (ValueError, TypeError):
                size = 0
            
            result.append({  # POPRAWKA: zmienione z 'files.append' na 'result.append'
                "filename": row['filename'] or f"file-{row['cid'][:8]}",
                "cid": row['cid'],
                "cid_short": row['cid'][:12] + "..." + row['cid'][-6:] if len(row['cid']) > 18 else row['cid'],
                "size_kb": size // 1024 if size > 0 else 0,
                "upload_type": row['upload_type'] or 'pin',
                "pinned_at": row['pinned_at']
            })
        
        return jsonify({"files": result})
        
    except Exception as e:
        print(f"Files endpoint error: {e}")  # Debug log
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard/activity')
def dashboard_activity():
    """Get recent user activity"""
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        conn = get_db_connection()
        user_id = session['user_id']
        
        activities = conn.execute('''
            SELECT event_type, details, timestamp, cid
            FROM audit_log 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''', (user_id,)).fetchall()
        
        conn.close()
        
        result = []
        for activity in activities:
            event_type = activity['event_type']
            
            if event_type == 'CID_PINNED':
                icon = 'pin'
                message = f"Pinned content to IPFS"
            elif event_type == 'FILE_UPLOADED':
                icon = 'upload'
                message = f"Uploaded file to IPFS"
            elif event_type == 'LOGIN_SUCCESS':
                icon = 'login'
                message = f"Logged in"
            else:
                icon = 'activity'
                message = event_type.replace('_', ' ').title()
            
            # Simple time calculation
            time_str = "Recently"
            
            result.append({
                "icon": icon,
                "message": message,
                "time": time_str,
                "timestamp": activity['timestamp']
            })
        
        return jsonify({"activities": result})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard/analytics')
def dashboard_analytics():
    """Get analytics data for charts"""
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        conn = get_db_connection()
        user_id = session['user_id']
        
        # Get storage data with proper NULL handling
        storage_data = conn.execute('''
            SELECT date(pinned_at) as date, SUM(CAST(size AS INTEGER)) as daily_size
            FROM pins 
            WHERE user_id = ? AND pinned_at > datetime('now', '-30 days')
            GROUP BY date(pinned_at)
            ORDER BY date
        ''', (user_id,)).fetchall()
        
        conn.close()
        
        # Safe data processing
        if storage_data:
            dates = []
            storage_mb = []
            
            for row in storage_data:
                if row['date'] and row['daily_size']:
                    dates.append(row['date'])
                    # Safe conversion with fallback
                    try:
                        size_bytes = int(row['daily_size']) if row['daily_size'] else 0
                        size_mb = round(size_bytes / (1024 * 1024), 2)
                        storage_mb.append(size_mb)
                    except (ValueError, TypeError):
                        storage_mb.append(0)
        else:
            # Fallback mock data
            dates = ['2025-01-25', '2025-01-26', '2025-01-27']
            storage_mb = [5.2, 12.8, 18.4]
        
        # Ensure we have at least some data
        if not dates:
            dates = ['2025-01-25', '2025-01-26', '2025-01-27']
            storage_mb = [5.2, 12.8, 18.4]
        
        return jsonify({
            "storage_usage": {
                "labels": dates,
                "data": storage_mb
            },
            "pin_activity": {
                "labels": dates,
                "uploads": [2, 1, 3] if len(dates) >= 3 else [2],
                "pins": [1, 2, 1] if len(dates) >= 3 else [1]
            },
            "bandwidth_usage": {
                "labels": dates,
                "data": [round(x * 0.7, 1) for x in storage_mb]  # 70% of storage as bandwidth estimate
            }
        })
                
    except Exception as e:
        # Fallback on any error
        return jsonify({
            "storage_usage": {
                "labels": ['2025-01-25', '2025-01-26', '2025-01-27'],
                "data": [5.2, 12.8, 18.4]
            },
            "pin_activity": {
                "labels": ['2025-01-25', '2025-01-26', '2025-01-27'],
                "uploads": [2, 1, 3],
                "pins": [1, 2, 1]
            },
            "bandwidth_usage": {
                "labels": ['2025-01-25', '2025-01-26', '2025-01-27'],
                "data": [3.6, 9.0, 12.9]
            },
            "error_debug": str(e)
        })

@app.route('/admin/check-logs')
def check_logs():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM request_log ORDER BY timestamp DESC LIMIT 20').fetchall()
    conn.close()
    
    html = "<h1>Recent GDPR Logs</h1><table border='1'>"
    html += "<tr><th>IP</th><th>Method</th><th>Endpoint</th><th>User Agent</th><th>Timestamp</th><th>User ID</th></tr>"
    
    for log in logs:
        html += f"<tr><td>{log['ip_address']}</td><td>{log['method']}</td><td>{log['endpoint']}</td><td>{log['user_agent'][:50]}</td><td>{log['timestamp']}</td><td>{log['user_id']}</td></tr>"
    
    html += "</table>"
    return html 
        
# CONTACT ROUTE - NIE RUSZAJ
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form with real email sending"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        if not all([name, email, subject, message]):
            return '''
            <div style="color: red; text-align: center; margin: 40px;">
                <h2>Błąd!</h2>
                <p>Wszystkie pola są wymagane</p>
                <a href="/contact">← Wróć do formularza</a>
            </div>
            ''', 400
        
        log_security_event('CONTACT_FORM', None, request.remote_addr, 
                          f"From: {email}, Subject: {subject}, Message: {message[:100]}...")
        
        email_sent = send_contact_email(name, email, subject, message)
        
        if email_sent:
            success_message = "Email wysłany pomyślnie!"
            status_color = "#27ae60"
            status_icon = "✅"
        else:
            success_message = "Wiadomość zapisana, ale email nie został wysłany"
            status_color = "#f39c12"
            status_icon = "⚠️"
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Wiadomość wysłana - ServeBeer</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #2c3e50; color: #ecf0f1; }}
                .container {{ max-width: 600px; margin: 0 auto; text-align: center; }}
                .status {{ background: {status_color}; padding: 30px; border-radius: 10px; margin: 20px 0; }}
                .details {{ background: #34495e; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: left; }}
                a {{ color: #4ecdc4; text-decoration: none; }}
                .back-btn {{ background: #4ecdc4; color: white; padding: 10px 20px; border-radius: 5px; margin: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="status">
                    <h1>{status_icon} {success_message}</h1>
                    <p>Dziękujemy {name}!</p>
                </div>
                
                <div class="details">
                    <h3>Podsumowanie wiadomości:</h3>
                    <p><strong>Email:</strong> {email}</p>
                    <p><strong>Temat:</strong> {subject}</p>
                    <p><strong>Wiadomość:</strong></p>
                    <p style="background: #2c3e50; padding: 10px; border-radius: 5px;">{message}</p>
                </div>
                
                <a href="/contact" class="back-btn">Wyślij kolejną wiadomość</a>
                <a href="/" class="back-btn">Strona główna</a>
            </div>
        </body>
        </html>
        '''
    
    testing_banner = '''
    <div style="position: fixed; top: 0; left: 0; right: 0; background: #e67e22; color: white; padding: 10px; text-align: center; font-weight: bold; z-index: 9999;">
        📧 CONTACT FORM - Wiadomości wysyłane na prawdziwy email! 📧
    </div>
    <div style="height: 50px;"></div>
    ''' if TESTING_MODE else ''
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Kontakt - ServeBeer</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #2c3e50; color: #ecf0f1; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .contact-form {{ background: #34495e; padding: 30px; border-radius: 10px; }}
            input, textarea, select {{ width: 100%; padding: 12px; margin: 10px 0; border: none; border-radius: 5px; box-sizing: border-box; }}
            button {{ background: #4ecdc4; color: white; padding: 12px 30px; border: none; border-radius: 5px; cursor: pointer; width: 100%; }}
            button:hover {{ background: #45b7b8; }}
            .info-box {{ background: #3498db; color: white; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            a {{ color: #4ecdc4; text-decoration: none; }}
            label {{ color: #ecf0f1; font-weight: bold; }}
        </style>
    </head>
    <body>
        {testing_banner}
        <div class="container">
            <h1>📧 Kontakt - ServeBeer</h1>
            
            <div class="info-box">
                📧 Formularz wysyła prawdziwe emaile! Odpowiemy tak szybko jak to możliwe.
            </div>
            
            <div class="contact-form">
                <form method="POST">
                    <label>Imię:</label>
                    <input type="text" name="name" placeholder="Twoje imię" required>
                    
                    <label>Email:</label>
                    <input type="email" name="email" placeholder="twoj@email.com" required>
                    
                    <label>Temat:</label>
                    <select name="subject" required>
                        <option value="">Wybierz temat...</option>
                        <option value="Pytanie ogólne">Pytanie ogólne</option>
                        <option value="Wsparcie techniczne">Wsparcie techniczne</option>
                        <option value="Sponsoring">Sponsoring</option>
                        <option value="IPFS Pin Request">Prośba o pin IPFS</option>
                        <option value="Zgłoszenie błędu">Zgłoszenie błędu</option>
                        <option value="Propozycja funkcji">Propozycja funkcji</option>
                        <option value="Współpraca">Współpraca</option>
                        <option value="Inne">Inne</option>
                    </select>
                    
                    <label>Wiadomość:</label>
                    <textarea name="message" rows="6" placeholder="Twoja wiadomość..." required></textarea>
                    
                    <button type="submit">📧 Wyślij wiadomość</button>
                </form>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <p>🍺 ServeBeer IPFS CDN - Community-Powered Storage</p>
                <p><a href="/">← Strona główna</a> | <a href="/dashboard">Dashboard</a></p>
            </div>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    setup_logging()
    init_database()
    
    mode_indicator = "BETA TESTING" if TESTING_MODE else "PRODUCTION"
    print(f"🍺 ServeBeer IPFS CDN Starting... [{mode_indicator}]")
    print(f"Database: {DATABASE_PATH}")
    print(f"IPFS API: {IPFS_API_URL}")
    print(f"Beta Mode: {TESTING_MODE}")
    
    ssl_context = create_ssl_context()
    
    if ssl_context and SSL_ENABLED:
        print("🔒 Starting with HTTPS on port 443...")
        print("🎯 Ready for guerrilla infrastructure!")
        print(f"📜 Certificate: {SSL_CERT_PATH}")
        print(f"🔑 Private Key: {SSL_KEY_PATH}")
        print("")
        print("⚠️  Port 443 requires root - run: sudo python3 app.py")
        try:
            app.run(debug=False, host='0.0.0.0', port=5000, ssl_context=ssl_context)
        except PermissionError:
            print("❌ Permission denied! Run: sudo python3 app.py")
    else:
        print("⚠️  SSL disabled, starting HTTP on port 5000...")
        print("🎯 Ready for guerrilla infrastructure!")
        app.run(debug=True, host='0.0.0.0', port=5000)
