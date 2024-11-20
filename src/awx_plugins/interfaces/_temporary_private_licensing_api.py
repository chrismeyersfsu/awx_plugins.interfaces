"""Shared runtime detection from ``awx``.

The hope is that it will find a better home one day.
"""

import functools
import pathlib


__all__ = ()  # noqa: WPS410


@functools.cache  # type: ignore[misc]
def detect_server_product_name() -> str:
    """Compute the official runtime name.

    :returns: Runtime name.
    """
    custom_version_file_present = pathlib.Path(
        '/var/lib/awx/.tower_version',
    ).exists()
    return (
        'Red Hat Ansible Automation Platform' if custom_version_file_present
        else 'AWX'
    )
