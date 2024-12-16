"""Shared stubs from ``awx`` credential.

The hope is that it will be refactored into something more standardized.
"""

GenericOptionalPrimitiveType = bool | str | int | float | None  # noqa: WPS465
"""Generic type for input values."""

CredentialInputType = dict[str, GenericOptionalPrimitiveType]


class Credential:
    """Input supplied by the user.

    Satisfies :class:`~._temporary_private_api.ManagedCredentialType`
    inputs want(s).
    """

    def __init__(
        self: 'Credential',
        inputs: CredentialInputType | None = None,
    ) -> None:
        self._inputs: CredentialInputType = inputs or {}

    def get_input(
            self: 'Credential',
            field_name: str,
            default: GenericOptionalPrimitiveType = None,
    ) -> GenericOptionalPrimitiveType:
        """Get the user supplied value for a given field.

        Given the name of a field, return the user supplied value.

        :param field_name: Input key to check if a value was supplied.
        :param default: Value to return if a value was not supplied by
            the user
        :returns: True if user supplied a value, False otherwise.
        """
        return self._inputs.get(field_name, default)

    def has_input(self: 'Credential', field_name: str) -> bool:
        """Check if user supplied a value for a given field.

        Given the name of a field, return True of False as to if a value
        was provided for that field.

        :param field_name: Input key to check if a value was supplied.
        :returns: True if user supplied a value, False otherwise.
        """
        return self._inputs.get(field_name, None) not in {'', None}

    def get_input_keys(self: 'Credential') -> list[str]:
        """Get the list of keys that can be used for input.

        Get a list of keys that can be used to get values for.

        :returns: List of strings for which input can be gotten.
        """
        return list(self._inputs.keys())


__all__ = ()  # noqa: WPS410
