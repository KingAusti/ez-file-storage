"""
Version management for the Data Storage Application
"""
import os
from datetime import datetime
from typing import Dict, Any

# Application version
VERSION = "1.1.0"

# Build information
BUILD_DATE = datetime.now().isoformat()
GIT_COMMIT = os.environ.get("GIT_COMMIT", "unknown")
GIT_BRANCH = os.environ.get("GIT_BRANCH", "unknown")

# Feature flags
FEATURES = {
    "search": True,
    "tags": True,
    "dark_mode": True,
    "audit_logging": True,
    "rate_limiting": True,
    "refresh_tokens": True,
    "password_reset": True,
    "structured_logging": True,
    "error_tracking": True,
    "health_monitoring": True,
    "database_backups": True,
    "ci_cd": True,
    "api_documentation": True,
}

# API version
API_VERSION = "v1"

def get_version_info() -> Dict[str, Any]:
    """Get comprehensive version information"""
    return {
        "version": VERSION,
        "api_version": API_VERSION,
        "build_date": BUILD_DATE,
        "git_commit": GIT_COMMIT,
        "git_branch": GIT_BRANCH,
        "features": FEATURES,
        "environment": os.environ.get("ENVIRONMENT", "development"),
    }

def get_health_version() -> Dict[str, str]:
    """Get minimal version info for health checks"""
    return {
        "version": VERSION,
        "api_version": API_VERSION,
        "build_date": BUILD_DATE,
    }
