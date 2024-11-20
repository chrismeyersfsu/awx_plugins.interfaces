# pylint: disable=fixme
"""Shared Django-coupled helpers from ``awx``.

The hope is that it will find a better home one day.
"""

try:  # noqa: WPS503
    # FIXME: delete Django imports from this project
    from django.conf import settings  # noqa: WPS433
except ImportError:
    def get_vmware_certificate_validation_setting() -> bool:
        """Retrieve VMware certificate validation platform toggle.

        This is a stub for when there is no Django in the environment.

        :returns: Whether the certificates should be validated.
        """
        return True
else:  # FIXME: eventually, this should not exist  # pragma: no cover
    def get_vmware_certificate_validation_setting() -> bool:  # noqa: WPS440
        """Retrieve VMware certificate validation platform toggle.

        :returns: Whether the certificates should be validated.
        """
        return settings.VMWARE_VALIDATE_CERTS


try:
    # FIXME: delete Django imports from this project
    # pylint: disable-next=unused-import
    from django.utils.translation import (  # noqa: WPS433
        gettext_lazy as gettext_lazy,
    )
except ImportError:  # FIXME: eventually, this should not exist
    def gettext_lazy(message: str) -> str:  # noqa: WPS440
        """Emulate a Django-imported lazy translator.

        :param message: Translatable string.
        :returns: Whatever's been passed in.
        """
        return message


try:
    # FIXME: delete Django imports from this project
    # pylint: disable-next=unused-import
    from django.utils.translation import (  # noqa: WPS433
        gettext_noop as gettext_noop,
    )
except ImportError:  # FIXME: eventually, this should not exist
    def gettext_noop(message: str) -> str:  # noqa: WPS440
        """Emulate a Django-imported no-op.

        :param message: Translatable string.
        :returns: Whatever's been passed in.
        """
        return message


__all__ = ()  # noqa: WPS410
