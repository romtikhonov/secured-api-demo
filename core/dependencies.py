from infrastructure.vault_client import VaultSecretProvider

from core.secrets import SecretProvider


def get_secret_provider() -> SecretProvider:
    return VaultSecretProvider()
