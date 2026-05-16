
# develop

```bash

# migrate/develop
cd ~/stewards-repo/stewards-back-api && git checkout main && git pull && npx prisma migrate deploy

# prisma generate
cd ~/stewards-repo/stewards-back-api && git checkout main && git pull && npx prisma generate


cd ~/stewards-repo/stewards-front-admin-portal-vite && docker compose up -d
cd ~/stewards-repo/stewards-back-api && docker compose up -d 

# pull
cd ~/stewards-repo/react-datatable5 && git checkout main && git pull
cd ~/stewards-repo/stewards-back-api && git checkout main && git pull
cd ~/stewards-repo/stewards-front-admin-portal-vite  && git checkout main && git pull
cd ~/stewards-repo/stewards-front-mobile-user  && git checkout main && git pull
cd ~/stewards-repo/stewards-dockercompose  && git checkout main && git pull


# rebase
cd ~/stewards-repo/stewards-back-api && git checkout main && git rebase
cd ~/stewards-repo/stewards-front-admin-portal-vite && git checkout main && git rebase


# commit
cd ~/stewards-repo/stewards-back-api && git commit
cd ~/stewards-repo/stewards-front-admin-portal-vite && git commit
```

## Docker: admin portal + API

- Backend (creates `stewards-network`): `cd ~/stewards-repo/stewards-back-api && docker compose up -d`
- Frontend: `cd ~/stewards-repo/stewards-front-admin-portal-vite && docker compose up -d --build`
- If `package.json` / Vite config changes: `docker compose build front` in the frontend dir


```bash
npx tsx scripts/sendTopicFcmNotification.ts --title "Your title" --body "Your message" --topic broadcast_tmo --image-url "https://fastly.picsum.photos/id/236/200/200.jpg?hmac=BntZCNnsVBEqCPw_5q7AhpFIO2vQrHXcSLFR_C1i4fo"
```