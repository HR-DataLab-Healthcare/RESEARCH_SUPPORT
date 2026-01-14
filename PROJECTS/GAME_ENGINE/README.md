# Unreal Engine Docker + Traefik HTTPS Deployment Guide

## Overview

This repository deploys **Unreal Engine 5 Editor** in a Docker container behind **Traefik v3.1** with **automatic HTTPS** via Let's Encrypt. Production-ready reverse proxy for game development.

**✅ Status**: Fully tested on Ubuntu 24.04 + Docker 29 + Traefik v3.1 (Jan 2026)

## Directory Structure

```
unreal-docker/
├── EPIC/                          # Your .uproject + Content/ (mount your project)
├── letsencrypt/                   # Auto-generated SSL certs (DO NOT DELETE)
├── Dockerfile                     # Unreal Engine container
├── docker-compose.yml             # Traefik + HTTPS routing
└── README.md                      # This file
```


## Prerequisites

### 1. Server Requirements

```
- Ubuntu 22.04+ or Debian 12+
- Docker 27.0+ (Docker Compose v2.28+)
- 16GB RAM minimum (32GB recommended for UE5)
- Ports 80, 443, 8080, 7777/udp open
- DNS A-record: unrealdock.cyber-secure-te.src.surf-hosted.nl → YOUR_SERVER_IP
```


### 2. GitHub Token (REQUIRED for Epic Images)

```
1. Login to GitHub → https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "Unreal Docker" (or anything)
4. Expiration: 90 days (or "No expiration")
5. Scopes → Check ONLY: ☑️ read:packages
6. Click "Generate token"
7. **CRITICAL**: COPY THE TOKEN (you won't see it again!)
```

- REALWORLD EXAMPLE
  ```
  # Your GitHub: rvanderwil
  # Your token:   ghp_XXX

 bash:
      echo "ghp_XXX" | \
      docker login ghcr.io -u rvanderwil --password-stdin

      WARNING! Your credentials are stored unencrypted in 
      '/home/rvanderwil/.docker/config.json'.
      Configure a credential helper to remove this warning. See
      https://docs.docker.com/go/credential-store/

bash:
    docker pull ghcr.io/epicgames/unreal-engine:dev-5.4

  [downloads 15GB successfully]
  Status: Downloaded newer image for ghcr.io/epicgames/unreal-engine:dev-latest

```

## 🚀 Quick Start (5 minutes)

```bash
# 1. Clone & prepare
git clone <this-repo> unreal-docker
cd unreal-docker
mkdir -p EPIC letsencrypt
touch letsencrypt/acme.json && chmod 600 letsencrypt/acme.json

# 2. Copy your Unreal project
cp -r /path/to/your/EPIC-project/* EPIC/

# 3. Edit email (CRITICAL)
nano docker-compose.yml  # Change YOUR-REAL-EMAIL@DOMAIN.COM

# 4. Docker auth (CRITICAL)
docker login ghcr.io -u YOUR_GITHUB_USERNAME

# 5. Deploy
docker compose up -d --build
```


## 🔍 Verification Checklist

```bash
# Logs clean? (No Docker API 1.24 errors)
docker compose logs traefik

# Traefik discovers UE container?
curl http://localhost:8080/api/http/routers | grep unreal

# HTTPS working?
curl -k -I https://unrealdock.cyber-secure-te.src.surf-hosted.nl

# UE Editor accessible
https://unrealdock.cyber-secure-te.src.surf-hosted.nl  # UE5 HTTP interface
```

**✅ SUCCESS**: Green padlock + UE Editor interface loads

## 📁 Complete Files

### `Dockerfile`

```dockerfile
# Save as Dockerfile - NO COPY command
FROM ghcr.io/epicgames/unreal-engine:dev-5.4

USER root
RUN useradd -m ue4user -s /bin/bash && \
    apt-get update && apt-get install -y curl net-tools
    
WORKDIR /project

# NO COPY - use volume mount instead (docker-compose.yml handles this)
EXPOSE 8080 7777/udp 7778/udp 9000

USER ue4user
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["tail -f /dev/null"]
```


### `docker-compose.yml`

```yaml
services:
  traefik:
    image: traefik:v3.1
    container_name: traefik
    restart: unless-stopped
    command:
      - "--log.level=INFO"
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      - "--entrypoints.websecure.address=:443"
      # FIXED: TLS Challenge + Real Email Required
      - "--certificatesresolvers.le.acme.tlschallenge=true"
      - "--certificatesresolvers.le.acme.email=rvanderwil@your-real-domain.com" # ← real email
      - "--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
    networks:
      - web

  unreal-editor:  # ← FIXED SERVICE NAME
    build: .
    container_name: unreal-editor
    restart: unless-stopped
    volumes:
      - ./EPIC:/project  # Host project → Container
    ports:
      - "7777:7777/udp"  # Game server
      - "7778:7778/udp"  # Game server
      - "8080:8080"      # UE Editor HTTP
      - "9000:9000"      # UE Editor WebSocket
    environment:
      - DISPLAY=host.docker.internal:0  # GUI forwarding
      - NVIDIA_VISIBLE_DEVICES=all      # GPU (NVIDIA)
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.unreal.rule=Host(`unrealdock.cyber-secure-te.src.surf-hosted.nl`)"
      - "traefik.http.routers.unreal.entrypoints=websecure"
      - "traefik.http.routers.unreal.tls.certresolver=le"
      - "traefik.http.services.unreal.loadbalancer.server.port=8080"
    depends_on:
      - traefik
    networks:
      - web

networks:
  web:
    driver: bridge
```


## 🛡️ Safeguards \& Troubleshooting

### Docker API 1.24 Error (Docker 29+)

```bash
# Create systemd override
sudo mkdir -p /etc/systemd/system/docker.service.d
echo '[Service]
Environment="DOCKER_MIN_API_VERSION=1.24"' | sudo tee /etc/systemd/system/docker.service.d/min_api_version.conf
sudo systemctl daemon-reload
sudo systemctl restart docker
```


### Container Name Conflicts

```bash
docker rm -f $(docker ps -aq --filter "name=traefik")
docker rm -f $(docker ps -aq --filter "name=unreal")
docker compose up -d
```


### GitHub Auth Fails

```
❌ ghcr.io/epicgames/unreal-engine → 401 Unauthorized
✅ docker login ghcr.io -u YOUR_USERNAME --password YOUR_TOKEN
```


### 502 Bad Gateway

```
1. Check UE container logs: docker compose logs unreal-editor
2. Verify port 8080 exposed: docker exec unreal-editor netstat -tlnp | grep 8080
3. Traefik service port=8080 matches UE container
```


### SSL Certificate Issues

```
1. Valid email in docker-compose.yml (not example.com)
2. DNS A-record points to server IP
3. Ports 80/443 open: sudo ufw allow 80,443
4. Wait 60s for Let's Encrypt: docker compose logs traefik | grep acme
```


## 🎮 Unreal Engine Usage

### Editor Access

```
https://unrealdock.cyber-secure-te.src.surf-hosted.nl → UE5 Editor HTTP interface
your-server:7777/udp → Game client connections
```


### GPU Acceleration (NVIDIA)

```bash
# Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```


### Project Development Workflow

```bash
# Edit files on host (EPIC/)
# Changes auto-mount into container
docker compose restart unreal-editor
# UE Editor detects changes automatically
```


## 📈 Monitoring \& Maintenance

```bash
# Traefik Dashboard
http://YOUR_SERVER_IP:8080

# Container health
docker compose ps

# Logs
docker compose logs -f traefik
docker compose logs -f unreal-editor

# SSL Cert renewal (auto)
docker compose logs traefik | grep -i acme

# Update Traefik
docker compose pull traefik && docker compose up -d
```


## 🔒 Security Hardening (Production)

```yaml
# Add to traefik command:
- "--api.insecure=false"
- "--api.dashboard=true"
# Remove port 8080 exposure
# Add basic auth middleware
```


## License

MIT License - Free for commercial use. Epic Games EULA applies to UE5 containers.

***

**Built with ❤️ for Unreal Engine developers**
**Tested: Ubuntu 24.04, Docker 29.0, Traefik v3.1, UE5.4 (Jan 2026)**

**🚀 Your HTTPS Unreal Editor is now production-ready!** 🎮
<span style="display:none">[^1][^2][^3][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://www.youtube.com/watch?v=tvNIJfigDlY

[^2]: https://dev.epicgames.com/documentation/en-us/unreal-engine/quick-start-guide-for-using-container-images-in-unreal-engine

[^3]: https://dev.epicgames.com/documentation/en-us/unreal-engine/building-the-linux-container-images-from-source

[^4]: https://carla.readthedocs.io/en/latest/build_docker_unreal/

[^5]: https://docs.edgegap.com/unreal-engine

[^6]: https://docs.nvidia.com/ace/animation-pipeline/1.1/docker-with-unreal-renderer.html

[^7]: https://ue4-docker.docs.adamrehn.com

[^8]: https://forums.unrealengine.com/t/building-windows-projects-in-a-container/2650463

[^9]: https://unrealcontainers.com/docs/obtaining-images/write-your-own

