"""Tests for Vault plugin interfaces."""

import json
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, MagicMock

from awx_plugins.interfaces.vault import (
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


class TestVaultConfig:
    """Test VaultConfig dataclass."""

    def test_vault_config_creation(self):
        """Test basic VaultConfig creation."""
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        assert config.url == "https://vault.example.com"
        assert config.auth_method == "token"
        assert config.auth_config == {"token": "test-token"}
        assert config.namespace is None
        assert config.verify_tls is True
        assert config.timeout == 30

    def test_vault_config_with_optional_fields(self):
        """Test VaultConfig with all optional fields."""
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="userpass",
            auth_config={"username": "user", "password": "pass"},
            namespace="test-namespace",
            ca_cert_path=Path("/path/to/ca.crt"),
            client_cert_path=Path("/path/to/client.crt"),
            client_key_path=Path("/path/to/client.key"),
            verify_tls=False,
            timeout=60
        )
        
        assert config.namespace == "test-namespace"
        assert config.ca_cert_path == Path("/path/to/ca.crt")
        assert config.verify_tls is False
        assert config.timeout == 60


class TestVaultSecretRequest:
    """Test VaultSecretRequest dataclass."""

    def test_secret_request_creation(self):
        """Test basic VaultSecretRequest creation."""
        request = VaultSecretRequest(path="secret/myapp")
        
        assert request.path == "secret/myapp"
        assert request.mount_point is None
        assert request.version is None
        assert request.metadata is None

    def test_secret_request_with_optional_fields(self):
        """Test VaultSecretRequest with optional fields."""
        request = VaultSecretRequest(
            path="secret/myapp",
            mount_point="secret-v2", 
            version=3,
            metadata={"environment": "prod"}
        )
        
        assert request.path == "secret/myapp"
        assert request.mount_point == "secret-v2"
        assert request.version == 3
        assert request.metadata == {"environment": "prod"}


class TestVaultSecretResponse:
    """Test VaultSecretResponse dataclass."""

    def test_secret_response_creation(self):
        """Test basic VaultSecretResponse creation."""
        response = VaultSecretResponse(data={"password": "secret123"})
        
        assert response.data == {"password": "secret123"}
        assert response.metadata is None
        assert response.warnings is None

    def test_secret_response_with_optional_fields(self):
        """Test VaultSecretResponse with optional fields."""
        response = VaultSecretResponse(
            data={"password": "secret123"},
            metadata={"version": 1, "created_time": "2023-01-01T00:00:00Z"},
            warnings=["Secret is deprecated"]
        )
        
        assert response.data == {"password": "secret123"}
        assert response.metadata["version"] == 1
        assert response.warnings == ["Secret is deprecated"]


class TestVaultExceptions:
    """Test Vault exception hierarchy."""

    def test_vault_plugin_error_inheritance(self):
        """Test that Vault exceptions inherit correctly."""
        assert issubclass(VaultAuthenticationError, VaultPluginError)
        assert issubclass(VaultConnectionError, VaultPluginError) 
        assert issubclass(VaultSecretNotFoundError, VaultPluginError)

    def test_vault_plugin_error_creation(self):
        """Test creating Vault exceptions."""
        error = VaultPluginError("Generic error")
        assert str(error) == "Generic error"
        
        auth_error = VaultAuthenticationError("Auth failed")
        assert str(auth_error) == "Auth failed"
        
        conn_error = VaultConnectionError("Connection failed")
        assert str(conn_error) == "Connection failed"
        
        not_found_error = VaultSecretNotFoundError("Secret not found")
        assert str(not_found_error) == "Secret not found"


class MockVaultPlugin(VaultPluginBase):
    """Mock implementation of VaultPluginBase for testing."""

    def __init__(self, config: VaultConfig):
        super().__init__(config)
        self.authenticate_call_count = 0
        self.get_secret_call_count = 0
        self.list_secrets_call_count = 0

    def authenticate(self, config: VaultConfig) -> bool:
        """Mock authenticate implementation."""
        self.authenticate_call_count += 1
        if config.auth_config.get("fail_auth"):
            raise VaultAuthenticationError("Authentication failed")
        self._authenticated = True
        return True

    def get_secret(self, request: VaultSecretRequest) -> VaultSecretResponse:
        """Mock get_secret implementation."""
        self.get_secret_call_count += 1
        if not self.is_authenticated:
            raise VaultAuthenticationError("Not authenticated")
        
        if request.path == "secret/notfound":
            raise VaultSecretNotFoundError("Secret not found")
            
        return VaultSecretResponse(
            data={"password": f"secret-for-{request.path}"},
            metadata={"version": request.version or 1}
        )

    def list_secrets(self, path: str, mount_point: Optional[str] = None) -> List[str]:
        """Mock list_secrets implementation."""
        self.list_secrets_call_count += 1
        if not self.is_authenticated:
            raise VaultAuthenticationError("Not authenticated")
        
        return [f"{path}/secret1", f"{path}/secret2"]


class TestVaultPluginBase:
    """Test VaultPluginBase abstract base class."""

    def test_plugin_initialization(self):
        """Test plugin initialization."""
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        plugin = MockVaultPlugin(config)
        assert plugin.config == config
        assert not plugin.is_authenticated

    def test_plugin_authentication_success(self):
        """Test successful authentication."""
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        plugin = MockVaultPlugin(config)
        result = plugin.authenticate(config)
        
        assert result is True
        assert plugin.is_authenticated
        assert plugin.authenticate_call_count == 1

    def test_plugin_authentication_failure(self):
        """Test authentication failure."""
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token", "fail_auth": True}
        )
        
        plugin = MockVaultPlugin(config)
        
        with pytest.raises(VaultAuthenticationError, match="Authentication failed"):
            plugin.authenticate(config)
        
        assert not plugin.is_authenticated

    def test_get_secret_success(self):
        """Test successful secret retrieval."""
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        plugin = MockVaultPlugin(config)
        plugin.authenticate(config)
        
        request = VaultSecretRequest(path="secret/myapp")
        response = plugin.get_secret(request)
        
        assert response.data == {"password": "secret-for-secret/myapp"}
        assert response.metadata == {"version": 1}
        assert plugin.get_secret_call_count == 1

    def test_get_secret_without_authentication(self):
        """Test secret retrieval without authentication."""
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        plugin = MockVaultPlugin(config)
        request = VaultSecretRequest(path="secret/myapp")
        
        with pytest.raises(VaultAuthenticationError, match="Not authenticated"):
            plugin.get_secret(request)

    def test_get_secret_not_found(self):
        """Test secret not found error."""
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        plugin = MockVaultPlugin(config)
        plugin.authenticate(config)
        
        request = VaultSecretRequest(path="secret/notfound")
        
        with pytest.raises(VaultSecretNotFoundError, match="Secret not found"):
            plugin.get_secret(request)

    def test_list_secrets_success(self):
        """Test successful secret listing."""
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        plugin = MockVaultPlugin(config)
        plugin.authenticate(config)
        
        secrets = plugin.list_secrets("secret")
        
        assert secrets == ["secret/secret1", "secret/secret2"]
        assert plugin.list_secrets_call_count == 1

    def test_list_secrets_without_authentication(self):
        """Test secret listing without authentication."""
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        plugin = MockVaultPlugin(config)
        
        with pytest.raises(VaultAuthenticationError, match="Not authenticated"):
            plugin.list_secrets("secret")

    def test_plugin_close(self):
        """Test plugin cleanup."""
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        plugin = MockVaultPlugin(config)
        plugin.authenticate(config)
        
        assert plugin.is_authenticated
        
        plugin.close()
        
        assert not plugin.is_authenticated


class TestVaultPlugin:
    """Test VaultPlugin protocol."""

    def test_vault_plugin_protocol_compliance(self):
        """Test that MockVaultPlugin implements VaultPlugin protocol."""
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        plugin = MockVaultPlugin(config)
        
        # Check that the plugin implements the protocol methods
        assert hasattr(plugin, 'authenticate')
        assert hasattr(plugin, 'get_secret')
        assert hasattr(plugin, 'list_secrets')
        assert hasattr(plugin, 'close')
        
        # Verify the methods are callable
        assert callable(plugin.authenticate)
        assert callable(plugin.get_secret)
        assert callable(plugin.list_secrets)
        assert callable(plugin.close)


def test_vault_module_exports():
    """Test that vault module exports expected symbols."""
    from awx_plugins.interfaces import vault
    
    expected_exports = {
        'VaultConfig',
        'VaultSecretRequest',
        'VaultSecretResponse',
        'VaultPlugin',
        'VaultPluginBase',
        'VaultPluginError',
        'VaultAuthenticationError',
        'VaultConnectionError',
        'VaultSecretNotFoundError',
    }
    
    actual_exports = set(vault.__all__)
    assert actual_exports == expected_exports