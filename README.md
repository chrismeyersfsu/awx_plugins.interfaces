<!-- DO-NOT-REMOVE-docs-badges-START -->

[![CI/CD Badge]][CI/CD]
[![pre-commit.ci Badge]][pre-commit.ci]
[![PyPI Badge]][PyPI]
[![PyPI Supported Versions Badge]][PyPI Supported Versions]
[![Codecov Badge]][Codecov]
[![Code of Conduct Badge]][Code of Conduct]
[![Apache v2 License Badge]][Apache v2 License]
[![Ansible Matrix Badge]][Ansible Matrix]
[![Ansible Discourse Badge]][Ansible Discourse]

[CI/CD Badge]:
https://github.com/ansible/awx_plugins.interfaces/actions/workflows/ci-cd.yml/badge.svg?branch=devel
[CI/CD]: https://github.com/ansible/awx_plugins.interfaces/actions/workflows/ci-cd.yml

[pre-commit.ci Badge]:
https://results.pre-commit.ci/badge/github/ansible/awx_plugins.interfaces/devel.svg
[pre-commit.ci]:
https://results.pre-commit.ci/latest/github/ansible/awx_plugins.interfaces/devel

[PyPI Badge]: https://img.shields.io/pypi/v/awx_plugins.interfaces
[PyPI]: https://pypi.org/p/awx_plugins.interfaces

[PyPI Supported Versions Badge]: https://img.shields.io/pypi/pyversions/awx_plugins.interfaces.svg
[PyPI Supported Versions]: https://pypi.org/p/awx_plugins.interfaces

[Codecov Badge]: https://codecov.io/gh/ansible/awx_plugins.interfaces/branch/devel/graph/badge.svg
[Codecov]: https://app.codecov.io/gh/ansible/awx_plugins.interfaces

[Code of Conduct Badge]: https://img.shields.io/badge/code%20of%20conduct-Ansible-yellow.svg
[Code of Conduct]: https://docs.ansible.com/ansible/latest/community/code_of_conduct.html

[Apache v2 License Badge]: https://img.shields.io/badge/license-Apache%202.0-brightgreen.svg
[Apache v2 License]: https://github.com/ansible/awx_plugins.interfaces/blob/devel/LICENSE

[Ansible Matrix Badge]:
https://img.shields.io/badge/matrix-Ansible%20Community-blueviolet.svg?logo=matrix
[Ansible Matrix]: https://chat.ansible.im/#/welcome

[Ansible Discourse Badge]:
https://img.shields.io/badge/discourse-Ansible%20Community-yellowgreen.svg?logo=discourse
[Ansible Discourse]: https://forum.ansible.com
<!-- DO-NOT-REMOVE-docs-badges-END -->

[![RTD Build Status Badge]][RTD Docs]

[RTD Build Status Badge]:
https://readthedocs.org/projects/awx-plugins-interfaces/badge/?version=latest
[RTD Docs]: https://awx-plugins-interfaces.rtfd.io

# awx_plugins.interfaces

<!-- DO-NOT-REMOVE-docs-intro-START -->
Common interfaces for implementing plugins to AWX.
<!-- DO-NOT-REMOVE-docs-intro-END -->

## Features

This package provides standardized interfaces and utilities for developing AWX plugins, with a focus on:

- **HashiCorp Vault Integration**: Native Python interfaces for Vault secret plugins
- **Ctypes Go Bridge**: Direct integration with Go shared libraries without subprocess overhead  
- **Plugin Discovery**: Automatic discovery of installed plugin libraries
- **Type Safety**: Comprehensive type hints and protocol definitions
- **Error Handling**: Structured exception hierarchy for plugin operations

## HashiCorp Vault Plugin Support

AWX can now integrate with HashiCorp Vault secret plugins directly through Python using ctypes, eliminating the need for subprocess calls to Go binaries.

### Key Components

- **VaultPlugin Interface**: Protocol defining the standard Vault plugin contract
- **VaultPluginBase**: Abstract base class for implementing custom Vault plugins  
- **GoVaultPlugin**: Ready-to-use implementation for Go shared libraries
- **VaultConfig**: Configuration management for Vault connections
- **Error Types**: Structured exceptions for different failure modes

### Quick Start

```python
from awx_plugins.interfaces import api

# Configure Vault connection
config = api.VaultConfig(
    url="https://vault.example.com",
    auth_method="token",
    auth_config={"token": "hvs.your-token-here"}
)

# Use Go shared library plugin
with api.GoVaultPlugin("/path/to/vault_plugin.so") as plugin:
    # Authenticate
    plugin.authenticate(config)
    
    # Retrieve secrets
    request = api.VaultSecretRequest(path="secret/myapp")
    response = plugin.get_secret(request)
    
    print(f"Secret: {response.data}")
```

### Building Go Shared Libraries

Create a Go shared library that implements the required C-compatible interface:

```bash
go build -buildmode=c-shared -o vault_plugin.so vault_plugin.go
```

See the `examples/` directory for complete implementation examples.

## Installation

```bash
pip install awx_plugins.interfaces
```

## Examples

The `examples/` directory contains:

- `example_vault_plugin.go` - Complete Go implementation
- `example_usage.py` - Python usage demonstration
- `README.md` - Detailed setup and usage instructions
- `Makefile` - Build automation for Go shared library

## Documentation

For comprehensive documentation, visit [awx-plugins-interfaces.rtfd.io](https://awx-plugins-interfaces.rtfd.io).

## Development

This project uses modern Python development practices:

- **Type Hints**: Full type annotation coverage
- **Testing**: Comprehensive test suite with pytest
- **Code Quality**: Pre-commit hooks with multiple linters
- **CI/CD**: Automated testing and release workflows

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.
