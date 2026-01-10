



====================================================================================================================
mkdir LANGFLOW
cd LANGFLOW

whoami
echo "$PUBLIC_IP"

scp -r "E:\github\RESEARCH_SUPPORT\PROJECTS\SRAM_DOCKER_LANGFLOW\*" rvanderwil@145.38.192.134:~/LANGFLOW/


cd ~/LANGFLOW
sudo systemctl stop nginx
sudo systemctl disable nginx
sudo touch acme.json
sudo chmod 600 acme.json
sudo usermod -aG docker $(whoami)
newgrp docker 
docker compose up -d build

====================================================================================================================




=====>
nano setup_langflow.sh

sudo chmod +x setup_langflow.sh
./setup_langflow.sh



#!/bin/bash

# Navigate to the project directory
cd ~/LANGFLOW || { echo "Directory ~/LANGFLOW not found"; exit 1; }

# Stop and disable Nginx to free up ports 80/443 for Traefik
echo "Stopping Nginx..."
sudo systemctl stop nginx
sudo systemctl disable nginx

# Setup Traefik SSL storage file
echo "Configuring acme.json..."
sudo touch acme.json
sudo chmod 600 acme.json

# Add current user to Docker group
echo "Adding $USER to docker group..."
sudo usermod -aG docker "$USER"

# Run docker compose
# Note: We use 'sg' to run the command as the docker group 
# because 'newgrp' would stop the script execution.
echo "Building and starting containers..."
sg docker -c "docker compose up -d --build"

echo "Setup complete!"




