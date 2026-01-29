"""Authentication utilities."""

import os
from typing import Any

import keyring
from keyring.errors import KeyringError


class AuthError(Exception):
    """Authentication error."""

    pass


def get_service_name(source: str) -> str:
    """Get the keyring service name for a source."""
    return f"mldata-{source}"


def get_credentials(source: str) -> dict[str, str] | None:
    """Get credentials for a source.

    Priority:
    1. Environment variables
    2. Keyring
    """
    # Environment variables first
    env_vars = {
        "huggingface": "HUGGINGFACE_TOKEN",
        "kaggle": ("KAGGLE_USERNAME", "KAGGLE_KEY"),
        "openml": "OPENML_API_KEY",
    }

    if source in env_vars:
        env_keys = env_vars[source]
        if isinstance(env_keys, tuple):
            creds = {}
            for key in env_keys:
                val = os.environ.get(key)
                if val:
                    creds[key.lower()] = val
            return creds if creds else None
        else:
            token = os.environ.get(env_keys)
            return {"token": token} if token else None

    # Fall back to keyring
    service = get_service_name(source)
    try:
        creds = keyring.get_credential(service, None)
        if creds:
            return {"username": creds.username, "password": creds.password}
    except KeyringError:
        pass

    return None


def save_credentials(source: str, **credentials: str) -> None:
    """Save credentials for a source to keyring."""
    service = get_service_name(source)

    if "token" in credentials:
        keyring.set_password(service, "token", credentials["token"])
    elif "username" in credentials and "password" in credentials:
        keyring.set_password(service, credentials["username"], credentials["password"])
    else:
        raise AuthError(f"Invalid credentials for source: {source}")


def clear_credentials(source: str) -> None:
    """Clear credentials for a source."""
    service = get_service_name(source)
    try:
        keyring.delete_password(service, "token")
    except KeyringError:
        pass
    try:
        # Also try to delete any stored username/password
        keyring.delete_password(service, "default")
    except KeyringError:
        pass


def check_credentials(source: str) -> bool:
    """Check if credentials are configured for a source."""
    creds = get_credentials(source)
    return creds is not None and any(v for v in creds.values())
