# Create Docker daemon override
sudo mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "min-api-version": "1.24"
}
EOF

# Restart Docker (this fixes Traefik)
sudo systemctl restart docker

# Restart your stack
cd ~/monitoring
sudo docker compose restart

# Watch Traefik connect
sudo docker compose logs -f traefik
