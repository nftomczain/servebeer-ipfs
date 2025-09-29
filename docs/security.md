# 🔒 Security Policy

**ServeBeer IPFS CDN Security Documentation**

---

## Table of Contents

1. [Reporting Security Vulnerabilities](#reporting-security-vulnerabilities)
2. [Supported Versions](#supported-versions)
3. [Security Features](#security-features)
4. [Known Security Considerations](#known-security-considerations)
5. [Best Practices](#best-practices)
6. [GDPR Compliance](#gdpr-compliance)
7. [Audit Logging](#audit-logging)
8. [Data Retention](#data-retention)
9. [Third-Party Dependencies](#third-party-dependencies)
10. [Security Roadmap](#security-roadmap)

---

## Reporting Security Vulnerabilities

We take security seriously. If you discover a security vulnerability, please follow responsible disclosure:

### 🚨 DO NOT Create Public GitHub Issues

**Instead, report privately via:**

📧 **Email:** tmpnft@gmail.com  
**Subject:** [SECURITY] Brief description

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)
- Your contact information

### Response Timeline

- **Initial Response:** Within 48 hours
- **Status Update:** Within 7 days
- **Fix Timeline:** Depends on severity
  - Critical: 1-7 days
  - High: 7-14 days
  - Medium: 14-30 days
  - Low: Next release cycle

### Recognition

Security researchers who responsibly disclose vulnerabilities will be:
- Credited in CHANGELOG (if desired)
- Listed in SECURITY.md acknowledgments
- Thanked publicly (with permission)

---

## Supported Versions

Currently supported versions receiving security updates:

| Version | Supported          | Notes                    |
| ------- | ------------------ | ------------------------ |
| 1.0.x   | :white_check_mark: | Current stable release   |
| Beta    | :white_check_mark: | Active development       |
| < 1.0   | :x:                | Upgrade to 1.0+          |

---

## Security Features

### Authentication

**Current Implementation:**
- Session-based authentication with secure cookies
- SHA-256 password hashing
- 30-day session lifetime
- Automatic session cleanup

**Session Security:**
```python
SESSION_COOKIE_SECURE = False      # Set True for HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 30 days
```

**Password Storage:**
- Passwords hashed with SHA-256
- No plaintext password storage
- No password recovery (only reset)

### Input Validation

**CID Validation:**
- Format checking (base58/CIDv1)
- Existence verification in IPFS network
- Size validation

**File Upload Validation:**
- File size limits enforced
- MIME type checking
- Filename sanitization

**SQL Injection Protection:**
- Parameterized queries only
- No string concatenation in SQL
- SQLite Row factory for safe data access

### XSS Protection

- Flask template auto-escaping enabled
- No `|safe` filters without validation
- Content-Security-Policy headers (to be added)

### CSRF Protection

**Current Status:** Not implemented  
**Planned:** Flask-WTF CSRF tokens

### Rate Limiting

**Current Status:** Not implemented  
**Planned:** Per-IP and per-user rate limiting

---

## Known Security Considerations

### 1. Password Hashing

**Current:** SHA-256 (fast, not ideal for passwords)

**Consideration:**
- SHA-256 is vulnerable to brute-force attacks
- No salting implemented
- No key stretching

**Recommendation for Production:**
```python
# Upgrade to bcrypt
import bcrypt

def hash_password(password):
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt)

def verify_password(password, hash):
    return bcrypt.checkpw(password.encode(), hash)
```

**Migration Path:**
- Add `password_hash_type` column to users table
- Gradually migrate users on next login
- Keep SHA-256 support for transition

### 2. No Rate Limiting

**Risk:** Brute-force attacks, API abuse

**Mitigation (Manual):**
- Monitor audit logs for suspicious activity
- Block IPs at firewall level
- Use reverse proxy (nginx) rate limiting

**Planned Implementation:**
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@limiter.limit("5 per minute")
@app.route('/login', methods=['POST'])
def login():
    ...
```

### 3. No CSRF Protection

**Risk:** Cross-site request forgery attacks

**Current Mitigation:**
- SameSite=Lax cookie attribute
- Session-based auth (not vulnerable to token theft)

**Recommended Addition:**
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
```

### 4. Email in Contact Form

**Current:** Uses Gmail SMTP with hardcoded credentials

**Security Concerns:**
- App-specific password in code
- No encryption for credentials

**Recommendation:**
```python
# Move to environment variables
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Consider using SendGrid/Mailgun API instead
```

### 5. API Key Authentication

**Status:** Generated but not actively used

**If Implemented:**
- Use Bearer token authentication
- Implement key rotation
- Add key expiration
- Rate limit by API key

---

## Best Practices

### For Administrators

**1. Environment Configuration:**
```bash
# Generate strong secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Never commit .env file
echo ".env" >> .gitignore

# Use different keys for dev/production
```

**2. Database Security:**
```bash
# Restrict database file permissions
chmod 600 database/servebeer.db

# Regular backups
cp database/servebeer.db database/backup-$(date +%Y%m%d).db

# Encrypt backups for off-site storage
gpg -c database/backup-*.db
```

**3. IPFS Security:**
```bash
# Restrict IPFS API access
ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin '["http://localhost:5000"]'

# Enable IPFS API authentication (if exposed)
ipfs config --json API.Authorizations '{"/": {"AuthSecret": "your-secret"}}'
```

**4. SSL/TLS:**
```bash
# Always use HTTPS in production
SSL_ENABLED=true
SSL_CERT_PATH=/etc/letsencrypt/live/domain/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/domain/privkey.pem

# Disable HTTP entirely
# Or redirect HTTP to HTTPS in nginx
```

**5. Firewall Configuration:**
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 4001/tcp    # IPFS P2P
sudo ufw enable

# Block IPFS API from external access
sudo ufw deny 5001/tcp
```

### For Developers

**1. Secure Coding:**
- Always use parameterized queries
- Validate all user input
- Escape output in templates
- Use prepared statements
- Never trust user data

**2. Secrets Management:**
```python
# Never hardcode secrets
❌ api_key = "sk_live_abc123"

# Always use environment variables
✅ api_key = os.getenv('API_KEY')

# Use .env for local development
# Use secrets manager for production
```

**3. Error Handling:**
```python
# Don't expose internal details
❌ return f"Database error: {str(e)}", 500

# Return generic messages
✅ return "Internal server error", 500
   # Log detailed error internally
   logging.error(f"Database error: {str(e)}")
```

**4. Logging:**
```python
# Log security events
log_security_event('LOGIN_FAILED', None, request.remote_addr, email)

# Never log passwords or tokens
❌ logging.info(f"User {email} logged in with password {password}")

# Log anonymized data
✅ logging.info(f"User {email} logged in from {request.remote_addr}")
```

---

## GDPR Compliance

ServeBeer implements GDPR-compliant practices:

### Data Collection

**What we collect:**
- Email addresses (for authentication)
- Hashed passwords
- IP addresses (for audit logging)
- User agent strings
- Pinned CID references
- Storage usage statistics

**What we DON'T collect:**
- Real names (unless in contact form)
- Physical addresses
- Payment information (currently)
- Browsing history outside application
- Cookie tracking (no analytics cookies)

### Legal Basis

- **Legitimate Interest:** Service operation, security
- **Consent:** User registration, terms acceptance
- **Contract:** Service provision

### User Rights

**Right to Access:**
```sql
-- Users can request their data
SELECT * FROM users WHERE id = ?;
SELECT * FROM pins WHERE user_id = ?;
SELECT * FROM audit_log WHERE user_id = ?;
```

**Right to Erasure:**
```sql
-- Delete user and all associated data
DELETE FROM pins WHERE user_id = ?;
DELETE FROM audit_log WHERE user_id = ?;
DELETE FROM request_log WHERE user_id = ?;
DELETE FROM users WHERE id = ?;
```

**Right to Data Portability:**
```python
# Export user data as JSON
@app.route('/api/export-data')
def export_user_data():
    # Returns complete user data in JSON format
    return jsonify({
        'user': user_data,
        'pins': pins_data,
        'audit_log': audit_data
    })
```

### Request Logging

All HTTP requests are logged:
```python
@app.before_request
def gdpr_logging():
    conn.execute('''
        INSERT INTO request_log 
        (ip_address, method, endpoint, user_agent, user_id)
        VALUES (?, ?, ?, ?, ?)
    ''')
```

**Retention:** Logs retained indefinitely (consider implementing rotation)

**Access:** Only administrators can access logs

**Purpose:** Security, debugging, legal compliance

---

## Audit Logging

### Logged Events

All security-relevant events are logged:

| Event Type | When | Data Logged |
|------------|------|-------------|
| `LOGIN_SUCCESS` | Successful login | User ID, IP, timestamp |
| `LOGIN_FAILED` | Failed login attempt | Email, IP, timestamp |
| `REGISTER_SUCCESS` | New account created | User ID, IP, timestamp |
| `REGISTER_FAILED` | Registration failed | Email, IP, reason |
| `CID_PINNED` | Content pinned | User ID, CID, size, IP |
| `FILE_UPLOADED` | File uploaded | User ID, CID, size, IP |
| `UPLOAD_FAILED` | Upload failed | User ID, error, IP |
| `CONTACT_FORM` | Contact form submitted | Email, subject, IP |

### Log Format

```
2025-01-27 15:30:00 | INFO | SECURITY: {'event': 'LOGIN_SUCCESS', 'user_id': 42, 'ip': '192.168.1.100'}
```

### Log Location

- **File:** `logs/servebeer_audit.log`
- **Database:** `audit_log` table
- **Permissions:** Read-only for application user

### Log Rotation

**Recommended setup:**
```bash
# /etc/logrotate.d/servebeer
/path/to/servebeer-ipfs/logs/*.log {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## Data Retention

### Active Users

- **Account Data:** Retained while account active
- **Pins:** Retained while account active
- **Audit Logs:** Indefinite retention (recommend 2-year policy)
- **Request Logs:** Indefinite retention (recommend 90-day policy)

### Inactive Users

**Definition:** No login for 365 days

**Policy:**
1. Email notification at 330 days
2. Final warning at 355 days
3. Account deletion at 365 days (if no response)

**Implementation:**
```python
# Periodic cleanup job
DELETE FROM users WHERE last_active < datetime('now', '-365 days');
```

### Deleted Accounts

**User-Initiated Deletion:**
- Immediate account deactivation
- 30-day grace period for recovery
- Permanent deletion after 30 days
- IPFS pins remain (content-addressed, no personal link)

**Data Removed:**
- User account record
- Personal information
- Pin associations
- API keys

**Data Retained:**
- Anonymized audit logs (IP + timestamp only)
- Aggregate statistics
- No personally identifiable information

---

## Third-Party Dependencies

### Direct Dependencies

Security status of key dependencies:

| Package | Version | Security | Notes |
|---------|---------|----------|-------|
| Flask | 2.3.3 | ✅ Good | Actively maintained |
| requests | 2.31.0 | ✅ Good | Widely used, secure |
| python-dotenv | 1.0.0 | ✅ Good | Simple, secure |
| gunicorn | 21.2.0 | ✅ Good | Production WSGI server |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | 7.4.2 | Testing |
| black | 23.9.1 | Code formatting |
| flake8 | 6.1.0 | Linting |

### Dependency Management

**Check for vulnerabilities:**
```bash
# Using pip-audit
pip install pip-audit
pip-audit

# Using safety
pip install safety
safety check
```

**Update dependencies:**
```bash
# Check outdated packages
pip list --outdated

# Update specific package
pip install --upgrade flask

# Update all (carefully!)
pip install --upgrade -r requirements.txt
```

### IPFS Dependency

**External Service:** IPFS Kubo daemon

**Security Considerations:**
- Runs as separate process
- HTTP API communication (local only)
- No authentication required (local trust)
- Firewall should block external access to port 5001

**Recommendation:**
```bash
# Bind IPFS API to localhost only
ipfs config Addresses.API "/ip4/127.0.0.1/tcp/5001"

# Or use Unix socket
ipfs config Addresses.API "/unix/var/run/ipfs.sock"
```

---

## Security Roadmap

### Short Term (1-3 months)

**Priority 1: Critical**
- [ ] Implement bcrypt password hashing
- [ ] Add CSRF protection
- [ ] Add rate limiting
- [ ] Move email credentials to environment variables
- [ ] Implement password complexity requirements

**Priority 2: High**
- [ ] Add Content-Security-Policy headers
- [ ] Implement API key authentication properly
- [ ] Add 2FA support (TOTP)
- [ ] Implement account lockout after failed attempts
- [ ] Add security headers (X-Frame-Options, etc.)

### Medium Term (3-6 months)

**Priority 3: Medium**
- [ ] Add password reset functionality
- [ ] Implement email verification
- [ ] Add session management page (view/revoke sessions)
- [ ] Implement API key rotation
- [ ] Add security audit dashboard
- [ ] Implement automated security scanning
- [ ] Add WAF (Web Application Firewall) rules

**Priority 4: Nice to Have**
- [ ] Add SSO support (OAuth2)
- [ ] Implement hardware key support (WebAuthn)
- [ ] Add anomaly detection
- [ ] Implement IP whitelist/blacklist
- [ ] Add DDoS protection

### Long Term (6-12 months)

**Infrastructure Security:**
- [ ] Security penetration testing
- [ ] Third-party security audit
- [ ] Bug bounty program
- [ ] SOC 2 compliance (if applicable)
- [ ] Regular security training for contributors

---

## Security Checklist

### Before Production Deployment

**Configuration:**
- [ ] `TESTING_MODE=False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] SSL/TLS enabled and configured
- [ ] Environment variables secured
- [ ] Debug mode disabled

**Authentication:**
- [ ] Default accounts removed/secured
- [ ] Password policy enforced
- [ ] Session timeout configured
- [ ] API keys rotated

**Network:**
- [ ] Firewall rules configured
- [ ] Only necessary ports exposed
- [ ] IPFS API not publicly accessible
- [ ] Rate limiting enabled
- [ ] Reverse proxy configured

**Database:**
- [ ] Backups automated
- [ ] File permissions restricted
- [ ] Encryption at rest (if applicable)
- [ ] Access logging enabled

**Monitoring:**
- [ ] Audit logging functional
- [ ] Error monitoring configured
- [ ] Security alerts setup
- [ ] Log rotation configured

**Legal:**
- [ ] Terms of Service published
- [ ] Privacy Policy published
- [ ] Cookie Policy published
- [ ] GDPR compliance verified
- [ ] DMCA policy established

---

## Incident Response

### If Security Breach Occurs

**Immediate Actions (0-1 hour):**
1. Isolate affected systems
2. Preserve evidence (logs, database)
3. Assess scope of breach
4. Contain the breach

**Short Term (1-24 hours):**
1. Notify affected users
2. Reset credentials if compromised
3. Apply patches/fixes
4. Document incident timeline
5. Contact authorities if required

**Medium Term (1-7 days):**
1. Conduct thorough investigation
2. Implement additional security measures
3. Publish incident report (if appropriate)
4. Update security policies
5. Train team on lessons learned

**Long Term (7+ days):**
1. Monitor for recurrence
2. Implement preventive measures
3. Third-party security audit
4. Update disaster recovery plan

### Contact Information

**Security Team:**
- Email: tmpnft@gmail.com
- Response time: 48 hours

**Emergency Contact:**
- For critical vulnerabilities: Same email with [URGENT] prefix

---

## Security Best Practices for Users

### For End Users

**Strong Passwords:**
- Use unique passwords (not reused)
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- Use password manager

**Account Security:**
- Don't share credentials
- Log out on shared devices
- Be cautious of phishing
- Verify URLs before entering credentials

**Content Safety:**
- Don't pin illegal content
- Respect copyright
- Report suspicious content
- Keep content backups

### For Self-Hosters

**System Security:**
```bash
# Keep system updated
sudo apt update && sudo apt upgrade

# Use SSH keys (disable password auth)
ssh-keygen -t ed25519
echo "PasswordAuthentication no" >> /etc/ssh/sshd_config

# Enable automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

**Application Security:**
```bash
# Run as non-root user
sudo useradd -m -s /bin/bash servebeer
sudo chown -R servebeer:servebeer /opt/servebeer

# Use systemd with restricted permissions
[Service]
User=servebeer
NoNewPrivileges=true
PrivateTmp=true
```

**Monitoring:**
```bash
# Install fail2ban
sudo apt install fail2ban

# Monitor logs
tail -f logs/servebeer_audit.log

# Setup alerting
# Email on failed login attempts
```

---

## Security Resources

### Tools

**Vulnerability Scanning:**
- [OWASP ZAP](https://www.zaproxy.org/) - Web app scanner
- [Bandit](https://bandit.readthedocs.io/) - Python security linter
- [Safety](https://github.com/pyupio/safety) - Dependency checker

**Password Security:**
- [Have I Been Pwned](https://haveibeenpwned.com/) - Check compromised passwords
- [password_strength](https://pypi.org/project/password-strength/) - Python library

**Monitoring:**
- [Sentry](https://sentry.io/) - Error tracking
- [Fail2Ban](https://www.fail2ban.org/) - Intrusion prevention
- [OSSEC](https://www.ossec.net/) - Host intrusion detection

### Educational Resources

**OWASP Top 10:**
- [OWASP Top 10 Web Application Security Risks](https://owasp.org/www-project-top-ten/)

**Flask Security:**
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)
- [Flask-Security](https://flask-security-too.readthedocs.io/)

**GDPR:**
- [GDPR Official Text](https://gdpr-info.eu/)
- [GDPR Compliance Checklist](https://gdpr.eu/checklist/)

---

## Security Acknowledgments

We thank the following security researchers for their contributions:

*(None yet - be the first!)*

---

## Updates to This Policy

This security policy will be updated as:
- New vulnerabilities are discovered
- Security features are added
- Best practices evolve
- Community feedback is received

**Last Updated:** January 27, 2025  
**Version:** 1.0.0

---

## Conclusion

Security is an ongoing process, not a destination. ServeBeer implements reasonable security measures for a community-driven IPFS pinning service, with known limitations documented transparently.

**Current Security Posture:**
- ✅ Basic authentication and authorization
- ✅ Audit logging and GDPR compliance
- ✅ Input validation and SQL injection protection
- ⚠️ Password hashing needs improvement
- ⚠️ Rate limiting not implemented
- ⚠️ CSRF protection not implemented

We prioritize transparency about security status and actively work to improve our security posture.

**For Questions:**
Contact: tmpnft@gmail.com

**For Security Reports:**
Follow responsible disclosure process outlined above.

---

*ServeBeer IPFS CDN - Security Policy v1.0*  
*"Guerrilla Infrastructure with Responsible Security"*  
*© 2025 NFTomczain Universe*