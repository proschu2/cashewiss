import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()  # Load .env file if present


def get_config():
    """Get configuration from environment variables."""
    server_url = os.getenv("ACTUAL_SERVER_URL")
    password = os.getenv("ACTUAL_PASSWORD")
    file = os.getenv("ACTUAL_FILE")
    encryption_password = os.getenv("ACTUAL_ENCRYPTION_PASSWORD")

    # Validate required
    if not server_url:
        raise ValueError("ACTUAL_SERVER_URL environment variable is required")
    if not password:
        raise ValueError("ACTUAL_PASSWORD environment variable is required")
    if not file:
        raise ValueError("ACTUAL_FILE environment variable is required")

    return {
        "server_url": server_url,
        "password": password,
        "file": file,
        "encryption_password": encryption_password,
    }
