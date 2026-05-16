#!/usr/bin/env python3
"""
Prepend intent-oriented module headers when a file lacks a substantive leading doc block.
Used to roll out documentation across stewards-back-api, admin portal, and mobile app.

Skips: node_modules, dist, build, generated trees, postgres_data, *.g.dart, *.freezed.dart.
Does not modify migration SQL or lockfiles.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SKIP_DIR_SUBSTR = (
    "node_modules",
    "dist",
    "build",
    ".git",
    "postgres_data",
    "keycloak-generated",
    "api-generated",
    ".react-router",
    "generated_api",
    ".dart_tool",
    "coverage",
)

ROUTE_PATH_RE = re.compile(
    r"server\.(?:get|post|put|patch|delete|head|options)\s*(?:<[^>]+>)?\s*\(\s*[`\"']([^`\"']+)[`\"']",
    re.MULTILINE,
)


def path_should_skip(p: Path) -> bool:
    s = str(p)
    return any(x in s for x in SKIP_DIR_SUBSTR)


def substantive_ts_leading_comment(text: str) -> bool:
    t = text.lstrip("\ufeff").lstrip()
    if not t.startswith("/**"):
        return False
    end = t.find("*/")
    if end == -1:
        return False
    inner = t[3:end]
    body = " ".join(
        ln.strip().lstrip("*").strip()
        for ln in inner.splitlines()
        if ln.strip().lstrip("*").strip()
    )
    return len(body) > 55


def substantive_dart_leading_comment(text: str) -> bool:
    t = text.lstrip("\ufeff").lstrip()
    if not t.startswith("///"):
        return False
    lines = t.splitlines()
    n = 0
    buf = []
    for line in lines[:25]:
        if line.startswith("///"):
            n += 1
            buf.append(line[3:].strip())
        elif n and line.strip() == "":
            continue
        elif n:
            break
    body = " ".join(buf)
    return len(body) > 55


def extract_route_paths(content: str) -> list[str]:
    found = ROUTE_PATH_RE.findall(content)
    out: list[str] = []
    for x in found:
        if x not in out:
            out.append(x)
    return out[:6]


def prepend_ts_header(path: Path, rel: str, kind: str) -> bool:
    if path_should_skip(path):
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    if substantive_ts_leading_comment(text):
        return False

    if kind == "route":
        paths = extract_route_paths(text)
        ptxt = ", ".join(f"`{p}`" for p in paths) if paths else "see registered handlers"
        hdr = (
            "/**\n"
            f" * HTTP route module — `{rel}`.\n"
            f" * Primary API path(s): {ptxt}.\n"
            " * Auth, validation, and response schemas are declared per route; "
            "request/response fields use snake_case per API convention.\n"
            " */\n\n"
        )
    elif kind == "service":
        hdr = (
            "/**\n"
            f" * Service layer — `{rel}`.\n"
            " * Encapsulates business logic and side effects (Prisma, queues, external APIs). "
            "Callers are typically routes or workers.\n"
            " */\n\n"
        )
    elif kind == "queue":
        hdr = (
            "/**\n"
            f" * Queue integration — `{rel}`.\n"
            " * Produces or consumes RabbitMQ messages; ensure idempotency where retries apply.\n"
            " */\n\n"
        )
    elif kind == "worker":
        hdr = (
            "/**\n"
            f" * Background worker — `{rel}`.\n"
            " * Standalone process (cron or consumer); see entrypoint for schedule and side effects.\n"
            " */\n\n"
        )
    elif kind == "admin_route":
        hdr = (
            "/**\n"
            f" * Admin portal route module — `{rel}`.\n"
            " * React Router UI; data via TanStack Query and generated API client where applicable. "
            "Align permissions with backend resource names.\n"
            " */\n\n"
        )
    elif kind == "admin_component":
        hdr = (
            "/**\n"
            f" * Admin portal UI component — `{rel}`.\n"
            " * Chakra UI + app conventions; keep i18n keys and permission checks consistent with routes.\n"
            " */\n\n"
        )
    elif kind == "admin_other":
        hdr = (
            "/**\n"
            f" * Admin portal module — `{rel}`.\n"
            " */\n\n"
        )
    else:
        hdr = (
            "/**\n"
            f" * `{rel}`\n"
            " */\n\n"
        )

    t2 = text.lstrip("\ufeff")
    if t2.startswith("/**"):
        end = t2.find("*/")
        if end != -1:
            inner = t2[3:end]
            thin = len(
                " ".join(
                    ln.strip().lstrip("*").strip()
                    for ln in inner.splitlines()
                    if ln.strip().lstrip("*").strip()
                )
            ) <= 55
            if thin:
                rest = t2[end + 2 :].lstrip("\n")
                path.write_text(hdr + rest, encoding="utf-8")
                return True
    path.write_text(hdr + text, encoding="utf-8")
    return True


def prepend_dart_header(path: Path, rel: str) -> bool:
    if path_should_skip(path):
        return False
    name = path.name
    if name.endswith(".g.dart") or name.endswith(".freezed.dart"):
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    if substantive_dart_leading_comment(text):
        return False
    hdr = (
        f"/// Module `{rel}` — see primary types and widgets below.\n"
        "/// Business rules and API contracts live in services/repos; keep snake_case aligned with OpenAPI.\n\n"
    )
    path.write_text(hdr + text, encoding="utf-8")
    return True


def prepend_prisma_file_comment(path: Path, rel: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    if text.lstrip().startswith("// Stewards Prisma schema"):
        return False
    hdr = (
        "// Stewards Prisma schema — database models and relations for the main API.\n"
        "// Use `///` on models/fields for docs surfaced in Prisma Studio and tooling.\n"
        "// Migrations under prisma/migrations are historical; edit schema here then migrate.\n\n"
    )
    path.write_text(hdr + text, encoding="utf-8")
    return True


def prepend_dockerfile_header(path: Path, rel: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    if text.lstrip().startswith("# Stewards container image"):
        return False
    hdr = (
        "# Stewards container image — see build stages and runtime CMD below.\n"
        f"# Path: `{rel}`\n\n"
    )
    path.write_text(hdr + text, encoding="utf-8")
    return True


def prepend_compose_header(path: Path, rel: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    if "Stewards **local dev**" in text[:400] or "Stewards **production-style stack**" in text[:400]:
        return False
    hdr = (
        "# Stewards **local / dev compose** — service wiring for this sub-project.\n"
        f"# File: `{rel}`. See CLAUDE.md for ports and network (`stewards-network`).\n\n"
    )
    path.write_text(hdr + text, encoding="utf-8")
    return True


def prepend_yaml_logrotate(path: Path, rel: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    if text.lstrip().startswith("# Logrotate"):
        return False
    hdr = f"# Logrotate config — `{rel}`\n\n"
    path.write_text(hdr + text, encoding="utf-8")
    return True


def walk_ts(
    base: Path,
    rel_root: Path,
    kind: str,
    *,
    extra_skip: tuple[str, ...] = (),
) -> int:
    n = 0
    if not base.is_dir():
        return 0
    for p in sorted(base.rglob("*.ts")):
        if any(x in str(p) for x in extra_skip):
            continue
        rel = p.relative_to(rel_root).as_posix()
        if prepend_ts_header(p, rel, kind):
            n += 1
    for p in sorted(base.rglob("*.tsx")):
        if any(x in str(p) for x in extra_skip):
            continue
        rel = p.relative_to(rel_root).as_posix()
        if prepend_ts_header(p, rel, kind):
            n += 1
    return n


def main() -> None:
    total = 0
    api = REPO / "stewards-back-api"
    portal = REPO / "stewards-front-admin-portal-vite"
    mobile = REPO / "stewards-front-mobile-user"
    dc = REPO / "stewards-dockercompose"

    # Phase 1a: API routes
    n = walk_ts(api / "src" / "routes", api, "route")
    print("api routes:", n)
    total += n

    # Phase 1b: services + queues
    n = walk_ts(api / "src" / "services", api, "service")
    print("api services:", n)
    total += n
    n = walk_ts(api / "src" / "queues", api, "queue")
    print("api queues:", n)
    total += n

    # Phase 1c: workers
    n = walk_ts(api / "workers", api, "worker", extra_skip=("node_modules",))
    print("api workers:", n)
    total += n

    # Phase 1d: plugins, utils, constants, types, database, assets, jasper, schema (ts), index, healthcheck
    for sub, k in (
        ("src/plugins", "admin_other"),
        ("src/utils", "admin_other"),
        ("src/constants", "admin_other"),
        ("src/types", "admin_other"),
        ("src/database", "admin_other"),
        ("src/assets", "admin_other"),
        ("src/jasper", "admin_other"),
        ("src/schema", "admin_other"),
    ):
        n = walk_ts(api / sub, api, k)
        print(sub, n)
        total += n
    for name in ("index.ts", "healthcheck.ts"):
        p = api / "src" / name
        if p.is_file() and prepend_ts_header(p, f"src/{name}", "admin_other"):
            total += 1
            print(name, 1)

    schema = api / "prisma" / "schema.prisma"
    if schema.is_file() and prepend_prisma_file_comment(schema, "prisma/schema.prisma"):
        total += 1
        print("prisma schema", 1)

    # Phase 2: admin portal
    n = walk_ts(portal / "app" / "routes", portal, "admin_route")
    print("portal routes:", n)
    total += n
    n = walk_ts(portal / "app" / "components", portal, "admin_component")
    print("portal components:", n)
    total += n
    for sub in (
        "app/api",
        "app/hooks",
        "app/contexts",
        "app/providers",
        "app/layout",
        "app/utils",
        "app/constants",
    ):
        n = walk_ts(portal / sub, portal, "admin_other")
        print(sub, n)
        total += n
    for name in (
        "root.tsx",
        "routes.ts",
        "entry.client.tsx",
        "entry.client.lazy.tsx",
        "oidc.client.ts",
    ):
        p = portal / "app" / name
        if p.is_file() and prepend_ts_header(p, f"app/{name}", "admin_other"):
            total += 1

    # Phase 3: mobile lib
    n = 0
    lib = mobile / "lib"
    if lib.is_dir():
        for p in sorted(lib.rglob("*.dart")):
            if "generated_api" in str(p) or "/l10n/" in str(p).replace("\\", "/"):
                continue
            rel = p.relative_to(mobile).as_posix()
            if prepend_dart_header(p, rel):
                n += 1
    print("mobile dart:", n)
    total += n

    # ARB sources
    l10n = mobile / "lib" / "l10n"
    if l10n.is_dir():
        na = 0
        for p in sorted(l10n.glob("*.arb")):
            try:
                t = p.read_text(encoding="utf-8")
            except OSError:
                continue
            if t.lstrip().startswith("{"):
                # one-line intent in @@locale if present — add top JSON comment not valid in JSON
                # ARB is JSON — skip or use "_comment" key; skip bulk ARB mutation
                pass
        print("arb skipped (JSON)")

    # Phase 4 dockercompose logrotate
    lr = dc / "logrotate"
    if lr.is_dir():
        n = 0
        for p in lr.rglob("*"):
            if p.is_file() and p.suffix in (".conf", "") and not p.name.startswith("."):
                if prepend_yaml_logrotate(p, p.relative_to(REPO).as_posix()):
                    n += 1
        print("logrotate:", n)
        total += n

    # Phase 5: Dockerfiles and compose in subprojects
    for proj_name, proj in (
        ("stewards-back-api", api),
        ("stewards-front-admin-portal-vite", portal),
        ("stewards-front-mobile-user", mobile),
    ):
        n = 0
        for p in sorted(proj.rglob("Dockerfile*")):
            if "node_modules" in str(p):
                continue
            if prepend_dockerfile_header(p, p.relative_to(REPO).as_posix()):
                n += 1
        for p in sorted(proj.glob("docker-compose*.yml")) + sorted(proj.glob("docker-compose*.yaml")):
            if prepend_compose_header(p, p.relative_to(REPO).as_posix()):
                n += 1
        print(f"docker {proj_name}:", n)
        total += n

    print("TOTAL FILES UPDATED:", total)


if __name__ == "__main__":
    main()
