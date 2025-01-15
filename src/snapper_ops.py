"""SnapperOps."""

import logging
import shlex
import subprocess
from pathlib import Path

import ops

from schemas import Confinement

logger = logging.getLogger(__name__)

SNAP_BINARY_PATH = Path("/usr/bin/snap")


class SnapperOps:
    """Track and perform operations regarding snapp packages."""

    def __init__(self, charm: ops.CharmBase):
        """Initialize the snapper ops."""
        self._charm = charm

    def _sys_exec(self, cmd: list[str]):
        """Execute a system command."""
        try:
            subprocess.call(cmd)
        except subprocess.CalledProcessError as exc:
            logger.error(f"Error executing command {shlex.join(cmd)} - {exc}")
            raise exc

    def install_snap(self, snap_name: str, channel: str, confinement: str):
        """Install a snap."""
        logger.debug(f"Installing snap {snap_name}")
        install_cmd = [str(SNAP_BINARY_PATH), "install", snap_name, "--channel", channel]
        if confinement == Confinement.classic:
            install_cmd.append("--classic")
        self._sys_exec(install_cmd)

    def stop_snap(self, snap_name: str, service_name: str| None = None):
        """Stop either all services or a certain servi e of a snap."""
        service = f"{snap_name}.{service_name}" if service_name else snap_name
        logger.debug(f"Stopping snap {service}")
        self._sys_exec([str(SNAP_BINARY_PATH), "stop", service])

    def remove_snap(self, snap_name: str):
        """Remove a snap."""
        logger.debug(f"Removing snap {snap_name}")
        self._sys_exec([str(SNAP_BINARY_PATH), "remove", snap_name])

    def refresh_snap(self, snap_name: str, channel: str, confinement: str):
        """Refresh a snap."""
        logger.debug(f"Refreshing snap {snap_name} to channel {channel} with confinement {confinement}")
        refresh_cmd = [str(SNAP_BINARY_PATH), "refresh", snap_name, "--channel", channel]
        if confinement == Confinement.classic:
            refresh_cmd.append("--classic")
        self._sys_exec(refresh_cmd)

    def config_snap(self, snap_name: str, config: dict[str, str]):
        """Configure a snap."""
        logger.debug(f"Configuring snap {snap_name} with {config}")
        for key, value in config.items():
            self._sys_exec([str(SNAP_BINARY_PATH), "set", snap_name, f"{key}={value}"])
