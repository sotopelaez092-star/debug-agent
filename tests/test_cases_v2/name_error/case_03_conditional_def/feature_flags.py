"""
Feature flags and environment detection.
Controls which features are available at runtime.
"""

import os
import sys
from typing import Dict, Any


class FeatureFlags:
    """Manages feature flags for the application."""

    def __init__(self):
        self.flags = self._load_flags()

    def _load_flags(self) -> Dict[str, bool]:
        """Load feature flags from environment."""
        return {
            'enable_redis_cache': os.getenv('ENABLE_REDIS', 'false').lower() == 'true',
            'enable_async_tasks': os.getenv('ENABLE_ASYNC', 'false').lower() == 'true',
            'enable_metrics': os.getenv('ENABLE_METRICS', 'true').lower() == 'true',
            'enable_advanced_search': os.getenv('ENABLE_ADVANCED_SEARCH', 'false').lower() == 'true',
            'debug_mode': os.getenv('DEBUG', 'false').lower() == 'true',
        }

    def is_enabled(self, flag: str) -> bool:
        """Check if a feature flag is enabled."""
        return self.flags.get(flag, False)

    def __repr__(self):
        return f"FeatureFlags({self.flags})"


# Global instance
feature_flags = FeatureFlags()


def has_redis() -> bool:
    """Check if Redis is available."""
    return feature_flags.is_enabled('enable_redis_cache')


def has_async() -> bool:
    """Check if async features are available."""
    return feature_flags.is_enabled('enable_async_tasks')


def has_advanced_search() -> bool:
    """Check if advanced search is available."""
    return feature_flags.is_enabled('enable_advanced_search')


def is_production() -> bool:
    """Check if running in production environment."""
    return os.getenv('ENVIRONMENT', 'development') == 'production'


def is_development() -> bool:
    """Check if running in development environment."""
    return os.getenv('ENVIRONMENT', 'development') == 'development'
