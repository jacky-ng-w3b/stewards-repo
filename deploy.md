# deploy

```bash
cd ~/stewards-back-api/ && git pull && npx tsx scripts/syncPermissionsFromCatalog.ts
cd ~/stewards-back-api/ && git pull && npx prisma migrate deploy
cd ~/stewards-dockercompose/ && docker compose pull && docker compose up -d --scale backapi=3
```

`backapi` is scaled to **3** instances. Traefik load-balances `api.$DOMAIN` across them.

- **Docker Compose (standalone):** use `--scale backapi=3` as above. The `deploy.replicas` field in `stewards-dockercompose/docker-compose.yaml` is not applied by standalone Compose; scaling is explicit on the CLI.
- **Docker Swarm (`docker stack deploy`):** `deploy.replicas: 3` on `backapi` is honored; align your stack workflow with that file.

**Scaling constraints**

- **`./uploads` bind mount:** All `backapi` replicas share the host `./uploads` directory. This fits a **single host** (or shared storage). Do not spread replicas across nodes without shared storage for `/app/uploads`, or `/uploads/` URLs may 404 on the wrong replica.
- **Do not scale cron workers** (`scheduled-notification-cron`, `scheduled-draw-cron`, `application-update-cron`): they run per-minute jobs; more than one replica risks duplicate work.

```bash
docker image prune
```
