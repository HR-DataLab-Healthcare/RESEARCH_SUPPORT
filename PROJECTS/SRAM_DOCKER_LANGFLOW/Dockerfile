FROM langflowai/langflow:latest

USER root

# Install system dependencies for Docling
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0

# Install Langflow with Docling extra
RUN uv pip install 'langflow[docling]'


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





