# Gatepass — Phase 1 Foundation

Production-oriented FastAPI foundation for the multi-tenant Gatepass SaaS.

## Included

- FastAPI + SQLAlchemy 2 async + MySQL
- Alembic migrations
- Redis client and health check
- JWT access + refresh authentication
- Login with either `email` **or** `username` + password
- Argon2 password hashing
- Organizations and memberships
- Roles and permissions
- Tenant context resolved from authenticated membership
- Mandatory `organization_id` on tenant-owned records
- Shared/dedicated database resolver abstraction
- Request ID and structured logging middleware
- Health/readiness endpoints
- Consistent API errors
- CORS configuration
- Unit/integration-ready test layout
- Docker Compose for local infrastructure

## Important tenancy rule

The client never supplies `organization_id` as an authority. The authenticated user selects a membership/organization context, and the backend validates that membership before creating `TenantContext`.

The same application services/repositories are intended to work against either a shared tenant database or a dedicated tenant database. Dedicated databases still contain `organization_id` on tenant-owned tables.

## Run locally

```bash
cp .env.example .env
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\\Scripts\\Activate.ps1
pip install -e '.[dev]'

alembic upgrade head
uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs
Health: http://localhost:8000/health
Readiness: http://localhost:8000/ready

## Docker

```bash
cp .env.example .env
# change PLATFORM_DATABASE_URL host from localhost to mysql
# PLATFORM_DATABASE_URL=mysql+aiomysql://gatepass:gatepass@mysql:3306/gatepass_platform

docker compose up --build
```

Run migrations inside the API container:

```bash
docker compose exec api alembic upgrade head
```

## API overview

- `POST /api/v1/auth/register` — create an initial organization and owner user
- `POST /api/v1/auth/login` — email/username + password
- `POST /api/v1/auth/refresh` — refresh access token
- `GET /api/v1/auth/me` — current authenticated user
- `GET /api/v1/organizations` — organizations accessible to current user
- `GET /api/v1/organizations/{organization_id}` — tenant-scoped organization
- `GET /api/v1/roles` — roles for current organization
- `GET /api/v1/permissions` — permissions for current organization context

## Phase 1 boundary

This phase establishes the platform/tenant foundation and access-control primitives. Visitors, visits, gatepasses, workflow engine, QR, scanner, movements, returnables, notifications, and platform billing/provisioning are deliberately left for later phases.

## Production hardening notes

- Set a unique high-entropy `SECRET_KEY`; never use the example value in production.
- Put dedicated tenant database credentials in a secrets manager and store only a `secret_ref` in platform data. The `connection_url` field exists for controlled bootstrap/development and should not contain long-lived plaintext credentials in production.
- Put the API behind TLS/reverse proxy and restrict CORS to real frontend origins.
- Use a separate MySQL user/database for the platform database.
- Back up MySQL and test restoration before onboarding real tenants.
- Run Alembic migrations as a deployment step, not automatically on every application startup.
- Add centralized logs/metrics/tracing and alert on `/ready` failures before production launch.
- Refresh tokens are stored hashed and rotated on refresh; revoking a refresh token does not expose its raw value in the database.
