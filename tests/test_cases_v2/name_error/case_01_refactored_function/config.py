"""
Configuration settings for the ETL pipeline.
"""

import os
from typing import Dict, Any


class Config:
    """Configuration class for pipeline settings."""

    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///data.db')
        self.batch_size = int(os.getenv('BATCH_SIZE', '100'))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.enable_validation = os.getenv('ENABLE_VALIDATION', 'true').lower() == 'true'
        self.enable_transformation = os.getenv('ENABLE_TRANSFORMATION', 'true').lower() == 'true'

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'database_url': self.database_url,
            'batch_size': self.batch_size,
            'log_level': self.log_level,
            'enable_validation': self.enable_validation,
            'enable_transformation': self.enable_transformation,
        }

    def __repr__(self):
        return f"Config({self.to_dict()})"


def get_pipeline_config() -> Config:
    """Get the pipeline configuration."""
    return Config()


def setup_logging(config: Config):
    """Setup logging configuration."""
    import logging

    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
