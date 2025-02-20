# pylint: disable=fixme
"""Shared stubs from ``awx`` managed credential type.

The hope is that it will be refactored into something more standardized.
"""


try:
    # pylint: disable-next=unused-import
    from awx.main.models.credential import (  # noqa: WPS433
        ManagedCredentialType as ManagedCredentialType,
    )
except ImportError:  # FIXME: eventually, this should not exist
    from dataclasses import dataclass  # noqa: WPS433

    @dataclass(frozen=True)
    class ManagedCredentialType:  # type: ignore[no-redef]  # noqa: WPS440
        """Managed credential type stub."""

        namespace: str
        """Plugin namespace."""

        name: str
        """Plugin name within the namespace."""

        kind: str
        """Plugin category."""

        inputs: dict[str, list[dict[str, bool | str] | str]]
        """UI input fields schema."""

        injectors: dict[str, dict[str, str]] | None = None
        """Injector hook parameters."""

        managed: bool = False
        """Flag for whether this plugin instance is managed."""


__all__ = ()  # noqa: WPS410
