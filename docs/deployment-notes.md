# 🚀 ServeBeer Deployment Notes

**Current Production Setup Documentation**

---

## Current Configuration

### Server Setup

**Hardware:**
- Raspberry Pi 400
- Location: Warsaw, Poland
- Connection: Fiber optic

**Software Stack:**
- OS: Debian 12 Bookworm
- Python: 3.11
- IPFS: Kubo (go-ipfs)
- Web Server: Flask (direct, no nginx)

### Network Configuration

**Port Forwarding:**
```
Router Configuration:
External Port 443 (HTTPS) → Internal Port 5000
```

**Application Configuration:**
```python
# app.py runs on port 5000
SSL_ENABLED=true
PORT=5000

# SSL context configured in app.py
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(SSL_CERT_PATH, SSL_KEY_PATH)

# Application listens on all interfaces
app.run(host='0.0.0.0', port=5000, ssl_context=context)
```

**Access Flow:**
```
Internet User
    │
    ▼
https://domain.com:443
    │
    ▼
Router (Port Forward)
    │ 443 → 5000
    ▼
Raspberry Pi :5000 (HTTPS)
    │
    ▼
Flask Application (SSL enabled)
```

---

## SSL/TLS Configuration

### Certificate Setup

**Current Implementation:**
- SSL certificates loaded directly in Flask
- No nginx reverse proxy
- Direct HTTPS on port 5000

**Certificate Locations:**
```bash
SSL_CERT_PATH=/path/to/fullchain.pem
SSL_KEY_PATH=/path/to/privkey.pem
```

**Advantages:**
- Simple setup (no nginx configuration)
- One less component to manage
- Direct SSL termination in Flask

**Disadvantages:**
- Flask SSL performance lower than nginx
- Requires root privileges for port binding
- No easy HTTP→HTTPS redirect

### Running with SSL on Port 5000

**Root Required (for privileged port):**
```bash
# If binding to port < 1024 would need root
# But port 5000 doesn't require root

# However, if SSL is enabled and reading certs:
sudo python3 app.py

# Or use capabilities:
sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python3.11
python3 app.py
```

**Systemd Service (Recommended):**
```ini
[Unit]
Description=ServeBeer IPFS CDN
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/servebeer-ipfs
Environment="PATH=/home/pi/servebeer-ipfs/venv/bin"
ExecStart=/home/pi/servebeer-ipfs/venv/bin/python app.py
Restart=on-failure

# If SSL certs require root:
# User=root
# Or use AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
```

---

## Router Configuration

### Port Forwarding Setup

**Router Settings:**
1. Access router admin panel
2. Navigate to Port Forwarding / NAT
3. Create rule:
   - External Port: 443
   - Internal IP: [Raspberry Pi IP]
   - Internal Port: 5000
   - Protocol: TCP

**Verify Port Forward:**
```bash
# From external network
curl -I https://your-domain.com

# Should connect to your Pi on port 5000
```

### Firewall Rules (Pi)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTPS internally (router forwards to this)
sudo ufw allow 5000/tcp

# Allow IPFS P2P
sudo ufw allow 4001/tcp

# Block IPFS API from external access
sudo ufw deny 5001/tcp

# Enable firewall
sudo ufw enable
```

---

## Alternative Deployment Options

### Option 1: Current Setup (Flask Direct SSL)

**Pros:**
- Simple configuration
- No additional software needed
- Direct SSL termination

**Cons:**
- Flask SSL performance
- Requires careful certificate permissions
- No HTTP→HTTPS redirect

### Option 2: Nginx Reverse Proxy

**Configuration:**
```nginx
# /etc/nginx/sites-available/servebeer

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

**Update app.py:**
```python
# Disable SSL in app.py
SSL_ENABLED=false

# Run on HTTP (nginx handles HTTPS)
app.run(host='127.0.0.1', port=5000)
```

**Router config stays the same:**
```
443 → 443 (nginx handles)
```

**Advantages:**
- Better SSL performance
- Easy HTTP→HTTPS redirect
- Rate limiting, caching, compression
- Load balancing (future)

**Disadvantages:**
- Additional software to manage
- More complex configuration

### Option 3: Caddy (Automatic HTTPS)

**Caddy configuration:**
```caddy
your-domain.com {
    reverse_proxy localhost:5000
    encode gzip
}
```

**Advantages:**
- Automatic Let's Encrypt certificates
- Automatic renewal
- Simple configuration
- Modern HTTP/2, HTTP/3 support

---

## SSL Certificate Management

### Let's Encrypt (Recommended)

**Installation:**
```bash
sudo apt install certbot
```

**Manual Certificate:**
```bash
sudo certbot certonly --standalone -d your-domain.com
```

**With Nginx:**
```bash
sudo certbot --nginx -d your-domain.com
```

**Auto-renewal:**
```bash
# Test renewal
sudo certbot renew --dry-run

# Automatic renewal (cron)
sudo crontab -e
# Add:
0 3 * * * certbot renew --quiet
```

**Certificate Locations (Let's Encrypt):**
```
/etc/letsencrypt/live/your-domain.com/fullchain.pem
/etc/letsencrypt/live/your-domain.com/privkey.pem
```

### Self-Signed Certificates (Development Only)

```bash
# Generate self-signed cert
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem -out cert.pem \
  -days 365 -nodes \
  -subj "/CN=localhost"

# Use in .env
SSL_CERT_PATH=cert.pem
SSL_KEY_PATH=key.pem
```

---

## Performance Optimization

### Flask SSL Performance

**Current Limitations:**
- Flask SSL slower than nginx
- Single-threaded by default
- Limited connection handling

**Improvements:**

**1. Use Gunicorn (Production WSGI Server):**
```bash
# Install
pip install gunicorn

# Run with multiple workers
gunicorn --workers 4 --bind 0.0.0.0:5000 \
  --certfile=/path/to/cert.pem \
  --keyfile=/path/to/key.pem \
  app:app
```

**2. Use Waitress (Windows-compatible):**
```bash
pip install waitress

# Run (no SSL, use nginx for SSL)
waitress-serve --listen=127.0.0.1:5000 app:app
```

**3. Enable HTTP/2:**
- Requires nginx or Caddy
- Not available in Flask directly
- Improves performance significantly

---

## Monitoring & Maintenance

### Check Service Status

```bash
# If running as systemd service
sudo systemctl status servebeer

# View logs
journalctl -u servebeer -f

# Application logs
tail -f logs/servebeer_audit.log
```

### Health Checks

```bash
# Internal health check
curl http://localhost:5000/health

# External health check
curl https://your-domain.com/health
```

### Certificate Expiry Check

```bash
# Check certificate expiry
echo | openssl s_client -connect your-domain.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

### Automated Monitoring

**Setup monitoring script:**
```bash
#!/bin/bash
# monitor.sh

# Check if app is running
if ! pgrep -f "python.*app.py" > /dev/null; then
    echo "ServeBeer not running! Restarting..."
    sudo systemctl restart servebeer
fi

# Check SSL expiry (30 days warning)
EXPIRY=$(echo | openssl s_client -connect localhost:5000 2>/dev/null | \
         openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

if [ $DAYS_LEFT -lt 30 ]; then
    echo "SSL certificate expires in $DAYS_LEFT days!"
    # Send alert (email, Discord webhook, etc.)
fi
```

**Add to crontab:**
```bash
crontab -e
# Add:
*/5 * * * * /path/to/monitor.sh
```

---

## Troubleshooting

### SSL Certificate Issues

**Problem:** Permission denied reading certificate
```bash
# Check certificate permissions
ls -l /path/to/*.pem

# Fix permissions
sudo chmod 644 /path/to/fullchain.pem
sudo chmod 600 /path/to/privkey.pem

# Or run as root (systemd with User=root)
```

**Problem:** Certificate expired
```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Restart application
sudo systemctl restart servebeer
```

### Port Forwarding Issues

**Problem:** Cannot access from external network
```bash
# Test from inside network
curl https://local-ip:5000

# Check router port forward
# Verify external IP
curl ifconfig.me

# Test external access
curl https://external-ip:443
```

**Problem:** Router doesn't support port forwarding to non-standard ports
```bash
# Some routers only allow 443→443
# Solution: Run app on port 443 (requires root)
PORT=443
sudo python3 app.py
```

---

## Security Considerations

### Running as Root

**Avoid if possible:**
```bash
# Don't run as root if you can help it
❌ sudo python3 app.py
```

**Better alternatives:**

**1. Use systemd with capabilities:**
```ini
[Service]
User=pi
AmbientCapabilities=CAP_NET_BIND_SERVICE
```

**2. Use setcap:**
```bash
sudo setcap 'cap_net_bind_service=+ep' $(which python3)
```

**3. Use port >1024:**
```bash
# Run on 5000, forward 443→5000 at router
# Current setup - GOOD!
```

### Protecting IPFS API

```bash
# IPFS API should NOT be accessible externally
sudo ufw deny 5001/tcp

# Bind IPFS API to localhost only
ipfs config Addresses.API "/ip4/127.0.0.1/tcp/5001"
```

---

## Upgrade Path

### Future Improvements

**Short Term:**
1. Add nginx reverse proxy
2. Implement automatic certificate renewal
3. Add HTTP→HTTPS redirect
4. Enable HTTP/2

**Medium Term:**
1. Move to Gunicorn/Waitress
2. Add load balancing (multiple Pi nodes)
3. Implement CDN (Cloudflare)
4. Add monitoring (Prometheus + Grafana)

**Long Term:**
1. Migrate to dedicated server
2. Kubernetes deployment
3. Geographic distribution
4. Professional CDN integration

---

## Quick Reference

**Current Setup:**
```
External: https://domain.com:443
Router: 443 → 5000
Internal: https://localhost:5000
SSL: Enabled in Flask
```

**Key Files:**
- `app.py` - SSL configuration
- `.env` - SSL paths, port config
- Router admin - Port forwarding

**Key Commands:**
```bash
# Start application
python3 app.py

# Check if running
pgrep -f "python.*app.py"

# View logs
tail -f logs/servebeer_audit.log

# Test health
curl https://localhost:5000/health
```

---

*ServeBeer Deployment Notes*  
*Current Configuration: Flask Direct SSL + Router Port Forward*  
*Updated: January 2025*