# Prometheus + Traefik (Dockerized) + Grafana (Native) - Downsized Monitoring Stack

A lightweight, production-ready monitoring stack for Ubuntu 22.04 VM with remote HTTPS Prometheus access via Traefik and local Grafana.

**Resource usage**: ~512MB RAM, 0.5 CPU total

## Features

- ✅ **Prometheus**: Remote HTTPS via custom domain (`https://prometheus.yourdomain.com`)
- ✅ **Traefik**: Automatic Let's Encrypt certificates, Docker auto-discovery
- ✅ **Grafana**: Native systemd service (local VM only, secure)
- ✅ **Downsized**: 256MB/0.5CPU limits per container, 2-day retention
- ✅ **Auto-restart**: Survives crashes, VM reboots, network issues


## Directory Structure

```
~/monitoring/
├── Dockerfile                 # Custom Prometheus build
├── docker-compose.yml         # Traefik + Prometheus stack
├── prometheus/
│   └── prometheus.yml         # Minimal self-monitoring config
└── traefik/
    └── acme.json              # Let's Encrypt certificates (empty, 600 perms)
```


## Prerequisites

- Ubuntu 22.04 VM (1 vCPU, 1GB RAM minimum)
- Docker + Docker Compose v2+ installed
- DNS A-record: `prometheus.yourdomain.com` → VM public IP
- Firewall: Ports 80/443 open


## Quick Setup (5 minutes)

```bash
# 1. Create directory structure
mkdir -p ~/monitoring/{prometheus,traefik}
cd ~/monitoring

# 2. Create all files (copy from below)
# 3. Setup Traefik ACME storage
touch traefik/acme.json
chmod 600 traefik/acme.json

# 4. Build & deploy
sudo docker compose build
sudo docker compose up -d

# 5. Install Grafana (native)
sudo apt-get update
sudo apt-get install -y apt-transport-https software-properties-common wget gnupg
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt-get update && sudo apt-get install -y grafana
sudo systemctl enable --now grafana-server
```


## File Contents

### `Dockerfile`

```dockerfile
FROM prom/prometheus:latest

# Copy minimal prometheus.yml
COPY prometheus/prometheus.yml /etc/prometheus/prometheus.yml

EXPOSE 9090
```


### `prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```


### `docker-compose.yml`

```yaml
version: "3.9"

services:
  traefik:
    image: traefik:v3.6.1
    container_name: traefik
    command:
      - "--log.level=INFO"
      - "--api.dashboard=true"
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@yourdomain.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/acme.json:/letsencrypt/acme.json
    restart: unless-stopped
    networks:
      - monitoring

  prometheus:
    build: .
    container_name: prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=2d"
      - "--storage.tsdb.retention.size=512MB"
      - "--web.enable-lifecycle"
    ports:
      - "9090:9090"
    volumes:
      - prometheus-data:/prometheus
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.prometheus.rule=Host(`prometheus.yourdomain.com`)"
      - "traefik.http.routers.prometheus.entrypoints=websecure"
      - "traefik.http.routers.prometheus.tls.certresolver=letsencrypt"
      - "traefik.http.services.prometheus.loadbalancer.server.port=9090"
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
    networks:
      - monitoring

volumes:
  prometheus-data:

networks:
  monitoring:
    driver: bridge
```


### `traefik/acme.json`

```bash
# Create empty file with correct permissions
touch traefik/acme.json
chmod 600 traefik/acme.json
```


## Verification Checklist

| Test | Command | Expected Result |
| :-- | :-- | :-- |
| **Prometheus Local** | `curl http://localhost:9090` | Prometheus HTML page |
| **Traefik Dashboard** | `curl http://localhost:8080/dashboard/` | Traefik UI |
| **Remote HTTPS** | `curl -k https://prometheus.yourdomain.com` | Prometheus HTML |
| **Grafana Local** | `curl http://localhost:3000` | Grafana login page |
| **Containers Healthy** | `sudo docker compose ps` | All services "Up" |

```bash
# Full verification
sudo docker compose ps
curl http://localhost:9090
curl http://localhost:8080/dashboard/
curl -k https://prometheus.yourdomain.com
curl http://localhost:3000
sudo systemctl status grafana-server
```


## Grafana Setup

1. **Access**: `http://localhost:3000` (admin/admin)
2. **Add Prometheus datasource**:
    - URL: `https://prometheus.yourdomain.com`
    - Save \& test ✅
3. **Import dashboard**: ID `1860` (Prometheus 2.0 Overview)

## Maintenance

### Daily Checks

```bash
cd ~/monitoring
sudo docker compose ps          # Container status
sudo docker compose logs --tail=50  # Recent logs
sudo systemctl status grafana-server  # Grafana status
df -h prometheus-data          # Disk usage
```


### Updates

```bash
cd ~/monitoring
sudo docker compose pull
sudo docker compose up -d
sudo apt-get update && sudo apt-get upgrade grafana
sudo systemctl restart grafana-server
```


### Backups

```bash
# Prometheus data
sudo tar czf prometheus-backup-$(date +%Y%m%d).tar.gz -C ~/monitoring prometheus-data/

# Grafana (dashboards, datasources)
sudo tar czf grafana-backup-$(date +%Y%m%d).tar.gz /var/lib/grafana/
```


### Complete Stop/Start

```bash
cd ~/monitoring
sudo docker compose down        # Stop Docker services
sudo docker compose up -d       # Start Docker services
sudo systemctl restart grafana-server  # Restart Grafana
```


### Troubleshooting

| Issue | Fix |
| :-- | :-- |
| **Traefik 404** | Check DNS → VM IP, ports 80/443 open |
| **Cert errors** | `sudo docker logs traefik`, check `acme.json` perms |
| **Prometheus down** | `sudo docker logs prometheus` |
| **Grafana 3000 refused** | `sudo systemctl status grafana-server` |
| **Docker socket errors** | `sudo chmod 666 /var/run/docker.sock` |

## Security Hardening (Production)

```bash
# 1. Grafana local-only binding
sudo sed -i 's/http_addr =/http_addr = 127.0.0.1/' /etc/grafana/grafana.ini
sudo systemctl restart grafana-server

# 2. Change Grafana admin password (first login)

# 3. Firewall (ufw)
sudo ufw allow 80,443,8080,9090,3000
sudo ufw enable
```


## VM Reboot Recovery

**All services auto-restart**:

- Docker: `restart: unless-stopped`
- Grafana: systemd `Restart=always`

**Post-reboot verification**:

```bash
sudo docker compose ps
sudo systemctl status grafana-server
curl -k https://prometheus.yourdomain.com
```
***

## SSH Tunnel Access (Recommended)

### How it works

```
Your Windows PC              SSH Tunnel                    Ubuntu VM
----------------          -----------------             ----------------
Browser: http://localhost:3000  ↔  Port 3000  ↔  ssh -L 3000:localhost:3000  ↔  Grafana: localhost:3000
```

**Step-by-step:**

1. **On your Windows PC**, open **PowerShell** and run:

```powershell
ssh -L 3000:localhost:3000 rvanderwil@145.38.189.5
```

    - This creates an **encrypted tunnel** from your PC's port 3000 to the VM's port 3000
    - Keep this PowerShell window **open** (the tunnel stays active)
2. **On your Windows PC**, open your **web browser** and go to:

```
http://localhost:3000
```

    - **NOT** `http://145.38.189.5:3000`
    - The `localhost:3000` on your PC gets **forwarded through the tunnel** to Grafana on the VM
3. **Login**: `admin` / `admin` (change password on first login)

### Visual flow

```
[Browser on PC] ----> localhost:3000 ----> [SSH Tunnel] ----> VM localhost:3000 ----> [Grafana]
```


### Why `localhost:3000` instead of VM IP?

```
❌ WRONG: http://145.38.189.5:3000
  ↓
  Goes directly to VM over the public internet (port 3000 must be open)

✅ CORRECT: http://localhost:3000  
  ↓
  Goes through your secure SSH tunnel (port 3000 stays closed to the world)
```


### Keep tunnel alive

The SSH session **must stay open** in PowerShell. To run tunnel in background:

```powershell
ssh -L 3000:localhost:3000 -N -f rvanderwil@145.38.189.5
```

- `-N`: No remote command
- `-f`: Background (frees up terminal)

**Close tunnel:**

```powershell
taskkill /IM ssh.exe /F
```


### Troubleshooting

| Symptom | Fix |
| :-- | :-- |
| `http://localhost:3000` "connection refused" | SSH tunnel not running (`ssh -L ...`) |
| SSH tunnel closes | VM rebooted, network dropped |
| "Port already in use" | Kill old tunnel: `taskkill /IM ssh.exe /F` |

**Result**: Secure access to Grafana without opening port 3000 publicly. Perfect for your "local Grafana" setup! 🔒

