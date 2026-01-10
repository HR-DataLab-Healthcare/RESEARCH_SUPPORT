#!/bin/bash

# Exit on any error to prevent partial setups
set -e

echo "-------------------------------------------------------"
echo "🛠️ Starting Deployment Script: $(date)"
echo "-------------------------------------------------------"

# 1. Handle Nginx
echo "Step 1: Stopping and disabling Nginx..."
if systemctl is-active --quiet nginx; then
    sudo systemctl stop nginx
    sudo systemctl disable nginx
    echo "✅ Nginx has been stopped and disabled."
else
    echo "ℹ️ Nginx was not running; skipping."
fi

# 2. Setup Traefik SSL storage
echo "Step 2: Configuring Traefik SSL storage (acme.json)..."
if [ ! -f acme.json ]; then
    sudo touch acme.json
    sudo chmod 600 acme.json
    echo "✅ acme.json created with secure permissions (600)."
else
    sudo chmod 600 acme.json
    echo "✅ acme.json already exists; permissions reset to 600."
fi

# 3. Docker Permissions
echo "Step 3: Checking Docker group membership for $USER..."
if groups "$USER" | grep &>/dev/null "\bdocker\b"; then
    echo "✅ User $USER is already in the docker group."
else
    sudo usermod -aG docker "$USER"
    echo "✅ User $USER added to the docker group."
fi

# 4. Docker Compose Execution
echo "Step 4: Building and starting containers with Traefik..."
# We use 'sg' to ensure the 'docker' group permission is recognized 
# in the current shell session without needing a logout/login.
if sg docker -c "docker compose up -d --build"; then
    echo "-------------------------------------------------------"
    echo "🚀 SUCCESS: Containers are building/starting."
else
    echo "❌ ERROR: Docker compose failed to start."
    exit 1
fi

echo "Step 5: Finalizing..."
# Optional: List running containers to verify
sg docker -c "docker ps"

echo "-------------------------------------------------------"
echo "✨ SETUP COMPLETE!"
echo "Traefik should now be handling traffic on ports 80/443."
echo "-------------------------------------------------------"