"""
Cache key generation and management.
This module defines how cache keys are formatted.
"""


class CacheKeyGenerator:
    """Generates standardized cache keys."""

    # Version 2.0 key format (NEW)
    # Format: {prefix}:{resource_type}:{identifier}:{version}

    @staticmethod
    def user_profile_key(user_id: str) -> str:
        """Generate cache key for user profile (v2 format)."""
        return f"app:user:profile:{user_id}:v2"

    @staticmethod
    def user_settings_key(user_id: str) -> str:
        """Generate cache key for user settings (v2 format)."""
        return f"app:user:settings:{user_id}:v2"

    @staticmethod
    def session_key(session_id: str) -> str:
        """Generate cache key for session (v2 format)."""
        return f"app:session:data:{session_id}:v2"

    @staticmethod
    def api_response_key(endpoint: str, params_hash: str) -> str:
        """Generate cache key for API response (v2 format)."""
        return f"app:api:response:{endpoint}:{params_hash}:v2"

    @staticmethod
    def query_result_key(query_hash: str) -> str:
        """Generate cache key for query result (v2 format)."""
        return f"app:db:query:{query_hash}:v2"


# Old v1 format (for reference)
# Format was: {resource_type}_{identifier}
# Examples:
#   - user_profile_{user_id}
#   - user_settings_{user_id}
#   - session_{session_id}
#   - api_response_{endpoint}_{params_hash}
#   - query_result_{query_hash}
