#!/usr/bin/env python3
"""
Example usage of AWX Vault plugin interfaces with ctypes Go bridge.

This example demonstrates how to:
1. Configure a Vault connection
2. Use the GoVaultPlugin to interact with a compiled Go shared library
3. Authenticate with Vault
4. Retrieve secrets
5. List secrets

Prerequisites:
- Compile the example_vault_plugin.go as a shared library:
  go build -buildmode=c-shared -o vault_plugin.so example_vault_plugin.go
"""

from pathlib import Path
from awx_plugins.interfaces import api


def main():
    """Demonstrate Vault plugin usage."""
    print("AWX Vault Plugin Example")
    print("=" * 40)
    
    # 1. Create Vault configuration
    print("\n1. Creating Vault configuration...")
    config = api.VaultConfig(
        url="https://vault.example.com",
        auth_method="token",
        auth_config={"token": "hvs.example-token"},
        verify_tls=True,
        timeout=30
    )
    print(f"   Configured Vault URL: {config.url}")
    print(f"   Auth method: {config.auth_method}")
    
    # 2. Look for available Vault libraries
    print("\n2. Discovering Vault libraries...")
    libraries = api.discover_vault_libraries()
    if libraries:
        print(f"   Found libraries: {libraries}")
        library_path = libraries[0]
    else:
        # Use example library path if discovery finds nothing
        library_path = Path("./examples/vault_plugin.so")
        print(f"   No libraries discovered, using example: {library_path}")
    
    if not library_path.exists():
        print(f"\n   Error: Library not found at {library_path}")
        print("   Please compile the Go example first:")
        print("   cd examples && go build -buildmode=c-shared -o vault_plugin.so example_vault_plugin.go")
        return
    
    # 3. Create and use Vault plugin
    print(f"\n3. Creating GoVaultPlugin with library: {library_path}")
    
    try:
        with api.GoVaultPlugin(library_path) as plugin:
            # 4. Authenticate with Vault
            print("\n4. Authenticating with Vault...")
            authenticated = plugin.authenticate(config)
            print(f"   Authentication successful: {authenticated}")
            
            if not authenticated:
                print("   Error: Authentication failed")
                return
            
            # 5. Retrieve a secret
            print("\n5. Retrieving secret...")
            request = api.VaultSecretRequest(
                path="secret/myapp",
                version=1
            )
            
            response = plugin.get_secret(request)
            print(f"   Secret data: {response.data}")
            print(f"   Metadata: {response.metadata}")
            if response.warnings:
                print(f"   Warnings: {response.warnings}")
            
            # 6. List secrets
            print("\n6. Listing secrets...")
            secrets = plugin.list_secrets("secret/")
            print(f"   Available secrets: {secrets}")
            
            # 7. Try retrieving another secret
            print("\n7. Retrieving another secret...")
            request2 = api.VaultSecretRequest(path="secret/database")
            response2 = plugin.get_secret(request2)
            print(f"   Secret data: {response2.data}")
            
    except api.VaultConnectionError as e:
        print(f"   Connection error: {e}")
    except api.VaultAuthenticationError as e:
        print(f"   Authentication error: {e}")
    except api.VaultPluginError as e:
        print(f"   Plugin error: {e}")
    except Exception as e:
        print(f"   Unexpected error: {e}")
    
    print("\n8. Plugin closed automatically (context manager)")
    print("\nExample completed successfully!")


def demonstrate_base_class():
    """Demonstrate how to implement a custom Vault plugin using the base class."""
    print("\n" + "=" * 60)
    print("Custom Vault Plugin Implementation Example")
    print("=" * 60)
    
    class MyVaultPlugin(api.VaultPluginBase):
        """Example custom Vault plugin implementation."""
        
        def authenticate(self, config: api.VaultConfig) -> bool:
            """Mock authentication implementation."""
            print(f"   Authenticating with {config.url} using {config.auth_method}")
            # Mock successful authentication
            self._authenticated = True
            return True
        
        def get_secret(self, request: api.VaultSecretRequest) -> api.VaultSecretResponse:
            """Mock secret retrieval implementation."""
            if not self.is_authenticated:
                raise api.VaultAuthenticationError("Not authenticated")
            
            print(f"   Retrieving secret from {request.path}")
            
            # Mock secret data
            mock_data = {
                "username": f"user-for-{request.path}",
                "password": f"pass-for-{request.path}",
            }
            
            return api.VaultSecretResponse(
                data=mock_data,
                metadata={"version": request.version or 1}
            )
        
        def list_secrets(self, path: str, mount_point: str = None) -> list[str]:
            """Mock secret listing implementation."""
            if not self.is_authenticated:
                raise api.VaultAuthenticationError("Not authenticated")
            
            print(f"   Listing secrets at {path}")
            
            # Mock secret list
            return [f"{path}/app1", f"{path}/app2", f"{path}/database"]
    
    # Use the custom plugin
    config = api.VaultConfig(
        url="https://vault.example.com",
        auth_method="custom",
        auth_config={"custom_param": "value"}
    )
    
    print("\n1. Creating custom Vault plugin...")
    plugin = MyVaultPlugin(config)
    
    print("\n2. Authenticating...")
    authenticated = plugin.authenticate(config)
    print(f"   Authenticated: {authenticated}")
    
    print("\n3. Retrieving secret...")
    request = api.VaultSecretRequest(path="secret/myapp")
    response = plugin.get_secret(request)
    print(f"   Secret: {response.data}")
    
    print("\n4. Listing secrets...")
    secrets = plugin.list_secrets("secret/")
    print(f"   Secrets: {secrets}")
    
    print("\n5. Closing plugin...")
    plugin.close()
    print(f"   Is authenticated: {plugin.is_authenticated}")


if __name__ == "__main__":
    main()
    demonstrate_base_class()