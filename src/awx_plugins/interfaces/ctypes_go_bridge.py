"""Ctypes bridge for interfacing with Go shared libraries.

This module provides a bridge between Python and Go code using ctypes,
allowing AWX to call HashiCorp Vault plugins compiled as shared libraries.
"""

from __future__ import annotations

import ctypes
import json
import logging
import os
import platform
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .vault import (
    VaultConfig,
    VaultConnectionError,
    VaultPlugin,
    VaultPluginError,
    VaultSecretRequest,
    VaultSecretResponse,
)

logger = logging.getLogger(__name__)


class GoString(ctypes.Structure):
    """Go string representation for ctypes."""
    
    _fields_ = [
        ('data', ctypes.c_char_p),
        ('len', ctypes.c_longlong),
    ]


class GoSlice(ctypes.Structure):
    """Go slice representation for ctypes."""
    
    _fields_ = [
        ('data', ctypes.POINTER(ctypes.c_void_p)),
        ('len', ctypes.c_longlong),
        ('cap', ctypes.c_longlong),
    ]


class GoResult(ctypes.Structure):
    """Standard result structure from Go functions."""
    
    _fields_ = [
        ('success', ctypes.c_bool),
        ('data', ctypes.c_char_p),
        ('error', ctypes.c_char_p),
    ]


def _detect_shared_library_extension() -> str:
    """Detect the appropriate shared library extension for the current platform."""
    system = platform.system().lower()
    if system == 'linux':
        return '.so'
    elif system == 'darwin':
        return '.dylib'
    elif system == 'windows':
        return '.dll'
    else:
        raise VaultConnectionError(f"Unsupported platform: {system}")


def _create_go_string(s: str) -> GoString:
    """Create a GoString from a Python string."""
    encoded = s.encode('utf-8')
    return GoString(data=ctypes.c_char_p(encoded), len=len(encoded))


def _go_string_to_python(go_str: GoString) -> str:
    """Convert a GoString to a Python string."""
    if go_str.data:
        return ctypes.string_at(go_str.data, go_str.len).decode('utf-8')
    return ""


class GoVaultBridge:
    """Bridge class for interfacing with Go-based Vault plugins via ctypes."""

    def __init__(self, library_path: Union[str, Path]) -> None:
        """Initialize the Go bridge with a shared library.
        
        Args:
            library_path: Path to the Go shared library
            
        Raises:
            VaultConnectionError: If library cannot be loaded
        """
        self.library_path = Path(library_path)
        self._lib: Optional[ctypes.CDLL] = None
        self._session_id: Optional[int] = None
        
        if not self.library_path.exists():
            raise VaultConnectionError(f"Library not found: {library_path}")
        
        self._load_library()
        self._setup_function_signatures()

    def _load_library(self) -> None:
        """Load the shared library."""
        try:
            self._lib = ctypes.CDLL(str(self.library_path))
            logger.info(f"Loaded Go library: {self.library_path}")
        except OSError as e:
            raise VaultConnectionError(f"Failed to load library {self.library_path}: {e}")

    def _setup_function_signatures(self) -> None:
        """Set up function signatures for the Go library functions."""
        if not self._lib:
            raise VaultConnectionError("Library not loaded")

        # VaultInit(config *C.char) *GoResult
        self._lib.VaultInit.argtypes = [ctypes.c_char_p]
        self._lib.VaultInit.restype = ctypes.POINTER(GoResult)

        # VaultClose(sessionId C.int) *GoResult  
        self._lib.VaultClose.argtypes = [ctypes.c_int]
        self._lib.VaultClose.restype = ctypes.POINTER(GoResult)

        # VaultGetSecret(sessionId C.int, request *C.char) *GoResult
        self._lib.VaultGetSecret.argtypes = [ctypes.c_int, ctypes.c_char_p]
        self._lib.VaultGetSecret.restype = ctypes.POINTER(GoResult)

        # VaultListSecrets(sessionId C.int, path *C.char) *GoResult
        self._lib.VaultListSecrets.argtypes = [ctypes.c_int, ctypes.c_char_p]
        self._lib.VaultListSecrets.restype = ctypes.POINTER(GoResult)

        # VaultAuthenticate(sessionId C.int, config *C.char) *GoResult
        self._lib.VaultAuthenticate.argtypes = [ctypes.c_int, ctypes.c_char_p]
        self._lib.VaultAuthenticate.restype = ctypes.POINTER(GoResult)

        # FreeGoResult(result *GoResult)
        self._lib.FreeGoResult.argtypes = [ctypes.POINTER(GoResult)]
        self._lib.FreeGoResult.restype = None

    def _call_go_function(self, func_name: str, *args) -> Dict[str, Any]:
        """Call a Go function and handle the result.
        
        Args:
            func_name: Name of the Go function to call
            *args: Arguments to pass to the function
            
        Returns:
            Parsed result from the Go function
            
        Raises:
            VaultPluginError: If the Go function returns an error
        """
        if not self._lib:
            raise VaultConnectionError("Library not loaded")

        func = getattr(self._lib, func_name)
        result_ptr = func(*args)
        
        if not result_ptr:
            raise VaultPluginError(f"Go function {func_name} returned null")

        result = result_ptr.contents
        
        try:
            if result.success:
                data_str = ctypes.string_at(result.data).decode('utf-8') if result.data else "{}"
                return json.loads(data_str)
            else:
                error_str = ctypes.string_at(result.error).decode('utf-8') if result.error else "Unknown error"
                raise VaultPluginError(f"Go function {func_name} failed: {error_str}")
        finally:
            # Free the Go-allocated memory
            self._lib.FreeGoResult(result_ptr)

    def init(self, config: VaultConfig) -> int:
        """Initialize a Vault session.
        
        Args:
            config: Vault configuration
            
        Returns:
            Session ID for subsequent operations
            
        Raises:
            VaultPluginError: If initialization fails
        """
        config_json = json.dumps({
            'url': config.url,
            'auth_method': config.auth_method,
            'auth_config': config.auth_config,
            'namespace': config.namespace,
            'ca_cert_path': str(config.ca_cert_path) if config.ca_cert_path else None,
            'client_cert_path': str(config.client_cert_path) if config.client_cert_path else None,
            'client_key_path': str(config.client_key_path) if config.client_key_path else None,
            'verify_tls': config.verify_tls,
            'timeout': config.timeout,
        })
        
        config_bytes = config_json.encode('utf-8')
        result = self._call_go_function('VaultInit', config_bytes)
        
        self._session_id = result.get('session_id')
        if self._session_id is None:
            raise VaultPluginError("Go library did not return session_id")
            
        return self._session_id

    def authenticate(self, config: VaultConfig) -> bool:
        """Authenticate with Vault.
        
        Args:
            config: Vault configuration including auth details
            
        Returns:
            True if authentication successful
            
        Raises:
            VaultPluginError: If authentication fails
        """
        if self._session_id is None:
            raise VaultPluginError("Session not initialized")

        auth_json = json.dumps({
            'auth_method': config.auth_method,
            'auth_config': config.auth_config,
        })
        
        auth_bytes = auth_json.encode('utf-8')
        result = self._call_go_function('VaultAuthenticate', self._session_id, auth_bytes)
        
        return result.get('authenticated', False)

    def get_secret(self, request: VaultSecretRequest) -> VaultSecretResponse:
        """Retrieve a secret from Vault.
        
        Args:
            request: Secret request details
            
        Returns:
            Secret response with data
            
        Raises:
            VaultPluginError: If secret retrieval fails
        """
        if self._session_id is None:
            raise VaultPluginError("Session not initialized")

        request_json = json.dumps({
            'path': request.path,
            'mount_point': request.mount_point,
            'version': request.version,
            'metadata': request.metadata or {},
        })
        
        request_bytes = request_json.encode('utf-8')
        result = self._call_go_function('VaultGetSecret', self._session_id, request_bytes)
        
        return VaultSecretResponse(
            data=result.get('data', {}),
            metadata=result.get('metadata'),
            warnings=result.get('warnings'),
        )

    def list_secrets(self, path: str, mount_point: Optional[str] = None) -> list[str]:
        """List secrets at the given path.
        
        Args:
            path: Vault path to list
            mount_point: Optional mount point
            
        Returns:
            List of secret names/paths
            
        Raises:
            VaultPluginError: If listing fails
        """
        if self._session_id is None:
            raise VaultPluginError("Session not initialized")

        request_json = json.dumps({
            'path': path,
            'mount_point': mount_point,
        })
        
        request_bytes = request_json.encode('utf-8')
        result = self._call_go_function('VaultListSecrets', self._session_id, request_bytes)
        
        return result.get('secrets', [])

    def close(self) -> None:
        """Close the Vault session and clean up resources."""
        if self._session_id is not None:
            try:
                self._call_go_function('VaultClose', self._session_id)
            except VaultPluginError:
                # Log but don't raise - we're cleaning up
                logger.warning(f"Error closing Vault session {self._session_id}")
            finally:
                self._session_id = None

    def __enter__(self) -> GoVaultBridge:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


class GoVaultPlugin:
    """Vault plugin implementation using Go shared libraries via ctypes."""

    def __init__(self, library_path: Union[str, Path]) -> None:
        """Initialize the Go Vault plugin.
        
        Args:
            library_path: Path to the Go shared library
        """
        self.library_path = library_path
        self._bridge: Optional[GoVaultBridge] = None
        self._authenticated = False

    @property
    def is_authenticated(self) -> bool:
        """Check if the plugin is authenticated with Vault."""
        return self._authenticated

    def authenticate(self, config: VaultConfig) -> bool:
        """Authenticate with Vault using the provided configuration.
        
        Args:
            config: Vault configuration including auth details
            
        Returns:
            True if authentication successful, False otherwise
            
        Raises:
            VaultPluginError: If authentication fails
        """
        if not self._bridge:
            self._bridge = GoVaultBridge(self.library_path)
            self._bridge.init(config)

        self._authenticated = self._bridge.authenticate(config)
        return self._authenticated

    def get_secret(self, request: VaultSecretRequest) -> VaultSecretResponse:
        """Retrieve a secret from Vault.
        
        Args:
            request: Details about the secret to retrieve
            
        Returns:
            VaultSecretResponse containing the secret data
            
        Raises:
            VaultPluginError: If secret retrieval fails
        """
        if not self._bridge:
            raise VaultPluginError("Plugin not initialized - call authenticate() first")
            
        if not self._authenticated:
            raise VaultPluginError("Plugin not authenticated - call authenticate() first")

        return self._bridge.get_secret(request)

    def list_secrets(self, path: str, mount_point: Optional[str] = None) -> list[str]:
        """List secrets at the given path.
        
        Args:
            path: Vault path to list
            mount_point: Optional mount point
            
        Returns:
            List of secret names/paths
            
        Raises:
            VaultPluginError: If listing fails
        """
        if not self._bridge:
            raise VaultPluginError("Plugin not initialized - call authenticate() first")
            
        if not self._authenticated:
            raise VaultPluginError("Plugin not authenticated - call authenticate() first")

        return self._bridge.list_secrets(path, mount_point)

    def close(self) -> None:
        """Clean up resources and close connections."""
        if self._bridge:
            self._bridge.close()
            self._bridge = None
        self._authenticated = False

    def __enter__(self) -> GoVaultPlugin:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


def discover_vault_libraries(search_paths: Optional[list[Union[str, Path]]] = None) -> list[Path]:
    """Discover available Vault Go shared libraries.
    
    Args:
        search_paths: Optional list of paths to search for libraries
        
    Returns:
        List of discovered library paths
    """
    if search_paths is None:
        # Default search paths
        search_paths = [
            Path.cwd() / 'vault_plugins',
            Path('/usr/local/lib/vault_plugins'),
            Path('/opt/vault_plugins'),
        ]
        
        # Add user-specific paths
        if 'HOME' in os.environ:
            search_paths.append(Path(os.environ['HOME']) / '.vault_plugins')

    extension = _detect_shared_library_extension()
    libraries = []
    
    for search_path in search_paths:
        search_path = Path(search_path)
        if search_path.exists() and search_path.is_dir():
            for lib_file in search_path.glob(f'*vault*{extension}'):
                if lib_file.is_file():
                    libraries.append(lib_file)
    
    return libraries


__all__ = [
    'GoString',
    'GoSlice', 
    'GoResult',
    'GoVaultBridge',
    'GoVaultPlugin',
    'discover_vault_libraries',
]