# 🧪 PathView + PathSim — Secure HTTPS Deployment on SURF Research Cloud

Deploy [PathView](https://github.com/pathsim/pathview), the visual node editor for dynamic systems simulation with [PathSim](https://github.com/pathsim/pathsim), on a remote Ubuntu VM accessible via a secure HTTPS domain URL.

This setup uses **Docker**, **Traefik** (reverse proxy + automatic SSL via Let's Encrypt), and the official **PathView Python package** — no manual certificate management needed.

---

## 📋 Prerequisites

- A SURF Research Cloud Ubuntu 22.04 VM (or any Ubuntu VM with a public FQDN)
- Ports **80** and **443** open in your security group (inbound TCP)
- Port **22** open for SSH access
- Docker and Docker Compose V2 installed
- `git`, `python3`, `curl` available on the VM

> ⚠️ Do **not** open port 5000 externally. Traefik routes all traffic internally.

---

## 📁 Project Structure

Create a dedicated project folder on your VM:

```bash
mkdir ~/sram_pathview && cd ~/sram_pathview
```

You will create the following files inside this folder:

```
sram_pathview/
├── Dockerfile
├── docker-compose.yaml
├── create-pathview.sh
└── acme.json              # auto-created by the script
```

---

## 🐳 Step 1 — Create the `Dockerfile`

PathView is published as an official Python package. The Dockerfile installs it directly from PyPI — no cloning or `requirements.txt` needed.

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pathview==0.8.4

EXPOSE 5000

CMD ["pathview", "serve", "--host", "0.0.0.0", "--port", "5000", "--no-browser"]
```

> PathView's built-in server uses **Waitress** (production-grade WSGI) and serves both the Flask API and the static SvelteKit frontend on a single port.

---

## ⚙️ Step 2 — Create the `docker-compose.yaml`

This file configures two services:
- **Traefik** — reverse proxy that handles HTTPS and auto-provisions the Let's Encrypt SSL certificate
- **PathView** — the simulation application container

```yaml
services:
  traefik:
    image: traefik:v3.6.1
    container_name: traefik_router
    restart: unless-stopped
    command:
      - "--api.insecure=false"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.web.http.redirections.entryPoint.to=websecure"
      - "--entrypoints.web.http.redirections.entryPoint.scheme=https"
      - "--certificatesresolvers.myresolver.acme.httpchallenge=true"
      - "--certificatesresolvers.myresolver.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.myresolver.acme.email=admin@${MYFQDN}"
      - "--certificatesresolvers.myresolver.acme.storage=/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./acme.json:/acme.json"

  pathview:
    build: .
    container_name: sram_pathview
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.pathview.rule=Host(`${MYFQDN}`)"
      - "traefik.http.routers.pathview.entrypoints=websecure"
      - "traefik.http.routers.pathview.tls.certresolver=myresolver"
      - "traefik.http.services.pathview.loadbalancer.server.port=5000"
```

> **Why Traefik v3.6.1?** Docker Engine v29 raised the minimum API version to 1.40. Traefik versions below v3.6.1 hardcode API v1.24 and fail to connect to the Docker daemon. Always use `traefik:v3.6.1` or higher on modern Docker installations.

---

## 🚀 Step 3 — Create the Deployment Script `create-pathview.sh`

This script automates the full deployment: stopping Nginx if present, generating `acme.json`, auto-detecting your SURF Research Cloud FQDN, and starting all containers.

```bash
#!/bin/bash
set -e
echo "-------------------------------------------------------"
echo "Starting Deployment Script $(date)"
echo "-------------------------------------------------------"

echo "Step 1: Stopping and disabling Nginx..."
if systemctl is-active --quiet nginx; then
  sudo systemctl stop nginx
  sudo systemctl disable nginx
  echo "Nginx has been stopped and disabled."
else
  echo "Nginx was not running, skipping."
fi

echo "Step 2: Configuring Traefik SSL storage acme.json..."
if [ ! -f acme.json ]; then
  sudo touch acme.json
  sudo chmod 600 acme.json
  echo "acme.json created with secure permissions 600."
else
  sudo chmod 600 acme.json
  echo "acme.json already exists, permissions reset to 600."
fi

echo "Step 2.5: Automatically detecting FQDN and creating .env..."
rm -rf .env
touch .env
RAWNAME=$(python3 -c "import socket; print(socket.getfqdn())")
# Converts e.g. pathsim-cyber-secure-te-src-surf-hosted-nl
# into: pathsim.cyber-secure-te.src.surf-hosted.nl
MYFQDN=$(echo $RAWNAME \
  | sed 's/-src-surf-hosted-nl/.src.surf-hosted.nl/' \
  | sed 's/-/\./')
echo "MYFQDN=$MYFQDN" >> .env
echo "--------------------------------"
echo "Success! .env file has been created."
echo "Current content of .env:"
cat .env
echo "--------------------------------"

echo "Step 3: Checking Docker group membership for $USER..."
if groups $USER | grep -q docker; then
  echo "User $USER is already in the docker group."
else
  sudo usermod -aG docker $USER
  newgrp docker
  echo "User $USER added to the docker group."
fi

echo "Step 4: Building and starting containers with Traefik..."
if sg docker -c "docker compose up -d --build --force-recreate"; then
  echo "-------------------------------------------------------"
  echo "SUCCESS! Containers are building/starting."
else
  echo "ERROR: Docker compose failed to start."
  exit 1
fi

echo "Step 5: Finalizing..."
sg docker -c "docker ps"
echo "--- Traefik Routing Rule ---"
sg docker -c "docker compose config | grep -i Host"
echo "-------------------------------------------------------"
echo "SETUP COMPLETE! Traefik on ports 80/443."
echo "-------------------------------------------------------"
```

---

## ▶️ Step 4 — Run the Deployment

Make the script executable and launch it:

```bash
chmod +x create-pathview.sh
./create-pathview.sh
```

After the script completes, wait **15–30 seconds** for Traefik to request the Let's Encrypt certificate. Then open your browser at:

```
https://<your-fqdn>
```

For example:
```
https://pathsim.cyber-secure-te.src.surf-hosted.nl
```

---

## 🔍 Step 5 — Verify & Troubleshoot

**Check running containers:**
```bash
docker ps
```

**Check Traefik logs for SSL certificate status:**
```bash
docker logs traefik_router | grep -i "acme\|error"
```

**Check PathView application logs:**
```bash
docker logs sram_pathview
```

**Clean restart (if certificate is stuck):**
```bash
docker compose down
sudo rm -f acme.json
sudo touch acme.json && sudo chmod 600 acme.json
./create-pathview.sh
```

---

## 🐛 Known Issues & Fixes

| Symptom | Cause | Fix |
|---|---|---|
| `TRAEFIK DEFAULT CERT` in browser | Traefik cannot reach Docker daemon | Use `traefik:v3.6.1` or higher |
| `client version 1.24 is too old` in logs | Docker Engine v29 broke older Traefik | Upgrade to `traefik:v3.6.1` |
| `No such file or directory: requirements.txt` | Dockerfile points to wrong path | Use `pip install pathview==0.8.4` directly |
| FQDN generates double dots e.g. `..src..` | Aggressive `sed` replacement | Use targeted `sed` on `-src-surf-hosted-nl` suffix only |
| `version` attribute warning in compose | Obsolete Docker Compose V2 field | Remove `version:` line from `docker-compose.yaml` |

---

## 🏗️ Architecture

```
Browser (HTTPS 443)
        │
        ▼
  [ Traefik v3.6.1 ]  ← Auto SSL via Let's Encrypt (HTTP Challenge)
        │
        ▼ internal Docker network (port 5000)
  [ PathView Container ]
   Flask + Waitress
   SvelteKit frontend
   PathSim backend
```

---

## 📦 Key Dependencies

| Component | Version | Role |
|---|---|---|
| `pathview` | 0.8.4 | Visual node editor + Flask server |
| `pathsim` | latest | Differential equation simulation engine |
| `traefik` | v3.6.1 | Reverse proxy + automatic HTTPS |
| `python` | 3.11-slim | Container base image |

---

## 📄 License

MIT — see [PathView repository](https://github.com/pathsim/pathview) for details.
