"""Tests for API entry point module."""

import pytest


def test_api_module_imports():
    """Test that API module imports work correctly."""
    from awx_plugins.interfaces import api
    
    # Test that we can import the main classes
    assert hasattr(api, 'VaultConfig')
    assert hasattr(api, 'VaultPlugin')
    assert hasattr(api, 'VaultPluginBase')
    assert hasattr(api, 'VaultSecretRequest')
    assert hasattr(api, 'VaultSecretResponse')
    
    # Test that we can import the exceptions
    assert hasattr(api, 'VaultPluginError')
    assert hasattr(api, 'VaultAuthenticationError')
    assert hasattr(api, 'VaultConnectionError')
    assert hasattr(api, 'VaultSecretNotFoundError')
    
    # Test that we can import the ctypes bridge
    assert hasattr(api, 'GoVaultBridge')
    assert hasattr(api, 'GoVaultPlugin')
    assert hasattr(api, 'discover_vault_libraries')


def test_api_module_exports():
    """Test that API module exports expected symbols."""
    from awx_plugins.interfaces import api
    
    expected_exports = {
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
    }
    
    actual_exports = set(api.__all__)
    assert actual_exports == expected_exports


def test_api_classes_are_importable():
    """Test that all exported classes can be imported and instantiated."""
    from awx_plugins.interfaces.api import (
        VaultConfig,
        VaultSecretRequest,
        VaultSecretResponse,
        VaultPluginError,
        VaultAuthenticationError,
        VaultConnectionError,
        VaultSecretNotFoundError,
    )
    
    # Test VaultConfig creation
    config = VaultConfig(
        url="https://vault.example.com",
        auth_method="token",
        auth_config={"token": "test-token"}
    )
    assert config.url == "https://vault.example.com"
    
    # Test VaultSecretRequest creation
    request = VaultSecretRequest(path="secret/myapp")
    assert request.path == "secret/myapp"
    
    # Test VaultSecretResponse creation
    response = VaultSecretResponse(data={"key": "value"})
    assert response.data == {"key": "value"}
    
    # Test exception creation
    error = VaultPluginError("Test error")
    assert str(error) == "Test error"
    
    auth_error = VaultAuthenticationError("Auth error")
    assert str(auth_error) == "Auth error"
    
    conn_error = VaultConnectionError("Connection error")
    assert str(conn_error) == "Connection error"
    
    not_found_error = VaultSecretNotFoundError("Not found error")
    assert str(not_found_error) == "Not found error"


def test_smoke_integration():
    """Smoke test to ensure basic integration works."""
    from awx_plugins.interfaces import api
    
    # Test that we can create a basic configuration
    config = api.VaultConfig(
        url="https://vault.example.com",
        auth_method="token", 
        auth_config={"token": "test-token"}
    )
    
    # Test that we can create a request
    request = api.VaultSecretRequest(path="secret/myapp")
    
    # Test that we can create a response
    response = api.VaultSecretResponse(data={"password": "secret123"})
    
    # Test that the types are what we expect
    assert isinstance(config, api.VaultConfig)
    assert isinstance(request, api.VaultSecretRequest)
    assert isinstance(response, api.VaultSecretResponse)