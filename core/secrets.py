import os
from urllib.parse import quote_plus

import hvac

from core.config import settings


class VaultInitializationError(Exception):
    """Raised when Vault cannot be initialized or authenticated."""

    pass


class SecretNotFoundError(Exception):
    """Raised when a required secret is not found in Vault."""

    pass


class SecretManager:
    def __init__(self):
        self.vault_client = hvac.Client(url=settings.vault.addr)

        jwt_path = settings.vault.jwt_token_path
        if not os.path.exists(jwt_path):
            raise VaultInitializationError("Not running in Kubernetes: service account token not found")

        try:
            with open(jwt_path) as f:
                jwt_token = f.read().strip()
            if not jwt_token:
                raise VaultInitializationError("Service account token is empty")
        except Exception as e:
            raise VaultInitializationError(f"Failed to read service account token: {e}")

        role = settings.vault.k8s_role
        try:
            self.vault_client.auth.kubernetes.login(role=role, jwt=jwt_token)
        except Exception as e:
            raise VaultInitializationError(f"Kubernetes auth failed for role '{role}': {e}")

        if not self.vault_client.is_authenticated():
            raise VaultInitializationError("Vault authentication succeeded but client is not authenticated")

    def get_db_password(self) -> str:
        try:
            response = self.vault_client.secrets.kv.v2.read_secret_version(mount_point="secret", path="db/creds")
            password = response["data"]["data"].get("password")
            if not password:
                raise SecretNotFoundError("Key 'password' not found in secret 'db/creds'")
            return quote_plus(str(password))
        except Exception as e:
            raise SecretNotFoundError(f"Failed to retrieve DB password: {e}")

    def get_auth_secret_key(self) -> str:
        try:
            response = self.vault_client.secrets.kv.v2.read_secret_version(mount_point="secret", path="auth/jwt")
            secret_key = response["data"]["data"].get("secret_key")
            if not secret_key:
                raise SecretNotFoundError("Key 'secret_key' not found in secret 'auth/jwt'")
            return str(secret_key)
        except Exception as e:
            raise SecretNotFoundError(f"Failed to retrieve JWT secret: {e}")

    def get_redis_password(self) -> str:
        try:
            response = self.vault_client.secrets.kv.v2.read_secret_version(mount_point="secret", path="redis/creds")
            password = response["data"]["data"].get("password")
            if not password:
                raise SecretNotFoundError("Key 'password' not found in secret 'redis/creds'")
            return str(password)
        except Exception as e:
            raise SecretNotFoundError(f"Failed to retrieve Redis password: {e}")


secret_manager = SecretManager()
