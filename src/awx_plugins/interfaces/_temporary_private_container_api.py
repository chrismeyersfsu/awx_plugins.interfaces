"""Shared container path mapping from ``awx``.

The hope is that it will find a better home one day.
"""

import os
import pathlib


__all__ = ()  # noqa: WPS410


CONTAINER_ROOT = '/runner'
"""The root of the private data directory as seen from inside of the container
running a job."""


def get_incontainer_path(
        path: os.PathLike[str] | str,
        private_data_dir: os.PathLike[str] | str,
) -> str:
    """Produce an in-container path string.

    Given a path inside of the host machine filesystem, this returns the
    expected path which would be observed by the job running inside of the EE
    container.
    This only handles the volume mount from ``private_data_dir``
    to ``/runner``.

    :param path: Host-side path view.
    :param private_data_dir: Host-side directory mounted to ``/runner``
                             in container.

    :raises RuntimeError: If the private data directory is not absolute or does
                          not contain the path.

    :returns: In-container path.
    """
    if not os.path.isabs(private_data_dir):
        raise RuntimeError('The private_data_dir path must be absolute')

    container_root = pathlib.Path(CONTAINER_ROOT)

    # NOTE: Due to how `tempfile.mkstemp()` works, we are probably passed
    # NOTE: a resolved `path`, but unresolved `private_data_dir``.
    resolved_path = pathlib.Path(path).resolve()
    resolved_pdd = pathlib.Path(private_data_dir).resolve()

    try:
        return str(container_root / resolved_path.relative_to(resolved_pdd))
    except ValueError as val_err:
        raise RuntimeError(
            f'Cannot convert path {resolved_path !s} '
            f'unless it is a subdir of {resolved_pdd !s}',
        ) from val_err
