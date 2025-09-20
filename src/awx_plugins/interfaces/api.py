"""Entry point module for interfacing with the AWX plugin interfaces."""

from .ctypes_go_bridge import (
    GoVaultBridge,
    GoVaultPlugin, 
    discover_vault_libraries,
)
from .vault import (
    VaultConfig,
    VaultPlugin,
    VaultPluginBase,
    VaultSecretRequest,
    VaultSecretResponse,
    VaultPluginError,
    VaultAuthenticationError,
    VaultConnectionError,
    VaultSecretNotFoundError,
)

__all__ = [
    # Vault plugin interfaces
    'VaultConfig',
    'VaultPlugin',
    'VaultPluginBase', 
    'VaultSecretRequest',
    'VaultSecretResponse',
    'VaultPluginError',
    'VaultAuthenticationError',
    'VaultConnectionError',
    'VaultSecretNotFoundError',
    
    # Ctypes Go bridge
    'GoVaultBridge',
    'GoVaultPlugin',
    'discover_vault_libraries',
]
