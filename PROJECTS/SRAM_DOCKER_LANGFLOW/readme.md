# Langflow on SURF Research Cloud Ubuntu VM

This repository provides a complete setup for deploying Langflow, a visual framework for building LLM applications, on a SURF Research Cloud Ubuntu VM. Tech leads of DataLabs can use these files to enable secure HTTPS access via the VM's domain name (FQDN). The stack uses Docker Compose with Traefik for reverse proxy and automatic Let's Encrypt SSL, PostgreSQL for persistence, and a custom Dockerfile for Langflow with Docling support.[^1][^2][^3]

## Prerequisites

Deploy on a SURF Research Cloud Ubuntu 22.04+ VM with public IP, ports 80/443/8080 open in the firewall, and a DNS A-record for the FQDN (e.g., langflow.datalab.src.surf-hosted.nl).[^4][^1]

- Install Docker and Docker Compose: Follow official docs or SURF guides.
- SSH access as a non-root user.
- Python 3 for FQDN detection in setup script.
- No conflicting services like Nginx or Apache running.[^1][^4]


## Quick Start

1. Clone or copy files to VM home directory: `git clone <repo> && cd langflow-docker` (or use `get-files.sh` to fetch from source).[^5]
2. Run `./create-langflow.sh` – it handles setup automatically:
    - Stops/disables Nginx.
    - Creates/secures `acme.json`.
    - Detects FQDN (e.g., from `socket.getfqdn()`) and generates `.env` with `MYFQDN=your.detected.src.surf-hosted.nl`.
    - Adds user to docker group.
    - Builds and starts `docker compose up -d --build`.[^1]
3. Access https://your-fqdn.src.surf-hosted.nl – Traefik handles HTTPS redirect and certs.[^2][^1]

Langflow initializes with user signup enabled; create admin on first access.[^2]

## File Descriptions

- **docker-compose.yaml**: Orchestrates three services.[^2]
    - **traefik**: v2.11 reverse proxy on ports 80/443/8080. Enables dashboard, Docker provider, HTTP-to-HTTPS redirect, Let's Encrypt ACME HTTP challenge. Volumes: `/var/run/docker.sock`, `acme.json`. DNS: 8.8.8.8 for cert validation.
    - **langflow**: Built from local Dockerfile. Env vars from `.env` (e.g., `LANGFLOWDATABASE_URL=postgresql://langflow:langflow@langflowdb:5432/langflow`, `LANGFLOW_SECRET_KEY`, auto-login false, new user signup true). Volumes for data/cache/Chrome. Traefik labels route `Host(`\$MYFQDN`)` to port 7860. Depends on healthy DB.
    - **db**: PostgreSQL 16 with DB/user/pass `langflow`. Healthcheck: `pg_isready`. Persistent volume `postgresdata`.
- **Dockerfile**: Extends `langflowai/langflow:latest`, installs `libgl1 libglib2.0-0` and `langflow[docling]` via uv pip for document processing support.[^3]
- **create-langflow.sh**: Automated deployment script with error handling (`set -e`). Detects FQDN via Python (`socket.getfqdn()` transformed to valid domain), creates `.env`, manages permissions, executes `docker compose`. Uses `sg docker` for non-sudo runs.[^1]
- **get-files.sh**: Downloads specific path from GitHub repo (sparse-checkout `PROJECTS/SRAM/DOCKER/LANGFLOW`), cleans up for clean folder setup.[^5]


## Customization

Edit `docker-compose.yaml` Traefik label: `- traefik.http.routers.langflow.rule=Host(\`\${MYFQDN}\`)` or override `MYFQDN` in `.env`. Generate new `LANGFLOW_SECRET_KEY` (e.g., `openssl rand -hex 32`). For custom domains, update DNS before running script.[^2][^1]
Adjust volumes/paths as needed; restart with `docker compose up -d --force-recreate`.[^2]

## Troubleshooting

| Issue | Solution |
| :-- | :-- |
| Port 80 in use | Run script (stops Nginx) or `sudo systemctl stop apache2`.[^1][^4] |
| Docker permission denied | Script adds user to group; `newgrp docker` or relogin.[^1] |
| No HTTPS cert | Verify DNS A-record, ports open, Traefik logs: `docker compose logs traefik`.[^2][^4] |
| Flows not persisting | Check `langflowdata` volume, DB health.[^2] |
| FQDN wrong | Manually edit `.env` before compose.[^1] |

## Security Notes

- `acme.json` chmod 600 protects cert keys.[^1]
- HTTPS enforced; no direct Langflow exposure.
- Use strong secret key; enable auth on first login.
- Volumes persist data securely.[^2]


## Maintenance

- Update: `docker compose pull && docker compose up -d`.[^4]
- Logs: `docker compose logs -f langflow`.
- Backup: `docker compose down; tar czf backup.tar.gz langflowdata postgresdata acme.json`.
- SURF-specific: Monitor VM quotas; scale Postgres if needed.[^2]
<span style="display:none">[^6]</span>

<div align="center">⁂</div>

[^1]: create-langflow.sh

[^2]: docker-compose.yaml

[^3]: Dockerfile

[^4]: readme.md

[^5]: get-files.sh

[^6]: Creating-a-Docker-Compose-catalog-item-SURF-User-Knowledge-Base-SURF-User-Knowledge-Base.url

