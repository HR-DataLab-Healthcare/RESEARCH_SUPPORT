# Langflow on SURF Research Cloud Ubuntu VM

This repository guides Tech Leads to deploy Langflow on SURF Research Cloud (SRC) Ubuntu VMs with secure HTTPS via a DOMAIN name, using SURF Research Access Management (SRAM) as the authorisation portal.
It includes a full Docker Compose stack with Traefik reverse proxy/Let's Encrypt, PostgreSQL persistence, Docling support, and automation scripts.

> **Corrections in this version:** the original `create-langflow.sh` FQDN-detection sed chain could corrupt domains containing multiple hyphens (e.g., `surf-hosted` was mis-parsed into `surf.hosted`). The `docker-compose.yaml` Traefik label also referenced a hardcoded example domain instead of consuming the `.env` variable. Both issues are fixed below.

<img width="1374" height="1132" alt="image" src="https://github.com/user-attachments/assets/09d75d1f-71c4-4529-bc38-de0aa995c01b" />

## Prerequisites

- SURF Ubuntu 22.04+ VM: public IP, ports 80/443/8080 open, DNS A-record (e.g., `zorglang.betekenisvolle.src.surf-hosted.nl`).
- Docker, Docker Compose, and Python3 installed.
- Non-root SSH access, no conflicting Nginx service.

## Setup Scripts

### get-files.sh

Fetches all project files via git sparse-checkout into `~/LANGFLOW`.

```bash
#!/bin/bash
set -e

mkdir -p ~/LANGFLOW
cd ~/LANGFLOW

git init
git remote add -f origin https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT.git
git config core.sparseCheckout true
echo "PROJECTS/SRAM_DOCKER_LANGFLOW/*" >> .git/info/sparse-checkout
git pull origin main

mv PROJECTS/SRAM_DOCKER_LANGFLOW/* .
rm -rf PROJECTS
rm -rf .git

echo "------------------------------------------"
echo "Success! Contents of SRAM_DOCKER_LANGFLOW are now in ~/LANGFLOW"
ls -la
```

### create-langflow.sh (corrected)

The FQDN-detection logic below replaces the previous chained `sed` substitutions, which could break domains with multiple hyphens (e.g., `surf-hosted`). It now splits the raw hostname by hyphen and rebuilds the FQDN by fixed position, so `surf-hosted` stays joined correctly.

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
rm -f .env
touch .env

RAWNAME=$(python3 -c "import socket; print(socket.getfqdn())")

# Rebuild FQDN by position instead of fragile sequential sed substitutions.
# Expected pattern: name-org-src-surf-hosted-nl
MYFQDN=$(python3 -c "
raw = '$RAWNAME'
parts = raw.split('-')
if len(parts) == 6:
    print(f'{parts}.{parts}.{parts}.{parts}-{parts}.{parts}')[1][2][3][4][5]
else:
    print(raw)
")

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

Builds the Langflow image with Docling extras for document parsing in healthcare/AI workflows.

```dockerfile
FROM langflowai/langflow:latest

USER root

# Install system dependencies for Docling
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0

# Install Langflow with pymysql extra
RUN uv pip install pymysql

# Install Langflow with Docling extra
RUN uv pip install 'langflow[docling]' lfx-docling

# Install Langflow with Docling extraffmpeg to process video input (mp4)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Switch back to Langflow's default user
USER 1000
```

### docker-compose.yaml (corrected)

Defines the stack: Traefik (proxy/SSL), Langflow (app), Postgres (DB). The Traefik label now always reads the domain from `${MYFQDN}` in `.env` — the previous hardcoded example domain has been removed so the stack is portable across any SURF VM.

```yaml
services:
  traefik:
    image: traefik:v2.11
    container_name: traefik
    dns:
      - 8.8.8.8
    restart: unless-stopped
    command:
      - --api.dashboard=true
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      - --entrypoints.web.http.redirections.entryPoint.to=websecure
      - --entrypoints.web.http.redirections.entryPoint.scheme=https
      - --certificatesresolvers.le.acme.httpchallenge=true
      - --certificatesresolvers.le.acme.httpchallenge.entrypoint=web
      - --certificatesresolvers.le.acme.storage=/letsencrypt/acme.json
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./acme.json:/letsencrypt/acme.json

  langflow:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: langflow
    restart: unless-stopped
    environment:
      - LANGFLOW_DATABASE_URL=postgresql://langflow:langflow@db:5432/langflow
      - LANGFLOW_AUTO_LOGIN=false
      - LANGFLOW_NEW_USER_SIGNUP=true
      - LANGFLOW_SECRET_KEY=a_long_random_string_here_for_security
      - LANGFLOW_LANGFLOW_USER_DEFAULT=false
      - LANGFLOW_CACHE_DIR=/app/langflow/cache
      - DO_NOT_TRACK=true
    volumes:
      - langflow_data:/app/langflow
      - ./langflow_cache:/app/langflow/cache
      - ./chroma_data:/app/chroma_data
    user: root
    depends_on:
      db:
        condition: service_healthy
    labels:
      - traefik.enable=true
      - traefik.http.routers.langflow.rule=Host(`${MYFQDN}`)
      - traefik.http.routers.langflow.entrypoints=websecure
      - traefik.http.routers.langflow.tls.certresolver=le
      - traefik.http.services.langflow.loadbalancer.server.port=7860
      - traefik.docker.network=langflow_default

  db:
    image: postgres:16
    container_name: langflow_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: langflow
      POSTGRES_USER: langflow
      POSTGRES_PASSWORD: langflow
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langflow"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  langflow_data:
  postgres_data:
```

> **Security note:** replace `LANGFLOW_SECRET_KEY` and the default `langflow` Postgres credentials with strong, unique values (e.g., via `openssl rand -hex 32`) before running in production. Do not commit real secrets to version control.

### Optional: rate-limit fix

If Langflow throws `SystemError: (11, 'Resource temporarily unavailable')`, add `ulimits` to the `langflow` service:

```yaml
  langflow:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: langflow
    restart: unless-stopped
    ulimits:
      nofile:
        soft: 65535
        hard: 65535
```

## Deployment Sequence

SSH into the SURF Ubuntu VM as a non-root user, then run:

```bash
# 1. Login to VM
ssh user@IP-address

# 2. Retrieve project files
nano get-files.sh
# paste get-files.sh content, save (Ctrl+X, Y, Enter)
chmod +x get-files.sh
./get-files.sh

# 3. Deploy Langflow
chmod +x create-langflow.sh
./create-langflow.sh
```

After deployment, verify the Traefik routing rule resolves to your actual domain:

```bash
docker compose config | grep -i Host
```

This should output `Host(\`xxxxxxx.betekenisvolle.src.surf-hosted.nl\`)` exactly, confirming the corrected FQDN logic and the `${MYFQDN}` variable in `docker-compose.yaml` are working together correctly.

Here  xxxxxxx is the name of the workspace

<img width="661" height="574" alt="image" src="https://github.com/user-attachments/assets/b163f668-2107-4f29-8a8e-a67188291c9c" />


---



# Bulk Create Users in Langflow (Docker + Ubuntu VM)

This guide explains step-by-step how to create multiple user accounts in a **Langflow** instance running in **Docker** on an **Ubuntu VM**.

---

## 📋 Prerequisites

- Ubuntu VM with **Docker** and **Docker Compose** installed
- Langflow running in Docker (with authentication enabled)
- Admin (superuser) account credentials for Langflow
- Python 3.8+ installed on the VM
- Internet access to install Python dependencies
- SSH access as user: ssh @

---

## 1️⃣ Verify Langflow is Running

Check your running containers:

```bash
docker ps
```

Example output:

```
CONTAINER ID   IMAGE                        COMMAND                  STATUS         PORTS
bb41390d9720   langflow_docker-langflow     "python -m langflow …"   Up 10 days
aac7058fb826   postgres:16                  "docker-entrypoint.s…"   Up 10 days
19a79058fe68   traefik:v2.11                "/entrypoint.sh ..."     Up 10 days     0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

If Langflow is behind **Traefik**, it will be accessible via your domain or server IP on port `80` or `443`.

---

## 2️⃣ Create `users.json`

This file contains the list of users you want to create.

```bash
nano users.json
```

Paste the following example:

```json
[
  {"username": "user01", "password": "User01", "is_superuser": false},
  {"username": "user02", "password": "User02", "is_superuser": false},
  {"username": "user03", "password": "User03", "is_superuser": false},
  {"username": "user04", "password": "User04", "is_superuser": false},
  {"username": "user05", "password": "User05", "is_superuser": false}
]
```
Make sure the last line is not followed by a comma.
Save and exit (`CTRL+O`, `ENTER`, `CTRL+X`).

---

## 3️⃣ Create `add_langflow_users.py`

```bash
nano add_langflow_users.py
```

Paste the following code:

```python
import requests
import json
import sys

# ===== CONFIGURATION =====
DOMAIN = "https://langflow.betekenisvolle.src.surf-hosted.nl"  # Change if needed
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "xxxxxxxxxxxx" # Id
USERS_FILE = "users.json"
VERIFY_SSL = True  # Set to False if using self-signed certs
# =========================

def get_access_token():
    """Login and return access token."""
    login_url = f"{DOMAIN}/api/v1/login"
    try:
        resp = requests.post(
            login_url,
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            verify=VERIFY_SSL
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise ValueError("No access token returned.")
        print("✅ Logged in successfully.")
        return token
    except requests.RequestException as e:
        print(f"❌ Network error during login: {e}")
        sys.exit(1)

def create_users(token):
    """Create users from JSON file."""
    try:
        with open(USERS_FILE, "r") as f:
            users_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Error reading {USERS_FILE}: {e}")
        sys.exit(1)

    api_base = f"{DOMAIN}/api/v1"
    for user in users_data:
        try:
            r = requests.post(
                f"{api_base}/users/",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=user,
                verify=VERIFY_SSL
            )
            if r.status_code == 201:
                print(f"✅ Created {user['username']}")
            elif r.status_code == 409:
                print(f"⚠️ {user['username']} already exists")
            else:
                print(f"❌ Failed to create {user['username']}: {r.status_code} {r.text}")
        except requests.RequestException as e:
            print(f"❌ Network error for {user['username']}: {e}")

if __name__ == "__main__":
    token = get_access_token()
    create_users(token)
```

Save and exit (CTRL+O, ENTER, CTRL+X).

---

## 4️⃣ Install Python Dependencies
#Pyhton Dependencies should already be installed. If so this step can be skipped.

```bash
pip install requests
```

---

## 5️⃣ Run the Script

```bash
python3 add_langflow_users.py
```

Expected output:

```
✅ Logged in successfully.
✅ Created user01
✅ Created user02
⚠️ user03 already exists
...
```

---

## 🔒 Security Notes

- Never commit your **admin password** to GitHub.
- Use environment variables or a `.env` file for credentials in production.
- Rotate admin passwords regularly.
- If using self-signed certificates, set `VERIFY_SSL = False` only for testing.

---

## ✅ Summary

You now have a working method to:
1. Create multiple users from a JSON file
2. Run everything from an Ubuntu VM with Langflow in Docker


---
---
---
---
---

## ADDENDUM: <br> Langflow on SRAM Docker <br> with Traefik and PostgreSQL

This setup deploys Langflow behind Traefik with PostgreSQL for persistence and optional direct access on port `7860`. It reflects the working configuration validated during troubleshooting, including the fix for the Langflow startup failure caused by using the legacy default superuser password. 


> Notes to resolve bad GATEWAY error
Implemented is the explicit 7860:7860 port mapping, the use of .env for MY_FQDN and secrets, and the warning not to use LANGFLOW_SUPERUSER_PASSWORD=langflow, because that exact value caused the boot failure in your logs. The final verified state in your session was a healthy Langflow startup with a successful 200 OK response from curl http://localhost:7860/

## Overview

The stack contains three services:

- `traefik` for HTTPS reverse proxy and certificate management.
- `langflow` for the application service.
- `db` for PostgreSQL 16 persistence.

In the validated deployment, Langflow started successfully, printed the welcome banner, and responded with `HTTP/1.1 200 OK` on `http://localhost:7860/`. 

## Resolved issues

During deployment, Langflow failed to boot because `LANGFLOW_SUPERUSER_PASSWORD` was set to the legacy default password (`langflow`), which Langflow rejects at startup. The crash manifested as repeated worker boot failures and `curl` returning `Recv failure: Connection reset by peer` on port `7860`. 

The issue was resolved by:

- Publishing port `7860:7860` for direct debugging access.
- Replacing the legacy default superuser password with a strong non-default password.
- Recreating the stack with the updated Compose file.

After that change, Langflow completed startup and served the UI successfully on port `7860`. 

## Directory structure

Suggested project structure:

```text
SRAM_DOCKER_LANGFLOW/
├── docker-compose.yaml
├── Dockerfile
├── .env
├── acme.json
├── chroma_data/
└── langflow_cache/
```

## Prerequisites

- Docker Engine with Compose plugin
- A reachable hostname for Traefik, stored as `MY_FQDN`
- Ports `80` and `443` open on the host
- A writable `acme.json` file for Traefik certificates

Create `acme.json` and secure it:

```bash
touch acme.json
chmod 600 acme.json
```

## Environment file

Create a `.env` file in the same directory as `docker-compose.yaml`:

```env
MY_FQDN=your-hostname.src.surf-hosted.nl
LANGFLOW_SUPERUSER=admin
LANGFLOW_SUPERUSER_PASSWORD=ReplaceThisWithALongRandomPassword_2026
LANGFLOW_SECRET_KEY=ReplaceThisTooWithALongRandomSecretKey_2026
```

Do not use `langflow` as the superuser password, because that exact legacy default value caused Langflow to abort during startup in the tested deployment. 

## Docker Compose

Use the following `docker-compose.yaml`:

```yaml
services:
  traefik:
    image: traefik:v2.11
    container_name: traefik
    dns:
      - 8.8.8.8
    restart: unless-stopped
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.web.http.redirections.entryPoint.to=websecure"
      - "--entrypoints.web.http.redirections.entryPoint.scheme=https"
      - "--certificatesresolvers.le.acme.httpchallenge=true"
      - "--certificatesresolvers.le.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./acme.json:/letsencrypt/acme.json"

  langflow:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: langflow
    restart: unless-stopped
    ports:
      - "7860:7860"
    environment:
      - LANGFLOW_DATABASE_URL=postgresql://langflow:langflow@db:5432/langflow
      - LANGFLOW_AUTO_LOGIN=false
      - LANGFLOW_SUPERUSER=${LANGFLOW_SUPERUSER}
      - LANGFLOW_SUPERUSER_PASSWORD=${LANGFLOW_SUPERUSER_PASSWORD}
      - LANGFLOW_SECRET_KEY=${LANGFLOW_SECRET_KEY}
      - LANGFLOW_NEW_USER_IS_ACTIVE=true
      - LANGFLOW_CACHE_DIR=/app/langflow/cache
      - DO_NOT_TRACK=true
    volumes:
      - langflow_data:/app/langflow
      - ./langflow_cache:/app/langflow/cache
      - ./chroma_data:/app/chroma_data
    user: "root"
    depends_on:
      db:
        condition: service_healthy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.langflow.rule=Host(`${MY_FQDN}`)"
      - "traefik.http.routers.langflow.entrypoints=websecure"
      - "traefik.http.routers.langflow.tls.certresolver=le"
      - "traefik.http.services.langflow.loadbalancer.server.port=7860"

  db:
    image: postgres:16
    container_name: langflow_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: langflow
      POSTGRES_USER: langflow
      POSTGRES_PASSWORD: langflow
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langflow"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  langflow_data:
  postgres_data:
```

## Dockerfile

If you are building locally, use a simple Dockerfile such as:

```dockerfile
FROM langflowai/langflow:latest
```

If your project already uses a custom Dockerfile, keep that file and only apply the Compose and environment changes described here.

## Deployment

Start the stack with:

```bash
docker compose down
docker compose up -d
```

Then follow the Langflow logs until startup completes:

```bash
docker logs -f langflow
```

A successful startup includes the Langflow welcome banner and the message indicating that Langflow is available at `http://localhost:7860`. 

## Verification

### Direct access

Test the application directly on the host:

```bash
curl -v http://localhost:7860/
```

In the validated run, this returned `HTTP/1.1 200 OK` and the Langflow HTML entry page. 

### Reverse proxy access

Test through Traefik:

```bash
curl -vk https://${MY_FQDN}/
```

If direct access works but the FQDN does not, inspect Traefik logs and the applied container labels:

```bash
docker logs traefik --tail 100
docker inspect langflow --format '{{json .Config.Labels}}'
```

## Troubleshooting

### 1. `Connection reset by peer` on `localhost:7860`

If `curl http://localhost:7860/` connects and then resets, Langflow is usually crashing during startup rather than failing at networking. In the resolved case, the root cause was the rejected legacy default superuser password. 

Check:

```bash
docker logs langflow --tail 200
```

Look for:

```text
ValueError: LANGFLOW_SUPERUSER_PASSWORD cannot use the legacy default password
```

Fix by changing `LANGFLOW_SUPERUSER_PASSWORD` to a strong non-default value and recreating the stack.

### 2. Langflow crash loop

Symptoms:

- `docker ps` shows `Up` only for a few seconds.
- `docker logs` ends with `Worker failed to boot`.
- `curl` to port `7860` resets or fails.

The confirmed startup blocker in this deployment was the legacy password policy for the superuser. 

### 3. Traefik route does not work

If `http://localhost:7860/` works but `https://${MY_FQDN}/` does not:

- Verify `MY_FQDN` is set in `.env`
- Confirm DNS points to the host
- Confirm Traefik labels are applied
- Check Traefik logs

Useful commands:

```bash
echo "$MY_FQDN"
docker inspect langflow --format '{{json .Config.Labels}}'
docker logs traefik --tail 100
```

### 4. CORS warnings

Langflow may warn that permissive CORS defaults are enabled. These warnings do not prevent startup, but you should set explicit origins in production. 

Example:

```yaml
environment:
  - LANGFLOW_CORS_ORIGINS=https://${MY_FQDN}
```

## Operational notes

- PostgreSQL 16 worked correctly in the validated deployment.
- Direct port publishing on `7860` is useful for debugging even when Traefik is the main entrypoint.
- Keep secrets out of version control by storing them in `.env` or another secret management mechanism.

## Quick start

```bash
touch acme.json
chmod 600 acme.json

cat > .env << 'EOF'
MY_FQDN=your-hostname.src.surf-hosted.nl
LANGFLOW_SUPERUSER=admin
LANGFLOW_SUPERUSER_PASSWORD=ReplaceThisWithALongRandomPassword_2026
LANGFLOW_SECRET_KEY=ReplaceThisTooWithALongRandomSecretKey_2026
EOF

docker compose down
docker compose up -d
docker logs -f langflow
curl -v http://localhost:7860/
```

Expected result:

- Langflow finishes startup cleanly.
- `curl http://localhost:7860/` returns `HTTP/1.1 200 OK`.
- The UI is reachable locally and, after Traefik and DNS are correct, via `https://${MY_FQDN}/`.
---
---
---
---
---