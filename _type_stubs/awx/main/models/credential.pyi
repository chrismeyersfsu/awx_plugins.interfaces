from typing import Callable

from awx_plugins.interfaces._temporary_private_credential_api import (  # noqa: WPS436
    Credential,
    GenericOptionalPrimitiveType,
)


class ManagedCredentialType:
    def __init__(
        self,
        namespace: str,
        name: str,
        kind: str,
        inputs: dict[str, list[dict[str, bool | str] | str]],
        injectors: dict[str, dict[str, str]] | None = None,
        managed: bool = False,
        custom_injector: Callable[[Credential, dict[str, GenericOptionalPrimitiveType], str], str | None] | None = None,
    ): ...
