<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Datalab Guide: Mounting Research Drive (RD)

This guide provides technical instructions for mounting Research Drive (RD) directories on Windows 11 and Ubuntu VMs. This setup is optimized for handling datasets, SQL scripts, and Docker environments.

## 1. Prerequisites

- **Rclone Installed:** Ensure Rclone is installed on the local or VM environment.
- **Configured Remote:** A configured Rclone remote named `RD` pointing to the SURF WebDAV endpoint.
- **FUSE (Linux Only):** Install FUSE on Ubuntu with:

```bash
sudo apt install fuse3
```

- **WinFsp (Windows Only):** Required to use `rclone mount` on Windows.

***

## 2. Windows 11 Configuration (Background Service)

To provide a seamless experience where the drive mounts automatically without keeping a terminal window open:

### A. Install WinFsp

Before mounting, install WinFsp. Open an administrative Command Prompt or PowerShell and run:

```powershell
choco install winfsp -y
```

**Note:** After installing WinFsp, your mount command will work as expected. Always use a drive letter (e.g., `X:`) as the mount point on Windows, not a folder path.

### B. The Mounting Script

Create `C:\Scripts\mount_rd.bat`:

```batch
@echo off
rclone mount "RD:BACKUPS (Projectfolder)/DATASETS/" X: ^
--vfs-cache-mode full ^
--vfs-cache-max-age 24h ^
--network-mode ^
--links ^
--no-console
```


### C. Silent Execution

Create `C:\Scripts\mount_rd.vbs` to hide the command prompt:

```vbs
Set WinScriptHost = CreateObject("WScript.Shell")
WinScriptHost.Run Chr(34) & "C:\Scripts\mount_rd.bat" & Chr(34), 0
Set WinScriptHost = Nothing
```


### D. Persistence

Add a shortcut of the `.vbs` file to the Windows Startup folder (`shell:startup`).

***

## 3. Ubuntu VM Configuration (Systemd Service)

On Linux, we utilize systemd to manage the mount as a system service, ensuring it restarts on failure and clears stale endpoints.

### A. Create the Service File

Path: `/etc/systemd/system/rclone-mount.service`

```ini
[Unit]
Description=Rclone Research Drive Mount Service
After=network-online.target

[Service]
Type=simple
User=[your-username]
# Clears 'Transport endpoint is not connected' errors on start
ExecStartPre=-/usr/bin/fusermount -uz /home/[your-username]/MyCloudDrive
ExecStart=/usr/bin/rclone mount "RD:BACKUPS (Projectfolder)/DATASETS" /home/[your-username]/MyCloudDrive \
--config /home/[your-username]/.config/rclone/rclone.conf \
--vfs-cache-mode full \
--vfs-cache-max-age 24h
ExecStop=/bin/fusermount -u /home/[your-username]/MyCloudDrive
Restart=on-failure

[Install]
WantedBy=default.target
```


### B. Activation Commands

```bash
sudo systemctl daemon-reload
sudo systemctl enable rclone-mount.service
sudo systemctl start rclone-mount.service
```


***

## 4. Technical Notes \& Best Practices

| Feature | Recommendation |
| :-- | :-- |
| Cache Mode | Always use `--vfs-cache-mode full` for SQL/Notebook work to support random access. |
| Case Sensitivity | Windows is case-insensitive; Ubuntu is case-sensitive. Verify folder paths exactly. |
| Unmounting | On Linux, use `fusermount -u [path]`. Do not kill the process manually. |
| Docker | If using the mount for Docker volumes, ensure the VFS cache is enabled to prevent file-locking errors. |


***

This guide is designed for easy setup and robust operation of Research Drive mounts on both Windows and Ubuntu systems.[^1][^2][^3]

<div align="center">⁂</div>

[^1]: https://www.rapidseedbox.com/blog/rclone-mount

[^2]: https://ucr-research-computing.github.io/Knowledge_Base/how_to_mount_google_drive.html

[^3]: https://ostechnix.com/mount-google-drive-using-rclone-in-linux/

