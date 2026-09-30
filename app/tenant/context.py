from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    organization_id: str
    storage_mode: str
    database_url: str | None = None
