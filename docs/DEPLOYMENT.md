# Production Deployment Guide

This guide covers deploying the Bike Lifecycle Management System to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Requirements](#server-requirements)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Database Setup](#database-setup)
5. [Backend Deployment](#backend-deployment)
6. [Frontend Deployment](#frontend-deployment)
7. [Nginx Configuration](#nginx-configuration)
8. [SSL Certificate Setup](#ssl-certificate-setup)
9. [Systemd Services](#systemd-services)
10. [Monitoring & Logging](#monitoring--logging)
11. [Backup Strategy](#backup-strategy)
12. [Rollback Procedures](#rollback-procedures)
13. [Post-Deployment Verification](#post-deployment-verification)

---

## Prerequisites

### Required Software

- **Operating System**: Ubuntu 22.04 LTS or later
- **Database**: PostgreSQL 14+
- **Python**: Python 3.11+
- **Node.js**: Node.js 20+ with npm
- **Web Server**: Nginx 1.18+
- **Process Manager**: systemd
- **SSL**: Let's Encrypt (certbot)

### Access Requirements

- Root or sudo access to production server
- Database admin credentials
- Domain name with DNS configured
- SSH key-based authentication configured

---

## Server Requirements

### Minimum Specifications

- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 50GB SSD
- **Network**: 100 Mbps

### Recommended Specifications

- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 100GB SSD
- **Network**: 1 Gbps

### Firewall Rules

```bash
# Allow SSH (port 22)
sudo ufw allow 22/tcp

# Allow HTTP (port 80)
sudo ufw allow 80/tcp

# Allow HTTPS (port 443)
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

---

## Pre-Deployment Checklist

### Code Preparation

- [ ] All code committed to main branch
- [ ] All tests passing (`pytest tests/`)
- [ ] No uncommitted changes
- [ ] Version tagged in git (`git tag v1.0.0`)
- [ ] Dependencies updated in requirements.txt and package.json

### Configuration

- [ ] Environment variables configured
- [ ] Database credentials secured
- [ ] API keys and secrets generated
- [ ] CORS origins configured for production domain
- [ ] Frontend API URL configured

### Database

- [ ] Backup of existing data (if any)
- [ ] Migration scripts tested
- [ ] Indexes created
- [ ] Materialized views created

### Security

- [ ] SSL certificate obtained
- [ ] Secrets stored securely (not in code)
- [ ] Database password is strong
- [ ] JWT secret key generated
- [ ] File permissions reviewed

---

## Database Setup

### 1. Install PostgreSQL

```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Start and enable service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

-- In PostgreSQL prompt:
CREATE DATABASE loan_manager;
CREATE USER loan_manager_user WITH PASSWORD 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE loan_manager TO loan_manager_user;

-- Enable required extensions
\c loan_manager
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Exit
\q
```

### 3. Configure PostgreSQL

Edit `/etc/postgresql/14/main/postgresql.conf`:

```ini
# Performance tuning for production
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB

# Connection limits
max_connections = 100
```

Edit `/etc/postgresql/14/main/pg_hba.conf`:

```
# Allow local connections
local   all             all                                     peer
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### 4. Run Migrations

```bash
# Clone repository
cd /var/www
sudo git clone https://github.com/yourusername/loan-manager.git
cd loan-manager

# Set permissions
sudo chown -R www-data:www-data /var/www/loan-manager

# Run migrations
cd /var/www/loan-manager/database/migrations
for f in *.sql; do
  sudo -u postgres psql loan_manager < "$f"
  echo "Applied migration: $f"
done
```

### 5. Create Materialized Views

```bash
cd /var/www/loan-manager/database/materialized_views
sudo -u postgres psql loan_manager < 001_bike_lifecycle_views.sql
```

### 6. Verify Database

```bash
sudo -u postgres psql loan_manager -c "\dt"  # List tables
sudo -u postgres psql loan_manager -c "\dm"  # List materialized views
sudo -u postgres psql loan_manager -c "\di"  # List indexes
```

---

## Backend Deployment

### 1. Install Python and Dependencies

```bash
# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Create virtual environment
cd /var/www/loan-manager/backend
sudo -u www-data python3.11 -m venv venv

# Activate and install dependencies
sudo -u www-data bash -c "source venv/bin/activate && pip install --upgrade pip"
sudo -u www-data bash -c "source venv/bin/activate && pip install -r requirements.txt"
```

### 2. Configure Environment Variables

Create `/var/www/loan-manager/backend/.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://loan_manager_user:STRONG_PASSWORD_HERE@localhost:5432/loan_manager

# Security
SECRET_KEY=GENERATE_RANDOM_SECRET_KEY_HERE
JWT_SECRET_KEY=GENERATE_RANDOM_JWT_KEY_HERE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["https://yourdomain.com"]

# Environment
ENVIRONMENT=production
DEBUG=false

# Server
HOST=127.0.0.1
PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/loan-manager/backend.log
```

**Generate secrets**:

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set permissions:

```bash
sudo chmod 600 /var/www/loan-manager/backend/.env
sudo chown www-data:www-data /var/www/loan-manager/backend/.env
```

### 3. Create Systemd Service

Create `/etc/systemd/system/loan-manager-backend.service`:

```ini
[Unit]
Description=Loan Manager Backend API
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/loan-manager/backend
Environment="PATH=/var/www/loan-manager/backend/venv/bin"
ExecStart=/var/www/loan-manager/backend/venv/bin/uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 4 \
    --log-config logging.conf

# Restart policy
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/loan-manager

# Limits
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

Create logging config `/var/www/loan-manager/backend/logging.conf`:

```ini
[loggers]
keys=root,uvicorn,app

[handlers]
keys=console,file

[formatters]
keys=default

[logger_root]
level=INFO
handlers=console,file

[logger_uvicorn]
level=INFO
handlers=console,file
qualname=uvicorn
propagate=0

[logger_app]
level=INFO
handlers=console,file
qualname=app
propagate=0

[handler_console]
class=StreamHandler
formatter=default
args=(sys.stdout,)

[handler_file]
class=handlers.RotatingFileHandler
formatter=default
args=('/var/log/loan-manager/backend.log', 'a', 10485760, 5)

[formatter_default]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
datefmt=%Y-%m-%d %H:%M:%S
```

Enable and start service:

```bash
# Create log directory
sudo mkdir -p /var/log/loan-manager
sudo chown www-data:www-data /var/log/loan-manager

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable loan-manager-backend
sudo systemctl start loan-manager-backend

# Check status
sudo systemctl status loan-manager-backend

# View logs
sudo journalctl -u loan-manager-backend -f
```

### 4. Install Materialized View Refresh Timer

Copy systemd files:

```bash
sudo cp /var/www/loan-manager/deployment/systemd/bike-lifecycle-refresh.service /etc/systemd/system/
sudo cp /var/www/loan-manager/deployment/systemd/bike-lifecycle-refresh.timer /etc/systemd/system/

# Edit service to use correct paths
sudo sed -i 's|/path/to/loan-manager|/var/www/loan-manager|g' /etc/systemd/system/bike-lifecycle-refresh.service

# Enable timer
sudo systemctl daemon-reload
sudo systemctl enable bike-lifecycle-refresh.timer
sudo systemctl start bike-lifecycle-refresh.timer

# Check timer status
sudo systemctl list-timers --all
```

---

## Frontend Deployment

### 1. Install Node.js

```bash
# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# Verify
node --version  # Should be v20.x
npm --version   # Should be v10.x
```

### 2. Configure Environment Variables

Create `/var/www/loan-manager/frontend/.env.production`:

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/v1
NEXT_PUBLIC_APP_NAME=Bike Lifecycle Management
NEXT_PUBLIC_APP_VERSION=1.0.0
```

### 3. Build Frontend

```bash
cd /var/www/loan-manager/frontend

# Install dependencies
sudo -u www-data npm ci --production

# Build for production
sudo -u www-data npm run build

# Verify build
ls -la .next/
```

### 4. Create Systemd Service

Create `/etc/systemd/system/loan-manager-frontend.service`:

```ini
[Unit]
Description=Loan Manager Frontend (Next.js)
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/loan-manager/frontend
Environment="NODE_ENV=production"
Environment="PORT=3000"
ExecStart=/usr/bin/npm start

# Restart policy
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable loan-manager-frontend
sudo systemctl start loan-manager-frontend
sudo systemctl status loan-manager-frontend
```

---

## Nginx Configuration

### 1. Install Nginx

```bash
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 2. Configure Site

Create `/etc/nginx/sites-available/loan-manager`:

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=30r/s;

# Backend API
upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# Frontend
upstream frontend {
    server 127.0.0.1:3000;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# API Server (HTTPS)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration (will be added by certbot)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logging
    access_log /var/log/nginx/api.yourdomain.com.access.log;
    error_log /var/log/nginx/api.yourdomain.com.error.log;

    # API proxy
    location / {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://backend;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }

    # Health check endpoint (no rate limit)
    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }
}

# Frontend Server (HTTPS)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logging
    access_log /var/log/nginx/yourdomain.com.access.log;
    error_log /var/log/nginx/yourdomain.com.error.log;

    # Next.js static files (with caching)
    location /_next/static/ {
        proxy_pass http://frontend;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    # Next.js images
    location /_next/image {
        proxy_pass http://frontend;
        add_header Cache-Control "public, max-age=3600";
    }

    # All other requests
    location / {
        limit_req zone=general_limit burst=50 nodelay;

        proxy_pass http://frontend;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable site:

```bash
# Test configuration
sudo nginx -t

# Enable site
sudo ln -s /etc/nginx/sites-available/loan-manager /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Reload Nginx
sudo systemctl reload nginx
```

---

## SSL Certificate Setup

### 1. Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 2. Obtain Certificates

```bash
# For main domain and www subdomain
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# For API subdomain
sudo certbot --nginx -d api.yourdomain.com

# Follow prompts and provide email address
```

### 3. Auto-Renewal

Certbot automatically creates a cron job. Verify:

```bash
sudo systemctl status certbot.timer

# Test renewal (dry run)
sudo certbot renew --dry-run
```

---

## Systemd Services

### Summary of Services

1. **loan-manager-backend.service** - FastAPI backend
2. **loan-manager-frontend.service** - Next.js frontend
3. **bike-lifecycle-refresh.timer** - Daily materialized view refresh
4. **postgresql.service** - Database (system service)
5. **nginx.service** - Web server (system service)

### Managing Services

```bash
# Start all services
sudo systemctl start loan-manager-backend
sudo systemctl start loan-manager-frontend

# Check status
sudo systemctl status loan-manager-backend
sudo systemctl status loan-manager-frontend

# View logs
sudo journalctl -u loan-manager-backend -f
sudo journalctl -u loan-manager-frontend -f

# Restart after updates
sudo systemctl restart loan-manager-backend
sudo systemctl restart loan-manager-frontend
```

---

## Monitoring & Logging

### 1. Application Logs

```bash
# Backend logs
sudo tail -f /var/log/loan-manager/backend.log

# Nginx access logs
sudo tail -f /var/log/nginx/yourdomain.com.access.log
sudo tail -f /var/log/nginx/api.yourdomain.com.access.log

# Nginx error logs
sudo tail -f /var/log/nginx/yourdomain.com.error.log
sudo tail -f /var/log/nginx/api.yourdomain.com.error.log

# Systemd journal
sudo journalctl -u loan-manager-backend -f
sudo journalctl -u loan-manager-frontend -f
```

### 2. Log Rotation

Create `/etc/logrotate.d/loan-manager`:

```
/var/log/loan-manager/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload loan-manager-backend > /dev/null 2>&1 || true
    endscript
}
```

### 3. Monitoring Checklist

Set up monitoring for:

- [ ] Server CPU usage
- [ ] Server memory usage
- [ ] Disk space usage
- [ ] Database connections
- [ ] API response times
- [ ] Error rates (4xx, 5xx)
- [ ] SSL certificate expiry
- [ ] Backup completion status

---

## Backup Strategy

### 1. Database Backups

Create `/usr/local/bin/backup-loan-manager-db.sh`:

```bash
#!/bin/bash

# Configuration
DB_NAME="loan_manager"
BACKUP_DIR="/var/backups/loan-manager"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/loan_manager_$DATE.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
sudo -u postgres pg_dump $DB_NAME | gzip > $BACKUP_FILE

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup successful: $BACKUP_FILE"

    # Remove old backups
    find $BACKUP_DIR -name "loan_manager_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Old backups cleaned up (retention: $RETENTION_DAYS days)"
else
    echo "Backup failed!" >&2
    exit 1
fi
```

Make executable:

```bash
sudo chmod +x /usr/local/bin/backup-loan-manager-db.sh
```

Create cron job for daily backups:

```bash
sudo crontab -e

# Add line for daily backup at 3:00 AM
0 3 * * * /usr/local/bin/backup-loan-manager-db.sh >> /var/log/loan-manager/backup.log 2>&1
```

### 2. Application Backups

```bash
# Backup uploaded files (if any)
sudo tar -czf /var/backups/loan-manager/uploads_$(date +%Y%m%d).tar.gz \
    /var/www/loan-manager/uploads/

# Backup configuration
sudo tar -czf /var/backups/loan-manager/config_$(date +%Y%m%d).tar.gz \
    /var/www/loan-manager/backend/.env \
    /var/www/loan-manager/frontend/.env.production \
    /etc/nginx/sites-available/loan-manager
```

### 3. Restore Procedure

```bash
# Restore database from backup
gunzip < /var/backups/loan-manager/loan_manager_TIMESTAMP.sql.gz | \
    sudo -u postgres psql loan_manager

# Restore files
sudo tar -xzf /var/backups/loan-manager/uploads_TIMESTAMP.tar.gz -C /
```

---

## Rollback Procedures

### Scenario 1: Bad Deployment (Code Issues)

```bash
# 1. Stop services
sudo systemctl stop loan-manager-backend
sudo systemctl stop loan-manager-frontend

# 2. Rollback to previous git tag
cd /var/www/loan-manager
sudo -u www-data git fetch --all
sudo -u www-data git checkout v1.0.0  # Previous working version

# 3. Reinstall backend dependencies
cd backend
sudo -u www-data bash -c "source venv/bin/activate && pip install -r requirements.txt"

# 4. Rebuild frontend
cd ../frontend
sudo -u www-data npm ci --production
sudo -u www-data npm run build

# 5. Restart services
sudo systemctl start loan-manager-backend
sudo systemctl start loan-manager-frontend

# 6. Verify
curl https://api.yourdomain.com/health
```

### Scenario 2: Database Migration Issues

```bash
# 1. Restore database from last known good backup
gunzip < /var/backups/loan-manager/loan_manager_TIMESTAMP.sql.gz | \
    sudo -u postgres psql loan_manager

# 2. Restart backend
sudo systemctl restart loan-manager-backend

# 3. Verify database state
sudo -u postgres psql loan_manager -c "SELECT * FROM alembic_version;"
```

### Scenario 3: Configuration Issues

```bash
# 1. Restore configuration from backup
sudo tar -xzf /var/backups/loan-manager/config_TIMESTAMP.tar.gz -C /

# 2. Reload services
sudo systemctl daemon-reload
sudo systemctl restart loan-manager-backend
sudo systemctl restart loan-manager-frontend
sudo systemctl reload nginx
```

---

## Post-Deployment Verification

### 1. Health Checks

```bash
# Backend health check
curl https://api.yourdomain.com/health
# Expected: {"status": "healthy"}

# Frontend accessibility
curl -I https://yourdomain.com
# Expected: HTTP/2 200

# SSL certificate check
echo | openssl s_client -connect yourdomain.com:443 -servername yourdomain.com 2>/dev/null | \
    openssl x509 -noout -dates
```

### 2. API Endpoint Tests

```bash
# Test authentication
curl -X POST https://api.yourdomain.com/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"password"}'

# Test bike listing (requires auth token)
curl https://api.yourdomain.com/v1/bikes?limit=5 \
    -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Database Verification

```bash
sudo -u postgres psql loan_manager

-- Check tables exist
\dt

-- Check materialized views
\dm

-- Check indexes
\di

-- Verify data
SELECT COUNT(*) FROM bicycles;
SELECT COUNT(*) FROM companies;
SELECT COUNT(*) FROM branches;
```

### 4. Service Status Check

```bash
# Check all services are running
sudo systemctl is-active loan-manager-backend
sudo systemctl is-active loan-manager-frontend
sudo systemctl is-active postgresql
sudo systemctl is-active nginx

# Check timer is active
sudo systemctl is-active bike-lifecycle-refresh.timer
```

### 5. Performance Verification

```bash
# Run performance tests
cd /var/www/loan-manager
python3 tests/performance/test_load_performance.py --bikes 100

# Check response times
ab -n 100 -c 10 https://api.yourdomain.com/v1/bikes?limit=10
```

### 6. Frontend Verification

Open browser and verify:

- [ ] Homepage loads correctly
- [ ] Login page accessible
- [ ] Dashboard displays data
- [ ] Forms submit successfully
- [ ] API calls work (check browser console)
- [ ] No JavaScript errors
- [ ] Mobile responsive design works

---

## Maintenance Tasks

### Daily

- [ ] Check service status
- [ ] Review error logs
- [ ] Verify backups completed

### Weekly

- [ ] Review disk space usage
- [ ] Check database performance
- [ ] Review security logs
- [ ] Update statistics: `VACUUM ANALYZE;`

### Monthly

- [ ] Review and rotate logs
- [ ] Check SSL certificate expiry
- [ ] Review API usage patterns
- [ ] Database optimization
- [ ] Security updates

### Quarterly

- [ ] Full system backup verification
- [ ] Disaster recovery drill
- [ ] Performance review
- [ ] Capacity planning

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
sudo journalctl -u loan-manager-backend -n 50

# Common issues:
# 1. Database connection failed
#    - Verify DATABASE_URL in .env
#    - Check PostgreSQL is running: sudo systemctl status postgresql
# 2. Port already in use
#    - Check what's using port 8000: sudo lsof -i :8000
# 3. Missing dependencies
#    - Reinstall: pip install -r requirements.txt
```

### Frontend Build Fails

```bash
# Clear cache and rebuild
cd /var/www/loan-manager/frontend
sudo -u www-data rm -rf .next node_modules
sudo -u www-data npm ci
sudo -u www-data npm run build
```

### Database Performance Issues

```bash
# Analyze and vacuum
sudo -u postgres psql loan_manager -c "VACUUM ANALYZE;"

# Check slow queries
sudo -u postgres psql loan_manager -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds';"

# Reindex if needed
sudo -u postgres psql loan_manager -c "REINDEX DATABASE loan_manager;"
```

### High Memory Usage

```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -n 10

# Restart services to free memory
sudo systemctl restart loan-manager-backend
sudo systemctl restart loan-manager-frontend
```

---

## Security Hardening

### 1. Firewall (UFW)

```bash
# Default deny
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# Enable
sudo ufw enable
```

### 2. Fail2Ban

```bash
# Install
sudo apt install fail2ban -y

# Configure for Nginx
sudo tee /etc/fail2ban/jail.local <<EOF
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
EOF

sudo systemctl restart fail2ban
```

### 3. Regular Updates

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Update Python packages
cd /var/www/loan-manager/backend
sudo -u www-data bash -c "source venv/bin/activate && pip list --outdated"

# Update Node packages
cd /var/www/loan-manager/frontend
sudo -u www-data npm outdated
```

---

## Support Contacts

- **System Administrator**: admin@yourdomain.com
- **Database Admin**: dba@yourdomain.com
- **DevOps Team**: devops@yourdomain.com
- **Emergency Hotline**: +94 XXX XXX XXX

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-18
**Next Review**: 2025-12-18
