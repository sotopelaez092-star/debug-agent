"""Test deep inheritance chain with multiple mixins and interfaces."""
from models import SuperAdmin


def main():
    # Create a super admin user
    admin = SuperAdmin(
        entity_id="sa-001",
        username="root",
        email="root@system.local"
    )

    # Test basic functionality
    print(f"Created: {admin.username}")
    print(f"Valid: {admin.is_valid()}")
    print(f"Cache key: {admin.cache_key()}")

    # Test audit logging
    admin.elevate_to_admin("user-123")
    admin.revoke_admin("user-456")

    # This triggers the bug - get_audit_trial() doesn't exist
    # Should be get_audit_trail()
    audit_log = admin.get_system_audit_log()
    print(f"Audit entries: {len(audit_log)}")

    # Serialize
    data = admin.to_dict()
    print(f"Serialized: {data}")


if __name__ == "__main__":
    main()
