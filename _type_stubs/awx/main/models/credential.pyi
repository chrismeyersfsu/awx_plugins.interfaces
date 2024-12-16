from typing import Callable

from awx_plugins.interfaces._temporary_private_api import (  # noqa: WPS436
    EnvVarsType,
    InjectorDefinitionType,
    InputDefinitionType,
)
from awx_plugins.interfaces._temporary_private_credential_api import (  # noqa: WPS436
    Credential,
)


class ManagedCredentialType:
    namespace: str
    name: str
    kind: str
    inputs: InputDefinitionType
    injectors: InjectorDefinitionType = None
    managed: bool = False
    custom_injectors: Callable[
        [
            Credential,
            EnvVarsType, str,
        ], str | None,
    ] | None = None

    def __init__(
        self,
        namespace: str,
        name: str,
        kind: str,
        inputs: InputDefinitionType,
        injectors: InjectorDefinitionType = None,
        managed: bool = False,
        custom_injectors: Callable[['Credential', EnvVarsType, str], str | None] | None = None,
    ): ...
