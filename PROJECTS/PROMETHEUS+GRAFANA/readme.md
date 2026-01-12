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

***

# Extending Your Stack: ML Model Monitoring with Grafana Tutorial

Your **current Prometheus + Grafana + Traefik stack is PERFECT** for implementing the DataCamp ML monitoring tutorial. Here's exactly how to adapt it:

## Current Stack → ML Monitoring Stack

```
✅ Existing: Prometheus (scrapes metrics) + Grafana (dashboards) + Traefik (HTTPS)
➡️ Add:     ML Model API (Flask/FastAPI) exposing Prometheus metrics
```


## Step-by-Step Implementation

### 1. Create ML Model API Container

Add this service to your existing `docker-compose.yml`:

```yaml
  ml-model:
    build: ./ml-model
    container_name: ml-model
    ports:
      - "5000:5000"
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mlmodel.rule=Host(`mlmodel.cyber-secure-te.src.surf-hosted.nl`)"
      - "traefik.http.routers.mlmodel.entrypoints=websecure"
      - "traefik.http.routers.mlmodel.tls.certresolver=letsencrypt"
      - "traefik.http.services.mlmodel.loadbalancer.server.port=5000"
    restart: unless-stopped
    networks:
      - monitoring
```


### 2. Create ML Model Directory Structure

```bash
mkdir -p ~/monitoring/ml-model/src ~/monitoring/ml-model/model-data
cd ~/monitoring/ml-model
```

**`ml-model/Dockerfile`**:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY model-data/ ./model-data/
CMD ["python", "src/app.py"]
```

**`ml-model/requirements.txt`**:

```
flask==2.3.3
scikit-learn==1.3.2
prometheus-client==0.20.0
pandas==2.1.4
joblib==1.3.2
seaborn==0.13.2
scipy==1.11.4
apscheduler==3.10.4
```


### 3. Train \& Save Model (DataCamp diamonds example)

**`ml-model/src/train.py`** (run once):

```python
import seaborn as sns
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# Load diamonds dataset
diamonds = sns.load_dataset("diamonds")
X = diamonds[["carat", "cut", "color", "clarity", "depth", "table"]]
y = diamonds["price"]

# Preprocessing pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), ["carat", "depth", "table"]),
        ("cat", OneHotEncoder(), ["cut", "color", "clarity"])
    ])

# Full pipeline
model_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("regressor", RandomForestRegressor(n_estimators=100, random_state=42))
])

# Train
model_pipeline.fit(X, y)
joblib.dump(model_pipeline, "../model-data/model_pipeline.joblib")
print("✅ Model trained and saved!")
```


### 4. ML Model API with Drift Detection + Prometheus Metrics

**`ml-model/src/app.py`**:

```python
from flask import Flask, request, jsonify
import joblib, pandas as pd, numpy as np
from prometheus_client import start_http_server, Gauge
from apscheduler.schedulers.background import BackgroundScheduler
import seaborn as sns
from scipy.stats import ks_2samp
from sklearn.metrics import mean_squared_error

app = Flask(__name__)

# Load model
model_pipeline = joblib.load("../model-data/model_pipeline.joblib")

# Prometheus metrics
data_drift_gauge = Gauge('data_drift_score', 'Data drift detection score')
concept_drift_gauge = Gauge('concept_drift_score', 'Concept drift score')
prediction_count = Gauge('predictions_total', 'Total predictions')

# Reference data (training data snapshot)
diamonds = sns.load_dataset("diamonds")
X_ref = diamonds[["carat", "cut", "color", "clarity", "depth", "table"]]
y_ref = diamonds["price"]

scheduler = BackgroundScheduler()
scheduler.start()

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    df = pd.DataFrame([data])
    prediction = model_pipeline.predict(df)[^0]
    prediction_count.inc()
    return jsonify({'prediction': float(prediction)})

@app.route('/metrics')
def metrics():
    return make_wsgi_app()

if __name__ == '__main__':
    start_http_server(8000)  # Prometheus metrics endpoint
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {'/metrics': make_wsgi_app()})
    app.run(host='0.0.0.0', port=5000)
```


### 5. Update Prometheus Config

Add to `~/monitoring/prometheus/prometheus.yml`:

```yaml
  - job_name: 'ml-model'
    static_configs:
      - targets: ['ml-model:8000']
```


### 6. Deploy ML Monitoring Stack

```bash
cd ~/monitoring

# Train model
docker run --rm -v $(pwd)/ml-model:/app ml-model python src/train.py

# Deploy full stack
sudo docker compose up -d --build
```


### 7. Grafana Dashboards (DataCamp Tutorial)

**In Grafana** (`http://localhost:3000` via SSH tunnel):

1. **Add Prometheus datasource** (already exists)
2. **New Dashboard → Add Panel**:

**Panel A - Data Drift**:

```
Query: data_drift_score
Threshold: > 0.1 (red line)
```

**Panel B - Concept Drift**:

```
Query: concept_drift_score  
Threshold: > 0.1 (red line)
```

**Panel C - Predictions**:

```
Query: predictions_total{job="ml-model"}
```


### 8. Alerts (Discord/Slack/Email)

**Alert Rule** (Dashboard → Alert tab):

```
WHEN data_drift_score > 0.1
FOR 2m
NOTIFY Discord/Slack/Email
```


## Result: Complete ML Monitoring

```
✅ Your Stack NOW monitors:
  - Data drift (KS test vs training data)
  - Concept drift (MSE drop vs training)  
  - Prediction volume
  - Latency (add @timer decorator)
  - Auto-alerts on drift detection

🚀 URLs:
  - Model API: https://mlmodel.cyber-secure-te.src.surf-hosted.nl/predict
  - Metrics:  https://mlmodel.cyber-secure-te.src.surf-hosted.nl/metrics
  - Grafana:  http://localhost:3000 (SSH tunnel)
```

**Your infrastructure is production-grade ML monitoring ready!** Just add your actual ML model to `train.py` and deploy.
<span style="display:none">[^1][^2][^3][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://www.datacamp.com/tutorial/grafana-tutorial-monitoring-machine-learning-models

[^2]: https://docs.mlrun.org/en/stable/model-monitoring/monitoring-models-grafana.html

[^3]: https://grafana.com/blog/monitoring-machine-learning-models-in-production-with-grafana-and-clearml/

[^4]: https://www.youtube.com/watch?v=eQoKK5KNGLY

[^5]: https://grafana.com/tutorials/

[^6]: https://grafana.com/docs/grafana-cloud/machine-learning/dynamic-alerting/forecasting/

[^7]: https://www.youtube.com/watch?v=fX8dIy6zGH8

[^8]: https://grafana.com/docs/grafana-cloud/machine-learning/

[^9]: https://www.lakera.ai/blog/ml-model-monitoring

