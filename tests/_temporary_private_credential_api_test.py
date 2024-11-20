"""Tests for the temporarily hosted private credential structure."""

import pytest

from awx_plugins.interfaces._temporary_private_credential_api import (
    Credential,
    GenericOptionalPrimitiveType,
)


def test_credential_instantiation() -> None:
    """Check that credential type can be instantiated."""
    assert Credential()


@pytest.mark.parametrize(
    ('inputs', 'key', 'expected'),
    (
        pytest.param({'foo': 'bar'}, 'foo', 'bar', id='key-present'),
        pytest.param({'foo1': 'bar1'}, 'baz', None, id='key-missing'),
    ),
)
def test_credential_get_input(
        inputs: dict[str, GenericOptionalPrimitiveType],
        key: str,
        expected: str,
) -> None:
    """Check that get_input operates on the dict we provided."""
    assert Credential(inputs=inputs).get_input(key) == expected


@pytest.mark.parametrize(
    ('inputs', 'key', 'expected'),
    (
        pytest.param(
            {'foo2': 'bar2'},
            'foo2',
            True,  # noqa: WPS425
            id='key-present',
        ),
        pytest.param(
            {'foo3': 'bar3'},
            'baz',
            False,  # noqa: WPS425
            id='key-missing',
        ),
    ),
)
def test_credential_has_input(
        inputs: dict[str, GenericOptionalPrimitiveType],
        key: str,
        expected: bool,
) -> None:
    """Check that has_input behaves like dict in operator."""
    assert Credential(inputs=inputs).has_input(key) is expected
