<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# MY PROMPT is Ubuntu VM USER:

rvanderwil@unrealdock-cyber-secure-te-src-surf-hosted-nl:~/unreal-docker\$

I am not inside the container
I do not KNOWE How to get inside the container!!

**YOU ARE ON YOUR UBUNTU HOST - NOT INSIDE CONTAINER!**

## **1 COMMAND TO GET INSIDE UE5 CONTAINER:**

```bash
docker compose exec unreal-editor bash
```

**That's it.** Run this **from your Ubuntu prompt** (`rvanderwil@unrealdock-cyber-secure-te-src-surf-hosted-nl:~/unreal-docker$`).

## **Expected Result:**

```
root@94ac848cff42:/project# 
```

**OR** (if it drops you as `ue4` user):

```
ue4@94ac848cff42:~$
```


## **Then run these 3 commands inside container:**

```bash
cd /home/ue4/UnrealEngine
mkdir -p /project/TestProject
./Engine/Binaries/Linux/UnrealEditor /project/TestProject -game -server -log -port=8080 -nullrhi -unattended
```


## **Complete Flow (Copy-Paste Each Line):**

```bash
# STEP 1: From Ubuntu host → Enter container
docker compose exec unreal-editor bash

# STEP 2: Inside container → Start UE5 (you'll see prompt change)
cd /home/ue4/UnrealEngine
mkdir -p /project/TestProject  
./Engine/Binaries/Linux/UnrealEditor /project/TestProject -game -server -log -port=8080 -nullrhi -unattended
```

**After STEP 2**: UE5 starts (60 seconds logs) → **LEAVE RUNNING** → test `https://unrealdock.cyber-secure-te.src.surf-hosted.nl`

## **Visual Flow:**

```
Ubuntu Host: rvanderwil@...$ → docker compose exec unreal-editor bash → 
Container:  root@94ac848cff42# → cd /home/ue4/UnrealEngine → ./UnrealEditor → 
UE5 Running → https://unrealdock... = UE5 Interface + Green Padlock ✅
```

**TYPE THIS NOW:**

```bash
docker compose exec unreal-editor bash
```

**Prompt changes = you're inside.** Then copy-paste the 3 UE5 commands. **90 seconds to UE5 HTTPS live!** 🎮
<span style="display:none">[^1][^10][^2][^3][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://www.baeldung.com/ops/docker-access-container-from-host-using-container-name

[^2]: https://dev.to/iamrj846/connecting-to-the-host-machines-localhost-from-a-docker-container-a-practical-guide-nc4

[^3]: https://stackoverflow.com/questions/37242217/access-docker-container-from-host-using-containers-name

[^4]: https://www.youtube.com/watch?v=OsuLjjJsg1A

[^5]: https://www.reddit.com/r/docker/comments/1ka8y1w/how_do_i_access_network_services_running_on_a/

[^6]: https://forums.docker.com/t/how-can-i-navigate-to-container-website-from-host-browser/25035

[^7]: https://blog.jetbrains.com/dotnet/2023/03/27/connecting-to-a-running-docker-container-shell/

[^8]: https://linuxize.com/post/how-to-connect-to-docker-container/

[^9]: https://forums.docker.com/t/accessing-host-machine-from-within-docker-container/14248

[^10]: https://www.reddit.com/r/docker/comments/swilid/is_it_possible_to_use_the_host_shell_from_inside/

