import pytest

from app.tenant.context import TenantContext


def test_tenant_context_is_immutable():
    context = TenantContext(organization_id="org-1", storage_mode="shared")
    assert context.organization_id == "org-1"
    with pytest.raises(Exception):
        context.organization_id = "org-2"
