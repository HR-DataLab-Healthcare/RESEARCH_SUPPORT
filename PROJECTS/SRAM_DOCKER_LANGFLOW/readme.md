# Langflow on SURF Research Cloud Ubuntu VM

This GitHub repository guides Tech Leads to deploy Langflow 
on SURF Research Cloud (SRC) Ubuntu VMs with secure HTTPS via DOMAIN name; 
using SURF Research Access Management (SRAM) as authorisation portal. <br>
It includes full Docker Compose  stack with Traefik reverse proxy/Let's Encrypt, 
PostgreSQL persistence, Docling support, and automation scripts. 
An example of a custom-made Langflow flow SURF AI-Hub (Willma) implementation is provided.
At the end of this readmefile a step-by-step DIY recipy is decribed.

<img width="1374" height="1132" alt="image" src="https://github.com/user-attachments/assets/09d75d1f-71c4-4529-bc38-de0aa995c01b" />

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
echo "PROJECTS/SRAM_DOCKER_LANGFLOW/" > .git/info/sparse-checkout
git pull origin main
mv PROJECTS/SRAM_DOCKER_LANGFLOW/* .
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

# Install ONLY docling - don't touch Langflow itself
RUN pip install --no-cache-dir "docling"

# Switch back to Langflow's default user
USER 1000
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
      - traefik.docker.network=langflow_default

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
ls -la create-langflow.sh  # Check current permissions
chmod +x create-langflow.sh
ls -la create-langflow.sh  # Should show -rwxr-xr-x
./create-langflow.sh       # Now works
sudo bash create-langflow.sh

# outcome:  installs ..............
​
```



# Bulk Create Users in Langflow (Docker + Ubuntu VM)

This guide explains step-by-step how to create multiple user accounts in a **Langflow** instance running in **Docker** on an **Ubuntu VM**.

---

## 📋 Prerequisites

- Ubuntu VM with **Docker** and **Docker Compose** installed
- Langflow running in Docker (with authentication enabled)
- Admin (superuser) account credentials for Langflow
- Python 3.8+ installed on the VM
- Internet access to install Python dependencies

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

## 2️⃣ Test API Access

Replace `<your-domain>` with your actual domain or IP:

```bash
curl -k https://<your-domain>/api/docs
```

If you see the Langflow API docs HTML, the API is reachable.

---

## 3️⃣ Get an Admin Access Token

Langflow’s API requires a **Bearer token** for user creation.

Run the following command, replacing `admin` and `yourpassword` with your superuser credentials:

```bash
curl -k -X POST "https://<your-domain>/api/v1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=yourpassword"
```

Example with your actual credentials:

```bash
curl -k -X POST "https://langflow.betekenisvolle.src.surf-hosted.nl/api/v1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=30108188-26c4-497f-b7e1-e8014a324a9d"
```

Expected output:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9....",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

Copy the `access_token` — you’ll need it in the script.

---

## 4️⃣ Create `users.json`

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

Save and exit (`CTRL+O`, `ENTER`, `CTRL+X`).

---

## 5️⃣ Create `add_langflow_users.py`

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

Save and exit.

---

## 6️⃣ Install Python Dependencies

```bash
pip install requests
```

---

## 7️⃣ Run the Script

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

- Never commit your **admin password** or **access token** to GitHub.
- Use environment variables or a `.env` file for credentials in production.
- Rotate admin passwords regularly.
- If using self-signed certificates, set `VERIFY_SSL = False` only for testing.

---

## ✅ Summary

You now have a working method to:
1. Log in to Langflow’s API
2. Retrieve an access token
3. Create multiple users from a JSON file
4. Run everything from an Ubuntu VM with Langflow in Docker















