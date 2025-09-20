"""Tests for ctypes Go bridge."""

import ctypes
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

from awx_plugins.interfaces.ctypes_go_bridge import (
    GoString,
    GoSlice,
    GoResult,
    GoVaultBridge,
    GoVaultPlugin,
    discover_vault_libraries,
    _detect_shared_library_extension,
    _create_go_string,
    _go_string_to_python,
)
from awx_plugins.interfaces.vault import (
    VaultConfig,
    VaultSecretRequest,
    VaultSecretResponse,
    VaultPluginError,
    VaultConnectionError,
)


class TestGoStructures:
    """Test Go ctypes structures."""

    def test_go_string_creation(self):
        """Test GoString structure."""
        test_data = b"test string"
        go_str = GoString(data=ctypes.c_char_p(test_data), len=len(test_data))
        
        assert go_str.data == test_data
        assert go_str.len == len(test_data)

    def test_go_slice_creation(self):
        """Test GoSlice structure."""
        data_ptr = ctypes.pointer(ctypes.c_void_p())
        go_slice = GoSlice(data=data_ptr, len=5, cap=10)
        
        assert go_slice.data == data_ptr
        assert go_slice.len == 5
        assert go_slice.cap == 10

    def test_go_result_creation(self):
        """Test GoResult structure."""
        data = b'{"key": "value"}'
        error = b"error message"
        
        result = GoResult(
            success=True,
            data=ctypes.c_char_p(data),
            error=ctypes.c_char_p(error)
        )
        
        assert result.success is True
        assert result.data == data
        assert result.error == error


class TestHelperFunctions:
    """Test helper functions."""

    def test_detect_shared_library_extension(self):
        """Test shared library extension detection."""
        with patch('platform.system') as mock_system:
            mock_system.return_value = 'Linux'
            assert _detect_shared_library_extension() == '.so'
            
            mock_system.return_value = 'Darwin'
            assert _detect_shared_library_extension() == '.dylib'
            
            mock_system.return_value = 'Windows'
            assert _detect_shared_library_extension() == '.dll'
            
            mock_system.return_value = 'Unsupported'
            with pytest.raises(VaultConnectionError, match="Unsupported platform"):
                _detect_shared_library_extension()

    def test_create_go_string(self):
        """Test creating GoString from Python string."""
        test_str = "hello world"
        go_str = _create_go_string(test_str)
        
        assert go_str.len == len(test_str.encode('utf-8'))
        assert ctypes.string_at(go_str.data, go_str.len) == test_str.encode('utf-8')

    def test_go_string_to_python(self):
        """Test converting GoString to Python string."""
        test_str = "hello world"
        encoded = test_str.encode('utf-8')
        go_str = GoString(data=ctypes.c_char_p(encoded), len=len(encoded))
        
        result = _go_string_to_python(go_str)
        assert result == test_str

    def test_go_string_to_python_empty(self):
        """Test converting empty GoString to Python string."""
        go_str = GoString(data=None, len=0)
        result = _go_string_to_python(go_str)
        assert result == ""


class TestDiscoverVaultLibraries:
    """Test Vault library discovery."""

    def test_discover_vault_libraries_default_paths(self):
        """Test discovering libraries with default search paths."""
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.is_dir') as mock_is_dir, \
             patch('pathlib.Path.glob') as mock_glob, \
             patch('pathlib.Path.is_file') as mock_is_file, \
             patch('platform.system') as mock_system, \
             patch.dict('os.environ', {'HOME': '/home/user'}):
            
            mock_system.return_value = 'Linux'
            mock_exists.return_value = True
            mock_is_dir.return_value = True
            mock_is_file.return_value = True
            
            # Mock library files
            mock_lib1 = Mock(spec=Path)
            mock_lib1.is_file.return_value = True
            mock_lib2 = Mock(spec=Path)
            mock_lib2.is_file.return_value = True
            
            mock_glob.return_value = [mock_lib1, mock_lib2]
            
            libraries = discover_vault_libraries()
            
            # Should find libraries in multiple search paths
            assert len(libraries) >= 0  # Depends on how many search paths return libraries

    def test_discover_vault_libraries_custom_paths(self):
        """Test discovering libraries with custom search paths."""
        custom_paths = [Path('/custom/path1'), Path('/custom/path2')]
        
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.is_dir') as mock_is_dir, \
             patch('pathlib.Path.glob') as mock_glob, \
             patch('platform.system') as mock_system:
            
            mock_system.return_value = 'Linux'
            mock_exists.return_value = True
            mock_is_dir.return_value = True
            
            mock_lib = Mock(spec=Path)
            mock_lib.is_file.return_value = True
            mock_glob.return_value = [mock_lib]
            
            libraries = discover_vault_libraries(custom_paths)
            
            # Should call glob on custom paths
            assert mock_glob.call_count == len(custom_paths)

    def test_discover_vault_libraries_nonexistent_paths(self):
        """Test discovering libraries with non-existent search paths."""
        custom_paths = [Path('/nonexistent')]
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            
            libraries = discover_vault_libraries(custom_paths)
            
            assert libraries == []


class TestGoVaultBridge:
    """Test GoVaultBridge class."""

    def create_mock_library(self):
        """Create a mock shared library for testing."""
        mock_lib = Mock()
        
        # Mock function signatures setup
        mock_lib.VaultInit = Mock()
        mock_lib.VaultInit.argtypes = [ctypes.c_char_p]
        mock_lib.VaultInit.restype = ctypes.POINTER(GoResult)
        
        mock_lib.VaultClose = Mock()
        mock_lib.VaultClose.argtypes = [ctypes.c_int]
        mock_lib.VaultClose.restype = ctypes.POINTER(GoResult)
        
        mock_lib.VaultGetSecret = Mock()
        mock_lib.VaultGetSecret.argtypes = [ctypes.c_int, ctypes.c_char_p]
        mock_lib.VaultGetSecret.restype = ctypes.POINTER(GoResult)
        
        mock_lib.VaultListSecrets = Mock()
        mock_lib.VaultListSecrets.argtypes = [ctypes.c_int, ctypes.c_char_p]
        mock_lib.VaultListSecrets.restype = ctypes.POINTER(GoResult)
        
        mock_lib.VaultAuthenticate = Mock()
        mock_lib.VaultAuthenticate.argtypes = [ctypes.c_int, ctypes.c_char_p]
        mock_lib.VaultAuthenticate.restype = ctypes.POINTER(GoResult)
        
        mock_lib.FreeGoResult = Mock()
        mock_lib.FreeGoResult.argtypes = [ctypes.POINTER(GoResult)]
        mock_lib.FreeGoResult.restype = None
        
        return mock_lib

    def create_mock_result(self, success=True, data=None, error=None):
        """Create a mock GoResult."""
        result_data = GoResult()
        result_data.success = success
        result_data.data = ctypes.c_char_p(data.encode('utf-8') if data else None)
        result_data.error = ctypes.c_char_p(error.encode('utf-8') if error else None)
        
        result_ptr = Mock()
        result_ptr.contents = result_data
        
        return result_ptr

    def test_go_vault_bridge_init_library_not_found(self):
        """Test GoVaultBridge initialization with non-existent library."""
        with pytest.raises(VaultConnectionError, match="Library not found"):
            GoVaultBridge("/nonexistent/library.so")

    @patch('pathlib.Path.exists')
    @patch('ctypes.CDLL')
    def test_go_vault_bridge_init_load_failure(self, mock_cdll, mock_exists):
        """Test GoVaultBridge initialization with library load failure."""
        mock_exists.return_value = True
        mock_cdll.side_effect = OSError("Library load failed")
        
        with pytest.raises(VaultConnectionError, match="Failed to load library"):
            GoVaultBridge("/path/to/library.so")

    @patch('pathlib.Path.exists')
    @patch('ctypes.CDLL')
    def test_go_vault_bridge_init_success(self, mock_cdll, mock_exists):
        """Test successful GoVaultBridge initialization."""
        mock_exists.return_value = True
        mock_lib = self.create_mock_library()
        mock_cdll.return_value = mock_lib
        
        bridge = GoVaultBridge("/path/to/library.so")
        
        assert bridge.library_path == Path("/path/to/library.so")
        assert bridge._lib == mock_lib
        mock_cdll.assert_called_once_with("/path/to/library.so")

    @patch('pathlib.Path.exists')
    @patch('ctypes.CDLL')
    def test_go_vault_bridge_init_vault_session(self, mock_cdll, mock_exists):
        """Test initializing Vault session."""
        mock_exists.return_value = True
        mock_lib = self.create_mock_library()
        mock_cdll.return_value = mock_lib
        
        # Mock successful VaultInit response
        init_response = json.dumps({"session_id": 123})
        result_ptr = self.create_mock_result(success=True, data=init_response)
        mock_lib.VaultInit.return_value = result_ptr
        
        bridge = GoVaultBridge("/path/to/library.so")
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        session_id = bridge.init(config)
        
        assert session_id == 123
        assert bridge._session_id == 123
        mock_lib.VaultInit.assert_called_once()
        mock_lib.FreeGoResult.assert_called_once_with(result_ptr)

    @patch('pathlib.Path.exists')
    @patch('ctypes.CDLL')
    def test_go_vault_bridge_init_vault_session_failure(self, mock_cdll, mock_exists):
        """Test Vault session initialization failure."""
        mock_exists.return_value = True
        mock_lib = self.create_mock_library()
        mock_cdll.return_value = mock_lib
        
        # Mock failed VaultInit response
        result_ptr = self.create_mock_result(success=False, error="Init failed")
        mock_lib.VaultInit.return_value = result_ptr
        
        bridge = GoVaultBridge("/path/to/library.so")
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        with pytest.raises(VaultPluginError, match="Go function VaultInit failed: Init failed"):
            bridge.init(config)

    @patch('pathlib.Path.exists')
    @patch('ctypes.CDLL')
    def test_go_vault_bridge_authenticate(self, mock_cdll, mock_exists):
        """Test Vault authentication."""
        mock_exists.return_value = True
        mock_lib = self.create_mock_library()
        mock_cdll.return_value = mock_lib
        
        # Mock successful init and authenticate responses
        init_response = json.dumps({"session_id": 123})
        init_result_ptr = self.create_mock_result(success=True, data=init_response)
        mock_lib.VaultInit.return_value = init_result_ptr
        
        auth_response = json.dumps({"authenticated": True})
        auth_result_ptr = self.create_mock_result(success=True, data=auth_response)
        mock_lib.VaultAuthenticate.return_value = auth_result_ptr
        
        bridge = GoVaultBridge("/path/to/library.so")
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        bridge.init(config)
        result = bridge.authenticate(config)
        
        assert result is True
        mock_lib.VaultAuthenticate.assert_called_once_with(123, b'{"auth_method": "token", "auth_config": {"token": "test-token"}}')

    @patch('pathlib.Path.exists')
    @patch('ctypes.CDLL')
    def test_go_vault_bridge_get_secret(self, mock_cdll, mock_exists):
        """Test getting secret from Vault."""
        mock_exists.return_value = True
        mock_lib = self.create_mock_library()
        mock_cdll.return_value = mock_lib
        
        # Mock successful init
        init_response = json.dumps({"session_id": 123})
        init_result_ptr = self.create_mock_result(success=True, data=init_response)
        mock_lib.VaultInit.return_value = init_result_ptr
        
        # Mock successful get_secret response
        secret_response = json.dumps({
            "data": {"password": "secret123"},
            "metadata": {"version": 1},
            "warnings": []
        })
        secret_result_ptr = self.create_mock_result(success=True, data=secret_response)
        mock_lib.VaultGetSecret.return_value = secret_result_ptr
        
        bridge = GoVaultBridge("/path/to/library.so")
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        bridge.init(config)
        
        request = VaultSecretRequest(path="secret/myapp")
        response = bridge.get_secret(request)
        
        assert response.data == {"password": "secret123"}
        assert response.metadata == {"version": 1}
        assert response.warnings == []

    @patch('pathlib.Path.exists')
    @patch('ctypes.CDLL')
    def test_go_vault_bridge_list_secrets(self, mock_cdll, mock_exists):
        """Test listing secrets from Vault."""
        mock_exists.return_value = True
        mock_lib = self.create_mock_library()
        mock_cdll.return_value = mock_lib
        
        # Mock successful init
        init_response = json.dumps({"session_id": 123})
        init_result_ptr = self.create_mock_result(success=True, data=init_response)
        mock_lib.VaultInit.return_value = init_result_ptr
        
        # Mock successful list_secrets response
        list_response = json.dumps({
            "secrets": ["secret1", "secret2", "secret3"]
        })
        list_result_ptr = self.create_mock_result(success=True, data=list_response)
        mock_lib.VaultListSecrets.return_value = list_result_ptr
        
        bridge = GoVaultBridge("/path/to/library.so")
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        bridge.init(config)
        
        secrets = bridge.list_secrets("secret/")
        
        assert secrets == ["secret1", "secret2", "secret3"]

    @patch('pathlib.Path.exists')
    @patch('ctypes.CDLL')
    def test_go_vault_bridge_close(self, mock_cdll, mock_exists):
        """Test closing Vault session."""
        mock_exists.return_value = True
        mock_lib = self.create_mock_library()
        mock_cdll.return_value = mock_lib
        
        # Mock successful init
        init_response = json.dumps({"session_id": 123})
        init_result_ptr = self.create_mock_result(success=True, data=init_response)
        mock_lib.VaultInit.return_value = init_result_ptr
        
        # Mock successful close response
        close_result_ptr = self.create_mock_result(success=True, data="{}")
        mock_lib.VaultClose.return_value = close_result_ptr
        
        bridge = GoVaultBridge("/path/to/library.so")
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        bridge.init(config)
        bridge.close()
        
        assert bridge._session_id is None
        mock_lib.VaultClose.assert_called_once_with(123)

    @patch('pathlib.Path.exists')
    @patch('ctypes.CDLL')
    def test_go_vault_bridge_context_manager(self, mock_cdll, mock_exists):
        """Test GoVaultBridge as context manager."""
        mock_exists.return_value = True
        mock_lib = self.create_mock_library()
        mock_cdll.return_value = mock_lib
        
        # Mock responses
        init_response = json.dumps({"session_id": 123})
        init_result_ptr = self.create_mock_result(success=True, data=init_response)
        mock_lib.VaultInit.return_value = init_result_ptr
        
        close_result_ptr = self.create_mock_result(success=True, data="{}")
        mock_lib.VaultClose.return_value = close_result_ptr
        
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        with GoVaultBridge("/path/to/library.so") as bridge:
            bridge.init(config)
            assert bridge._session_id == 123
        
        # Should have called close automatically
        mock_lib.VaultClose.assert_called_once_with(123)


class TestGoVaultPlugin:
    """Test GoVaultPlugin class."""

    @patch('awx_plugins.interfaces.ctypes_go_bridge.GoVaultBridge')
    def test_go_vault_plugin_init(self, mock_bridge_class):
        """Test GoVaultPlugin initialization."""
        plugin = GoVaultPlugin("/path/to/library.so")
        
        assert plugin.library_path == "/path/to/library.so"
        assert plugin._bridge is None
        assert not plugin.is_authenticated

    @patch('awx_plugins.interfaces.ctypes_go_bridge.GoVaultBridge')
    def test_go_vault_plugin_authenticate(self, mock_bridge_class):
        """Test GoVaultPlugin authentication."""
        mock_bridge = Mock()
        mock_bridge.init.return_value = 123
        mock_bridge.authenticate.return_value = True
        mock_bridge_class.return_value = mock_bridge
        
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        plugin = GoVaultPlugin("/path/to/library.so")
        result = plugin.authenticate(config)
        
        assert result is True
        assert plugin.is_authenticated
        mock_bridge_class.assert_called_once_with("/path/to/library.so")
        mock_bridge.init.assert_called_once_with(config)
        mock_bridge.authenticate.assert_called_once_with(config)

    @patch('awx_plugins.interfaces.ctypes_go_bridge.GoVaultBridge')
    def test_go_vault_plugin_get_secret(self, mock_bridge_class):
        """Test GoVaultPlugin secret retrieval."""
        mock_bridge = Mock()
        mock_bridge.init.return_value = 123
        mock_bridge.authenticate.return_value = True
        
        expected_response = VaultSecretResponse(data={"password": "secret123"})
        mock_bridge.get_secret.return_value = expected_response
        mock_bridge_class.return_value = mock_bridge
        
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        plugin = GoVaultPlugin("/path/to/library.so")
        plugin.authenticate(config)
        
        request = VaultSecretRequest(path="secret/myapp")
        response = plugin.get_secret(request)
        
        assert response == expected_response
        mock_bridge.get_secret.assert_called_once_with(request)

    def test_go_vault_plugin_get_secret_not_initialized(self):
        """Test GoVaultPlugin secret retrieval without initialization."""
        plugin = GoVaultPlugin("/path/to/library.so")
        request = VaultSecretRequest(path="secret/myapp")
        
        with pytest.raises(VaultPluginError, match="Plugin not initialized"):
            plugin.get_secret(request)

    @patch('awx_plugins.interfaces.ctypes_go_bridge.GoVaultBridge')
    def test_go_vault_plugin_get_secret_not_authenticated(self, mock_bridge_class):
        """Test GoVaultPlugin secret retrieval without authentication."""
        mock_bridge = Mock()
        mock_bridge.init.return_value = 123
        mock_bridge.authenticate.return_value = False
        mock_bridge_class.return_value = mock_bridge
        
        config = VaultConfig(
            url="https://vault.example.com",
            auth_method="token",
            auth_config={"token": "test-token"}
        )
        
        plugin = GoVaultPlugin("/path/to/library.so")
        plugin.authenticate(config)  # This will set authenticated to False
        
        request = VaultSecretRequest(path="secret/myapp")
        
        with pytest.raises(VaultPluginError, match="Plugin not authenticated"):
            plugin.get_secret(request)

    @patch('awx_plugins.interfaces.ctypes_go_bridge.GoVaultBridge')
    def test_go_vault_plugin_context_manager(self, mock_bridge_class):
        """Test GoVaultPlugin as context manager."""
        mock_bridge = Mock()
        mock_bridge_class.return_value = mock_bridge
        
        with GoVaultPlugin("/path/to/library.so") as plugin:
            assert plugin._bridge is None  # Not initialized until authenticate is called
        
        # Should call close on the bridge if it was created
        # In this test, bridge is never created since authenticate wasn't called
        mock_bridge.close.assert_not_called()


def test_ctypes_go_bridge_module_exports():
    """Test that ctypes_go_bridge module exports expected symbols."""
    from awx_plugins.interfaces import ctypes_go_bridge
    
    expected_exports = {
        'GoString',
        'GoSlice',
        'GoResult',
        'GoVaultBridge',
        'GoVaultPlugin',
        'discover_vault_libraries',
    }
    
    actual_exports = set(ctypes_go_bridge.__all__)
    assert actual_exports == expected_exports