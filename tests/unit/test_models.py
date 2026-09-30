from app.models import Base, DatabaseConnection, Organization, Role, TenantConfiguration


def test_phase1_relationships_are_defined():
    assert Organization.__mapper__.relationships["roles"].back_populates == "organization"
    assert Organization.__mapper__.relationships["database_connection"].back_populates == "organization"
    assert Organization.__mapper__.relationships["tenant_configuration"].back_populates == "organization"
    assert Role.__mapper__.relationships["organization"].back_populates == "roles"
    assert DatabaseConnection.__mapper__.relationships["organization"].back_populates == "database_connection"
    assert TenantConfiguration.__mapper__.relationships["organization"].back_populates == "tenant_configuration"


def test_phase1_foreign_keys_exist():
    database_connection = Base.metadata.tables["database_connections"]
    organizations = Base.metadata.tables["organizations"]
    foreign_keys = {
        (fk.parent.name, fk.column.table.name, fk.column.name)
        for fk in database_connection.foreign_keys
    }
    assert ("organization_id", organizations.name, "id") in foreign_keys
