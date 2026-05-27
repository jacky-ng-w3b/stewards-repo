# Runner Disk Cleanup (Linux + Docker)

Use this when a runner shows `/` near or at 100%.

## 1) Quick status check

```bash
df -h
docker system df
```

If `/` is full and `docker` is installed, start with Docker cleanup first.

## 2) Safe Docker cleanup

Removes only unused resources:

```bash
docker system prune -f
```

## 3) Aggressive Docker cleanup

Removes all unused images and unused volumes (may require re-pull/rebuild later):

```bash
docker system prune -a --volumes -f
```

## 4) Identify what still uses space

```bash
du -xh / --max-depth=1 2>/dev/null | sort -h
du -xh /var/lib/docker --max-depth=2 2>/dev/null | sort -h | tail -n 30
du -xh /var/lib/docker/containers --max-depth=2 2>/dev/null | sort -h | tail -n 30
```

Notes:
- `overlay ... /var/lib/docker/rootfs/overlayfs/...` entries in `df -h` are normal mount points for running containers.
- They are not separate extra disks; they reflect usage on the same root filesystem.

## 5) Clear oversized Docker container logs

If `*-json.log` files are very large:

```bash
find /var/lib/docker/containers -name "*-json.log" -exec truncate -s 0 {} \;
```

## 6) Clear system journal logs

```bash
journalctl --vacuum-time=3d
```

## 7) Verify result

```bash
df -h
docker system df
```

## Typical outcome

After cleanup, `/` dropping from `100%` to around `80%` (for example, with `~7.5G` free on a `38G` disk) is a normal successful recovery state for busy runners.


## Add start on restart

For the **runner service itself**, you’re already in good shape based on your output:

- `Loaded: ... enabled` => it **starts automatically on reboot**
- `Active: active (running)` => it’s currently healthy

If you want to verify runner behavior explicitly:

```bash
# boot-start enabled?
systemctl is-enabled actions.runner.chassis-app.github-runner-2.service

# auto-restart policy on failure?
systemctl show actions.runner.chassis-app.github-runner-2.service -p Restart -p RestartSec
```

If `Restart` is not `always`, set a systemd override:

```bash
sudo systemctl edit actions.runner.chassis-app.github-runner-2.service
```

Add:

```ini
[Service]
Restart=always
RestartSec=5
```

Then apply:

```bash
sudo systemctl daemon-reload
sudo systemctl restart actions.runner.chassis-app.github-runner-2.service
```

If you mean “run cleanup whenever runner service restarts (not only machine reboot)”, say the word and I’ll give you the exact unit wiring for that pattern too.