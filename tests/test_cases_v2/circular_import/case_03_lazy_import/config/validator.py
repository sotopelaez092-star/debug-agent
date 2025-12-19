"""Configuration validator."""
from typing import Dict, List, Any
from config.settings import Settings


class ConfigValidator:
    """Validates configuration settings."""

    def __init__(self):
        self._settings = Settings()

    def validate(self) -> Dict[str, Any]:
        """Validate all configuration settings."""
        errors = []
        warnings = []

        # Validate database settings
        if not self._validate_database_settings():
            errors.append("Invalid database settings")

        # Validate optimization settings
        if not self._validate_optimization_settings():
            warnings.append("Suboptimal optimization settings")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _validate_database_settings(self) -> bool:
        """Validate database connection settings."""
        postgres_port = self._settings.get('postgres_port')
        redis_port = self._settings.get('redis_port')
        mongo_port = self._settings.get('mongo_port')

        return (
            isinstance(postgres_port, int) and
            isinstance(redis_port, int) and
            isinstance(mongo_port, int)
        )

    def _validate_optimization_settings(self) -> bool:
        """Validate optimization settings."""
        level = self._settings.get('optimization_level', 1)
        return 1 <= level <= 3

    def get_recommendations(self) -> List[str]:
        """Get configuration recommendations."""
        recommendations = []

        if self._settings.get('optimization_level', 1) < 2:
            recommendations.append("Consider increasing optimization_level to 2 or 3")

        max_conn = self._settings.get('max_connections', 10)
        if max_conn < 20:
            recommendations.append("Consider increasing max_connections for better performance")

        return recommendations
