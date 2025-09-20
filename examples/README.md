# AWX Vault Plugin Examples

This directory contains examples demonstrating how to use the AWX Vault plugin interfaces with ctypes integration for calling Go shared libraries.

## Files

- `example_vault_plugin.go` - Example Go implementation of a Vault plugin that can be compiled as a shared library
- `example_usage.py` - Python example showing how to use the Vault plugin interfaces
- `Makefile` - Build script for compiling the Go shared library

## Prerequisites

1. **Go** (version 1.18 or later) - Required to compile the Go shared library
2. **Python** (version 3.11 or later) - Required to run the Python examples
3. **awx_plugins.interfaces** - The Python package with Vault interfaces

## Building the Go Shared Library

To compile the example Go Vault plugin as a shared library:

```bash
cd examples
make build
```

Or manually:

```bash
go build -buildmode=c-shared -o vault_plugin.so example_vault_plugin.go
```

This will create:
- `vault_plugin.so` - The shared library (Linux)
- `vault_plugin.h` - The C header file (generated automatically)

## Running the Python Example

After building the shared library:

```bash
cd examples
python example_usage.py
```

## What the Example Demonstrates

### Go Shared Library (`example_vault_plugin.go`)

- Exports C-compatible functions for Python ctypes integration
- Implements basic Vault operations:
  - `VaultInit` - Initialize a new Vault session
  - `VaultAuthenticate` - Authenticate with Vault
  - `VaultGetSecret` - Retrieve a secret from Vault
  - `VaultListSecrets` - List available secrets
  - `VaultClose` - Close a Vault session
  - `FreeGoResult` - Free memory allocated by Go functions

- Uses JSON for data exchange between Go and Python
- Implements session management for concurrent access
- Mock implementation for demonstration (real implementation would use Vault Go client)

### Python Usage (`example_usage.py`)

1. **Configuration**: Shows how to create `VaultConfig` objects
2. **Library Discovery**: Demonstrates automatic discovery of Vault shared libraries
3. **Plugin Initialization**: Creates `GoVaultPlugin` instances
4. **Authentication**: Shows different authentication methods
5. **Secret Operations**: Retrieves and lists secrets
6. **Error Handling**: Demonstrates exception handling
7. **Custom Plugins**: Shows how to implement custom plugins using `VaultPluginBase`

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AWX Python    │    │ awx_plugins.     │    │  Go Shared      │
│   Application   │───▶│ interfaces       │───▶│  Library        │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              │ ctypes bridge
                              │
                       ┌──────▼──────────┐
                       │ VaultPlugin     │
                       │ Interface       │
                       │                 │
                       │ • VaultConfig   │
                       │ • SecretRequest │
                       │ • SecretResponse│
                       │ • Error Types   │
                       └─────────────────┘
```

## Integration Steps

To integrate Vault plugins with AWX:

1. **Implement Go Plugin**: Create a Go shared library implementing the Vault plugin interface
2. **Compile Library**: Build the Go code as a shared library (.so, .dll, or .dylib)
3. **Deploy Library**: Place the shared library in a discoverable location
4. **Configure AWX**: Configure AWX to use the Vault plugin with appropriate credentials
5. **Use in Workflows**: Reference Vault secrets in AWX job templates and workflows

## Real-World Implementation

For production use, replace the mock implementation in `example_vault_plugin.go` with:

1. **Vault Go Client**: Use the official HashiCorp Vault Go client library
2. **Proper Authentication**: Implement real authentication methods (token, AWS IAM, etc.)
3. **Error Handling**: Add comprehensive error handling and logging
4. **Security**: Implement proper secret handling and memory management
5. **Performance**: Add connection pooling and caching as needed

## Troubleshooting

### Library Not Found
- Ensure the Go shared library is compiled and in the expected location
- Check that Go is installed and available in PATH
- Verify the shared library extension matches your platform (.so, .dll, .dylib)

### Import Errors
- Ensure `awx_plugins.interfaces` is installed: `pip install awx_plugins.interfaces`
- Check Python path and virtual environment

### Go Build Errors
- Ensure Go version is 1.18 or later: `go version`
- Check that CGO is enabled: `go env CGO_ENABLED` (should be "1")

### Runtime Errors
- Check the Go shared library architecture matches Python architecture (32-bit vs 64-bit)
- Verify that all required symbols are exported from the Go library
- Check error messages in the Go function implementations