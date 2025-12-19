"""
Main entry point for the application.
Sets environment to 'testing' which triggers the import error.
"""

import os
import sys

# Set environment to testing, which will trigger the conditional import error
os.environ['APP_ENV'] = 'testing'

# This import will fail because config.__init__.py tries to import
# from .test_config but the file is actually named testing_config.py
from app import create_app


def main():
    """Main function."""
    print("Starting application in testing mode...")
    app = create_app()

    if app.run():
        print("Application started successfully")
    else:
        print("Application failed to start")


if __name__ == "__main__":
    main()
