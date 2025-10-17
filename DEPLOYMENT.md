# COINjecture Faucet API - DigitalOcean Deployment Guide

## Overview
This guide covers deploying the COINjecture Faucet API to DigitalOcean droplet (164.92.89.62).

## Prerequisites
- DigitalOcean droplet with Ubuntu 20.04+ 
- SSH access to droplet
- Domain name (optional, can use IP directly)

## Step 1: Server Setup

### SSH into droplet
```bash
ssh root@164.92.89.62
```

### Update system
```bash
apt update && apt upgrade -y
```

### Install Python 3.9 and dependencies
```bash
apt install -y python3.9 python3.9-pip python3.9-venv nginx git
```

### Create application user
```bash
adduser coinjecture
usermod -aG sudo coinjecture
```

## Step 2: Application Deployment

### Switch to application user
```bash
su - coinjecture
```

### Clone repository
```bash
git clone https://github.com/beanapologist/COINjecture.git
cd COINjecture
```

### Create virtual environment
```bash
python3.9 -m venv venv
source venv/bin/activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Create cache directory
```bash
mkdir -p data/cache
```

## Step 3: Systemd Services

### Create API service
```bash
sudo nano /etc/systemd/system/coinjecture-api.service
```

Add:
```ini
[Unit]
Description=COINjecture Faucet API
After=network.target

[Service]
Type=simple
User=coinjecture
WorkingDirectory=/home/coinjecture/COINjecture
Environment=PATH=/home/coinjecture/COINjecture/venv/bin
ExecStart=/home/coinjecture/COINjecture/venv/bin/python src/api/faucet_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Create cache updater service
```bash
sudo nano /etc/systemd/system/coinjecture-cache.service
```

Add:
```ini
[Unit]
Description=COINjecture Cache Updater
After=network.target

[Service]
Type=simple
User=coinjecture
WorkingDirectory=/home/coinjecture/COINjecture
Environment=PATH=/home/coinjecture/COINjecture/venv/bin
ExecStart=/home/coinjecture/COINjecture/venv/bin/python src/api/update_cache.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

### Enable and start services
```bash
sudo systemctl daemon-reload
sudo systemctl enable coinjecture-api
sudo systemctl enable coinjecture-cache
sudo systemctl start coinjecture-api
sudo systemctl start coinjecture-cache
```

## Step 4: Nginx Configuration

### Create nginx config
```bash
sudo nano /etc/nginx/sites-available/coinjecture
```

Add:
```nginx
server {
    listen 80;
    server_name 164.92.89.62;  # Replace with your domain if available

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Enable site
```bash
sudo ln -s /etc/nginx/sites-available/coinjecture /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 5: Firewall Configuration

### Configure UFW
```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

## Step 6: Verification

### Check services
```bash
sudo systemctl status coinjecture-api
sudo systemctl status coinjecture-cache
```

### Test API endpoints
```bash
curl http://164.92.89.62/health
curl http://164.92.89.62/v1/data/block/latest
```

## Step 7: Monitoring

### View logs
```bash
sudo journalctl -u coinjecture-api -f
sudo journalctl -u coinjecture-cache -f
```

### Check cache files
```bash
ls -la /home/coinjecture/COINjecture/data/cache/
cat /home/coinjecture/COINjecture/data/cache/latest_block.json
```

## Troubleshooting

### Service won't start
```bash
sudo journalctl -u coinjecture-api --no-pager
sudo journalctl -u coinjecture-cache --no-pager
```

### Permission issues
```bash
sudo chown -R coinjecture:coinjecture /home/coinjecture/COINjecture
```

### Port conflicts
```bash
sudo netstat -tlnp | grep :5000
sudo lsof -i :5000
```

## Updates

### Deploy updates
```bash
cd /home/coinjecture/COINjecture
git pull origin main
sudo systemctl restart coinjecture-api
sudo systemctl restart coinjecture-cache
```

## Security Notes

- API is read-only (GET requests only)
- Rate limiting prevents abuse
- No authentication required (public data)
- Firewall configured for HTTP/HTTPS only
- Services run as non-root user

## Performance

- API responds < 100ms
- Cache updates every 30 seconds
- Rate limit: 100 requests/minute per IP
- Nginx handles static file serving
- Systemd auto-restart on failure
