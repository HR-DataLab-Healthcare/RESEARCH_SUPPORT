<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# GitHub Token for Epic Games Unreal Engine Docker Images - Complete Guide

## Why You Need It

Epic Games hosts **Unreal Engine Docker images** on **GitHub Container Registry (ghcr.io)**, not public Docker Hub. These images require **authentication** even though they're "public" because Epic restricts access to verified GitHub accounts.

```
❌ docker pull ghcr.io/epicgames/unreal-engine:dev-latest
→ 401 Unauthorized

✅ docker login ghcr.io → docker pull works!
```


## Step-by-Step (5 Minutes)

### 1. Create GitHub Personal Access Token (PAT)

```
1. Login to GitHub → https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "Unreal Docker" (or anything)
4. Expiration: 90 days (or "No expiration")
5. Scopes → Check ONLY: ☑️ read:packages
6. Click "Generate token"
7. **CRITICAL**: COPY THE TOKEN (you won't see it again!)
```

**Example Token**: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 2. Docker Login (Secure Method)

```bash
# METHOD 1: Secure (recommended) - Token via stdin
echo "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" | \
docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Expected output:
# Login Succeeded
```

```bash
# METHOD 2: Interactive (if Method 1 fails)
docker login ghcr.io -u YOUR_GITHUB_USERNAME
# Password: [paste your token, not GitHub password]
```


### 3. Test Authentication

```bash
docker pull ghcr.io/epicgames/unreal-engine:dev-latest
```

**Success**: Downloads ~15GB UE5 container
**Fail**: `401 Unauthorized` → Token wrong/missing `read:packages` scope

## Real-World Example

```
# Your GitHub: rvanderwil
# Your token:   ghp_ABC123def456GHI789jkl0MNO

rvanderwil@unreal-docker:~$ echo "ghp_ABC123def456GHI789jkl0MNO" | \
docker login ghcr.io -u rvanderwil --password-stdin
Login Succeeded

rvanderwil@unreal-docker:~$ docker pull ghcr.io/epicgames/unreal-engine:dev-latest
dev-latest: Pulling from epicgames/unreal-engine
... [downloads 15GB successfully]
Status: Downloaded newer image for ghcr.io/epicgames/unreal-engine:dev-latest
```


## Common Errors \& Fixes

| Error | Cause | Fix |
| :-- | :-- | :-- |
| `401 Unauthorized` | Wrong token/missing scope | Regenerate with `read:packages` |
| `Login Succeeded` but `401` on pull | Token expired | Generate new token |
| `docker: command not found` | Docker not installed | `sudo apt install docker.io` |
| `Permission denied` | Not in docker group | `sudo usermod -aG docker $USER` |

## Token Security Best Practices

```bash
# ✅ GOOD: Token via stdin (not visible in history)
echo $TOKEN | docker login ghcr.io -u $USER --password-stdin

# ✅ GOOD: Environment variable
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
echo $GITHUB_TOKEN | docker login ghcr.io -u $USER --password-stdin

# ❌ BAD: Direct password (visible in bash history)
docker login ghcr.io -u $USER -p ghp_xxxxxxxxxxxxxxxxxxxx
```


## Available Tags (After Login)

```
# Development (full editor + tools, ~15GB)
ghcr.io/epicgames/unreal-engine:dev-latest
ghcr.io/epicgames/unreal-engine:dev-5.4
ghcr.io/epicgames/unreal-engine:dev-5.3

# Runtime (smaller, no editor, ~8GB)
ghcr.io/epicgames/unreal-engine:runtime-5.4
ghcr.io/epicgames/unreal-engine:runtime-pixel-streaming
```


## Logout (When Done)

```bash
docker logout ghcr.io
```


## Pro Tips

- **Token expires?** Docker will show `401` → regenerate + relogin
- **Multiple machines?** Same token works everywhere
- **Team access?** Each developer needs their own token
- **CI/CD?** Store token as GitHub Secret: `GHCR_TOKEN`

```
🚀 After login → docker compose up -d --build
→ Unreal Engine 5 Editor behind HTTPS via Traefik!
```

**That's it!** Your `docker-compose.yml` will now pull the real UE5 container instead of nginx test image.
<span style="display:none">[^1][^10][^2][^3][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://dev.epicgames.com/documentation/en-us/unreal-engine/quick-start-guide-for-using-container-images-in-unreal-engine

[^2]: https://forums.unrealengine.com/t/i-cannot-gain-access-to-unreal-engine-source-code/2641668

[^3]: https://forums.unrealengine.com/t/epics-unreal-container-does-it-exist/250284/12

[^4]: https://colory-games.net/site/en/use-unreal-engine-container-images-with-docker-en/

[^5]: https://forums.unrealengine.com/t/unable-to-pull-ghcr-io-epicgames-pixel-streaming-signalling-server-4-27-2/271450

[^6]: https://ue4-docker.docs.adamrehn.com

[^7]: https://dev.epicgames.com/documentation/en-us/unreal-engine/horde-server-for-unreal-engine

[^8]: https://forums.unrealengine.com/t/how-to-run-unreal-engine-app-with-pixel-streaming-using-ghcr-io-epicgames-unreal-engine-runtime-pixel-streaming-in-docker/1934433

[^9]: https://forums.unrealengine.com/t/epics-unreal-container-does-it-exist/250284

[^10]: https://unrealcontainers.com/docs/obtaining-images/official-images

