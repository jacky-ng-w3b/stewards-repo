# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This is a monorepo for the Stewards (香港神託會) system — an event management, membership, and social services platform. It contains five sub-projects:

| Directory | Description | Tech Stack |
|---|---|---|
| `stewards-back-api/` | Main API server | Fastify v5, Prisma v7, PostgreSQL, RabbitMQ, MinIO |
| `stewards-front-admin-portal-vite/` | Admin portal SPA | React Router v7, Chakra UI v3, TanStack Query, Vite |
| `stewards-front-mobile-user/` | Flutter member app (iOS + Android) | Flutter 3.38.5 (FVM), Riverpod, Firebase, OpenAPI-generated client |
| `stewards-auth/` | Authentication/translation service | Fastify v4, Prisma v5, PostgreSQL, Keycloak |
| `stewards-dockercompose/` | Production docker-compose orchestration | Traefik, Watchtower |

Each sub-project has its own `package.json`, `docker-compose.yml`, and (where applicable) its own `CLAUDE.md` with detailed project-specific guidance. **Always read the sub-project's CLAUDE.md before working in it.**

## Development Commands

### Backend API (`stewards-back-api/`)
```bash
docker compose up -d          # Start dev environment (PostgreSQL, RabbitMQ, MinIO, API)
# Do NOT use `npm run dev` directly — the API runs inside Docker
npm run test                  # Run all tests (Vitest)
npm run test -- path/to/file  # Run a single test file
npm run lint                  # ESLint
npm run format                # Prettier
npx prisma migrate dev        # Create/apply migrations
npx prisma generate           # Regenerate Prisma client
npx prisma studio             # Database GUI
```

### Frontend Admin Portal (`stewards-front-admin-portal-vite/`)
```bash
docker compose up -d          # Start dev server on port 4123 (connects to stewards-network)
npm run dev                   # Or run locally outside Docker
npm run build                 # Production build
npm run typecheck             # TypeScript check (only run when explicitly asked)
npm run types                 # Regenerate API types from OpenAPI spec → types/api.d.ts
npm run generate:api-wrappers # Generate API wrapper functions
```

### Auth Service (`stewards-auth/`)
```bash
npm run dev                   # Dev server with tsx watch
npm run build                 # TypeScript compilation
npx prisma migrate dev        # Database migrations
```

### Mobile App (`stewards-front-mobile-user/`) — WSL tooling

```bash
# One-time WSL bootstrap (Dart/Flutter via FVM)
curl -fsSL https://fvm.app/install.sh | bash
echo 'export PATH="$PATH:$HOME/.pub-cache/bin:$HOME/fvm/default/bin"' >> ~/.bashrc
source ~/.bashrc

# Install the pinned SDK (reads .fvmrc -> Flutter 3.38.5, Dart ^3.8.0)
cd ~/stewards-repo/stewards-front-mobile-user
fvm install
fvm use 3.38.5

# Day-to-day
fvm flutter pub get
fvm flutter analyze              # run before considering a task done
fvm dart run build_runner build  # *.g.dart codegen
fvm flutter gen-l10n             # ARB -> Dart localizations
bash tools/update_openapi.sh     # regenerate lib/generated_api/* after API changes
```

- Always use `fvm flutter` / `fvm dart` (never bare `flutter`/`dart`) so the pinned 3.38.5 toolchain is used.
- Android SDK / signing / device deployment is intentionally out of scope here — handle those on a host with Android Studio. The above is enough for `analyze`, codegen, and tests.
- To build artifacts (`fvm flutter build aab`) you still need an Android SDK + JDK 17+; this WSL already has JDK 21 at `/usr/local/jdk-21.0.2` but no Android SDK by default.

## System Architecture

The services share a Docker network (`stewards-network`). Key ports:
- **8081**: Backend API
- **4123**: Frontend admin portal
- **5432**: PostgreSQL
- **5672/15672**: RabbitMQ
- **9000/9001**: MinIO (API/Console)

### Background Workers (in `stewards-back-api/workers/`)
Standalone Node processes consuming RabbitMQ queues or running cron jobs:
- `notification-consumer` — unified queue consumer for mobile, activity update, and application update notifications
- `scheduled-notification-cron` / `scheduled-draw-cron` / `application-update-cron` — cron jobs

## Centre Codes
- **tmo** = Ma On Shan Centre
- **tko** = Tseung Kwan O Centre
- **tac** = Sha Tin Centre

## Cross-Project Conventions

- Always use `dayjshk` for date handling (locale-safe)
- Always use snake_case for API params, query, and body variable names
- No backward compatibility unless explicitly requested
- Always use `getName` from `app/utils/getName.ts` (frontend) to format Chinese/English names
- Always add zh-HK translations for any new hardcoded strings
- Use `/api/permissions` to fetch the complete system permission list, and keep frontend permission vocabulary/mappings aligned with this endpoint response
- When a resource’s valid **namespace** or **status** values change in the backend, update **`permission_resource_catalog`** (and any related seed/migrations) in the same change, and keep **permission assignment UIs** and **permissions list/filter** surfaces in the admin portal aligned with the catalog (`/api/me/permissions/catalog`).
- **Admin portal API errors:** use the centralized translated error toast (`showApiErrorToast` / `toApiError`, global React Query mutation handler). Do not add a second user-facing error toast in `useMutation`’s `onError` unless the product explicitly needs a different UX; if you must handle errors locally, set `meta: { suppressGlobalErrorToast: true }` on that mutation. Add new backend `error_code` strings to `public/locales/zh-HK/errors.json` (and `en-US` when maintained).
