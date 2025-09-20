"""HashiCorp Vault plugin interfaces for AWX.

This module provides interfaces for integrating HashiCorp Vault secret plugins
with AWX using ctypes to call Go shared libraries directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union


@dataclass(frozen=True)
class VaultSecretRequest:
    """Request structure for retrieving secrets from Vault."""

    path: str
    """The Vault path to the secret."""

    mount_point: Optional[str] = None
    """The mount point for the secrets engine."""

    version: Optional[int] = None
    """The version of the secret to retrieve (for versioned KV)."""

    metadata: Optional[Dict[str, Any]] = None
    """Additional metadata for the request."""


@dataclass(frozen=True)
class VaultSecretResponse:
    """Response structure containing retrieved secrets from Vault."""

    data: Dict[str, Any]
    """The secret data retrieved from Vault."""

    metadata: Optional[Dict[str, Any]] = None
    """Metadata about the secret (version, timestamps, etc.)."""

    warnings: Optional[List[str]] = None
    """Any warnings returned by Vault."""


@dataclass(frozen=True)
class VaultConfig:
    """Configuration for Vault connection and authentication."""

    url: str
    """The Vault server URL."""

    auth_method: str
    """Authentication method (token, userpass, aws, etc.)."""

    auth_config: Dict[str, Any]
    """Configuration specific to the auth method."""

    namespace: Optional[str] = None
    """Vault namespace (Enterprise feature)."""

    ca_cert_path: Optional[Path] = None
    """Path to CA certificate for TLS verification."""

    client_cert_path: Optional[Path] = None
    """Path to client certificate for mTLS."""

    client_key_path: Optional[Path] = None
    """Path to client private key for mTLS."""

    verify_tls: bool = True
    """Whether to verify TLS certificates."""

    timeout: int = 30
    """Connection timeout in seconds."""


class VaultPluginError(Exception):
    """Base exception for Vault plugin errors."""

    pass


class VaultAuthenticationError(VaultPluginError):
    """Exception raised when Vault authentication fails."""

    pass


class VaultConnectionError(VaultPluginError):
    """Exception raised when connection to Vault fails."""

    pass


class VaultSecretNotFoundError(VaultPluginError):
    """Exception raised when requested secret is not found."""

    pass


class VaultPlugin(Protocol):
    """Protocol defining the interface for Vault plugins."""

    def authenticate(self, config: VaultConfig) -> bool:
        """Authenticate with Vault using the provided configuration.
        
        Args:
            config: Vault configuration including auth details
            
        Returns:
            True if authentication successful, False otherwise
            
        Raises:
            VaultAuthenticationError: If authentication fails
            VaultConnectionError: If connection to Vault fails
        """
        ...

    def get_secret(self, request: VaultSecretRequest) -> VaultSecretResponse:
        """Retrieve a secret from Vault.
        
        Args:
            request: Details about the secret to retrieve
            
        Returns:
            VaultSecretResponse containing the secret data
            
        Raises:
            VaultSecretNotFoundError: If secret is not found
            VaultAuthenticationError: If not authenticated
            VaultConnectionError: If connection fails
        """
        ...

    def list_secrets(self, path: str, mount_point: Optional[str] = None) -> List[str]:
        """List secrets at the given path.
        
        Args:
            path: Vault path to list
            mount_point: Optional mount point
            
        Returns:
            List of secret names/paths
            
        Raises:
            VaultAuthenticationError: If not authenticated
            VaultConnectionError: If connection fails
        """
        ...

    def close(self) -> None:
        """Clean up resources and close connections."""
        ...


class VaultPluginBase(ABC):
    """Abstract base class for Vault plugins."""

    def __init__(self, config: VaultConfig) -> None:
        """Initialize the Vault plugin with configuration.
        
        Args:
            config: Vault configuration
        """
        self.config = config
        self._authenticated = False

    @property
    def is_authenticated(self) -> bool:
        """Check if the plugin is authenticated with Vault."""
        return self._authenticated

    @abstractmethod
    def authenticate(self, config: VaultConfig) -> bool:
        """Authenticate with Vault using the provided configuration.
        
        Args:
            config: Vault configuration including auth details
            
        Returns:
            True if authentication successful, False otherwise
            
        Raises:
            VaultAuthenticationError: If authentication fails
            VaultConnectionError: If connection to Vault fails
        """

    @abstractmethod
    def get_secret(self, request: VaultSecretRequest) -> VaultSecretResponse:
        """Retrieve a secret from Vault.
        
        Args:
            request: Details about the secret to retrieve
            
        Returns:
            VaultSecretResponse containing the secret data
            
        Raises:
            VaultSecretNotFoundError: If secret is not found
            VaultAuthenticationError: If not authenticated
            VaultConnectionError: If connection fails
        """

    @abstractmethod
    def list_secrets(self, path: str, mount_point: Optional[str] = None) -> List[str]:
        """List secrets at the given path.
        
        Args:
            path: Vault path to list
            mount_point: Optional mount point
            
        Returns:
            List of secret names/paths
            
        Raises:
            VaultAuthenticationError: If not authenticated
            VaultConnectionError: If connection fails
        """

    def close(self) -> None:
        """Clean up resources and close connections."""
        self._authenticated = False


__all__ = [
    'VaultConfig',
    'VaultSecretRequest', 
    'VaultSecretResponse',
    'VaultPlugin',
    'VaultPluginBase',
    'VaultPluginError',
    'VaultAuthenticationError',
    'VaultConnectionError',
    'VaultSecretNotFoundError',
]