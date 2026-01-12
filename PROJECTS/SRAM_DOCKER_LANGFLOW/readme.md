# Langflow on SURF Research Cloud Ubuntu VM

This GitHub repository enables DataLabs Tech Leads to deploy Langflow 
on SURF Research Cloud Ubuntu VMs with secure HTTPS via DOMAIN name. 
Includes full Docker Compose  stack with Traefik reverse proxy/Let's Encrypt, 
PostgreSQL persistence, Docling support, and automation scripts.

## Prerequisites

SURF Ubuntu 22.04+ VM: public IP, ports 80/443/8080 open, DNS A-record (e.g., langflow.src.surf-hosted.nl). 
Docker/Compose/Python3 installed, non-root SSH, no Nginx conflicts.

## Setup Scripts

### get-files.sh

Fetches files via sparse-checkout.

```bash
#!/bin/bash
mkdir -p LANGFLOW
cd LANGFLOW
git init
git remote add -f origin https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT.git
git config core.sparseCheckout true
echo "PROJECTS/SRAM/DOCKER/LANGFLOW/" > .git/info/sparse-checkout
git pull origin main
mv PROJECTS/SRAM/DOCKER/LANGFLOW/* .
rm -rf PROJECTS
rm -rf .git
echo "------------------------------------------"
echo "Success! Contents of SRAM/DOCKER/LANGFLOW are now in LANGFLOW"
ls -la
```


### create-langflow.sh

Automates: Nginx stop, acme.json, FQDN .env gen, docker perms, compose up.

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
MYFQDN=$(echo $RAWNAME | sed 's/-/\./g' | sed 's/src/\.src\./' | sed 's/surf-hosted/\.surf-hosted\./' | sed 's/nl/.nl/')
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
if sg docker -c "docker compose up -d --build"; then
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


## Docker Files

### Dockerfile

Builds Langflow image with Docling extras for document parsing in healthcare/AI workflows.

```dockerfile
FROM langflowai/langflow:latest

USER root

RUN apt-get update && \
    apt-get install -y libgl1 libglib2.0-0
# Install system dependencies for Docling (GUI/graphics libs)

RUN uv pip install "langflow[docling]"
# Install Langflow with Docling extra via uv (fast pip alternative)
```

Used in `docker-compose.yaml` under `langflow: build: . dockerfile: Dockerfile`. Runs as root for deps. Enables advanced RAG/document flows relevant to DataLabs.[^2]

## docker-compose.yaml

Defines stack: Traefik (proxy/SSL), Langflow (app), Postgres (DB). Auto HTTPS redirect, certs via Let's Encrypt HTTP challenge. Uses `${MYFQDN}` from .env for SURF domains.

```yaml
services:
  traefik:
    image: traefik:v2.11
    container_name: traefik
    dns:
      - 8.8.8.8  # Reliable DNS for cert validation
    restart: unless-stopped
    command:
      # Core Traefik config
      - --api.dashboard=true
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      # HTTP entrypoint (redirects to HTTPS)
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      # Global redirect HTTP → HTTPS
      - --entrypoints.web.http.redirections.entryPoint.to=websecure
      - --entrypoints.web.http.redirections.entryPoint.scheme=https
      # Let's Encrypt ACME HTTP challenge
      - --certificatesresolvers.le.acme.httpchallenge=true
      - --certificatesresolvers.le.acme.httpchallenge.entrypoint=web
      - --certificatesresolvers.le.acme.storage=/letsencrypt/acme.json
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - .acme.json:/letsencrypt/acme.json  # Cert storage (chmod 600)

  langflow:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: langflow
    restart: unless-stopped
    environment:
      # Postgres connection (creds match DB service)
      - LANGFLOW_DATABASE_URL=postgresql://langflow:langflow@langflowdb:5432/langflow
      # Auth: disable auto-login, enable signup
      - LANGFLOW_AUTOLOGIN=false
      - LANGFLOW_NEW_USER_SIGNUP=true
      # Security: replace with strong key
      - LANGFLOW_SECRET_KEY=alongrandomstringhereforsecurity
      - LANGFLOW_LANGFLOW_USER_DEFAULT=false
      # Paths/caching
      - LANGFLOW_CACHEDIR=/app/langflow/.cache
      - DONOT_TRACK=true
    volumes:
      - langflowdata:/app/langflow  # Persistent flows/DB
      - .langflowcache:/app/langflow/.cache
      - .chromedata:/app/chromedata  # Chrome for tools
    user: root
    depends_on:
      db:
        condition: service_healthy
    labels:
      # Traefik routing: HTTPS only, Host match from .env
      - traefik.enable=true
      - traefik.http.routers.langflow.rule=Host(`${MYFQDN}`)
      - traefik.http.routers.langflow.entrypoints=websecure
      - traefik.http.routers.langflow.tls.certresolver=le
      - traefik.http.services.langflow.loadbalancer.server.port=7860  # Langflow port

  db:
    image: postgres:16
    container_name: langflowdb
    restart: unless-stopped
    environment:
      POSTGRES_DB: langflow
      POSTGRES_USER: langflow
      POSTGRES_PASSWORD: langflow
    volumes:
      - postgresdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langflow"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  langflowdata:
  postgresdata:
```

# Langflow Deployment Sequence on SURF VM


SSH into SURF Ubuntu VM as non-root user (ssh user@IP-address) and follow this exact terminal sequence to deploy Dockerized Langflow with HTTPS access via DOMAIN (FQDN).
​

OPEN TERMINAL on Local PC
<br> Follow the Terminal command Sequence shown below: <br> 

```yaml

# 1. login to VM
ssh user@IP-address  

# 2. Open nano  text-editor to create a .sh script
nano get-files.sh

# Open GitHub URL in browser: 
https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT/blob/main/PROJECTS/SRAM_DOCKER_LANGFLOW/get-files.sh
# Select all raw content (right-click > Select All or Ctrl+A).
# Copy to clipboard (Ctrl+C).

# In nano: right-click paste or Ctrl+Shift+V (terminal paste).

# Verify content matches (scroll with arrows):
#Exit: Ctrl+X shift-Y

# Run script in terminal to retreive the required materials
source  get-files.sh
bash  get-files.sh
# outcome: Downloads Langflow files (docker-compose.yaml, etc.) into ./LANGFLOW dir + ls -al display's its content

# Run script in terminal to create Langflow 
source  +x create-langflow.sh
# outcome:  installs ..............
​
```


















