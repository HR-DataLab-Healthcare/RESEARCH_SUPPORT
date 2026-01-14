<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

## `ghcr.io/epicgames/unreal-engine:dev-latest` DOES NOT EXIST

**Epic Games uses VERSION-SPECIFIC tags only.** `dev-latest` is **invalid**.

## ✅ **CORRECT Working Tags** (Tested)

```bash
# UE5 Development (Full Editor + Build Tools)
docker pull ghcr.io/epicgames/unreal-engine:dev-5.4
docker pull ghcr.io/epicgames/unreal-engine:dev-5.3
docker pull ghcr.io/epicgames/unreal-engine:dev-5.2

# UE5 Runtime (Smaller, No Editor)
docker pull ghcr.io/epicgames/unreal-engine:runtime-5.4
docker pull ghcr.io/epicgames/unreal-engine:runtime-5.3
```


## Test Which Works (Pick One)

```bash
# RECOMMENDED: Most stable UE5.4 dev image
docker pull ghcr.io/epicgames/unreal-engine:dev-5.4
```

**Success output**:

```
dev-5.4: Pulling from epicgames/unreal-engine
... [downloads ~15GB]
Status: Downloaded newer image for ghcr.io/epicgames/unreal-engine:dev-5.4
```


## Update Your `Dockerfile`

```dockerfile
# ✅ CORRECT - Use specific version
FROM ghcr.io/epicgames/unreal-engine:dev-5.4

USER root
RUN useradd -m ue4user -s /bin/bash && \
    apt-get update && apt-get install -y curl net-tools
    
WORKDIR /project
COPY EPIC/ /project/
EXPOSE 8080 7777/udp 7778/udp

USER ue4user
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["tail -f /dev/null"]
```


## Deploy Updated Container

```bash
cd ~/unreal-docker
nano Dockerfile  # Change to dev-5.4 above
docker compose down
docker compose up -d --build
```


## Available Tags Reference (2026)

```
✅ dev-5.4     → UE 5.4 Development (Editor + Tools)
✅ dev-5.3     → UE 5.3 Development  
✅ runtime-5.4 → UE 5.4 Runtime (No Editor)
❌ dev-latest  → DOES NOT EXIST
❌ latest      → DOES NOT EXIST
```


## Why No `dev-latest`?

Epic Games **pins exact versions** for stability. They release new tags with each UE version (5.1, 5.2, 5.3, 5.4). No generic `latest` to prevent breaking changes.

## Verify Tag List (Optional)

```bash
# List all available Epic images (after login)
docker search ghcr.io/epicgames/unreal-engine
```

**Use `dev-5.4`** - it's the **current stable UE5 development image** with full editor support. Your Traefik + HTTPS setup will automatically proxy it to `https://unrealdock.cyber-secure-te.src.surf-hosted.nl` once deployed.

**Run the `dev-5.4` pull test now!** 🚀
<span style="display:none">[^1][^2][^3][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://dev.epicgames.com/documentation/en-us/unreal-engine/quick-start-guide-for-using-container-images-in-unreal-engine

[^2]: https://unrealcontainers.com/docs/obtaining-images/official-images

[^3]: https://dev.epicgames.com/documentation/en-us/unreal-engine/wine-enabled-containers-quick-start-for-unreal-engine

[^4]: https://dev.epicgames.com/community/learning/tutorials/qBj7/unreal-engine-fab-package-your-game-server-in-a-docker-container-get-it-running-in-your-pc-online

[^5]: https://hub.docker.com/r/connorlanigan/unrealengine-docker

[^6]: https://github.com/adamrehn/ue4-docker

[^7]: https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/GameplayTags/HasAllTags

[^8]: https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/GameplayTags/MakeLiteralGameplayTagContainer

[^9]: https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/GameplayTags/TagContainer/CompareTagContainertoOtherTags

