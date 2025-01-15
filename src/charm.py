#!/usr/bin/env python3
# Copyright 2025 Matheus Tosta
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Snapper charm."""

import logging
from typing import Any

import ops
import yaml

from snapper_ops import SnapperOps, SNAP_BINARY_PATH
from schemas import Snaps

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)


class SnapperCharm(ops.CharmBase):
    """Orchestrate the charm ops."""

    _stored = ops.framework.StoredState()

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)

        self._stored.set_default(installed=False)
        self._stored.set_default(config_available=False)
        self._stored.set_default(snaps={})
        self._stored.set_default(first_run=True)

        self.snapper_ops = SnapperOps(self)

        event_handler_bindings = {
            self.on.install: self._on_install,
            self.on.start: self._on_start,
            self.on.config_changed: self._on_config_changed,
            self.on.stop: self._on_stop,
            self.on.remove: self._on_remove,
        }
        for event, handler in event_handler_bindings.items():
            self.framework.observe(event, handler)

    def _on_install(self, event: ops.InstallEvent) -> None:
        """Handle the install event."""
        if not SNAP_BINARY_PATH.exists():
            logger.error(f"{SNAP_BINARY_PATH} not found.")
            self.unit.status = ops.BlockedStatus(f"Snapper requires the snap binary to be accessible at {SNAP_BINARY_PATH}.")
            event.defer()
            return

        if self._stored.config_available is False:
            logger.debug("Config not available yet.")
            event.defer()
            return

        assert isinstance(self._stored.snaps, dict)

        for snap in self._stored.snaps.get("snaps", []):
            snap_name = snap.get("name")
            assert isinstance(snap_name, str)

            snap_channel = snap.get("channel")
            assert isinstance(snap_channel, str)

            snap_confinement = snap.get("confinement")
            assert isinstance(snap_confinement, str)

            self.snapper_ops.install_snap(snap_name, snap_channel, snap_confinement)

        self._stored.installed = True

    def _on_start(self, event: ops.StartEvent) -> None:
        """Handle the start event."""
        if self._stored.installed is True and self._stored.config_available is True:
            logger.debug("Snaps are installed.")
            self.unit.status = ops.ActiveStatus("Snaps are installed")
        else:
            logger.debug("Snaps are not installed yet or config is not available.")
            event.defer()
            return

    def _on_config_changed(self, event: ops.ConfigChangedEvent) -> None:
        """Handle the config changed event.

        In the first run, the config is stored in the charm's state. In the next runs,
        the config is validated and the diff between the current snaps and the ones in the
        config is calculated. The charm then installs, removes, or refreshes the snaps
        accordingly.

        Except in the first run, the configurations are applied to the snaps.
        """
        raw_snaps = self.model.config.get("snaps")
        assert isinstance(raw_snaps, str)

        snaps_dict = yaml.safe_load(raw_snaps)

        try:
            Snaps(**snaps_dict)  # validate the config
        except ValueError as exc:
            logger.error(f"Invalid config: {exc}")
            self.unit.status = ops.BlockedStatus(f"Invalid config in `snaps`")
            event.defer()
            return

        if self._stored.first_run is True:
            self._stored.snaps = snaps_dict
            self._stored.config_available = True
            self._stored.first_run = False
            event.defer()
            return

        if self._stored.installed is False:
            logger.debug("Snaps are not installed yet. Deferring.")
            event.defer()
            return

        current_snaps = self._stored.snaps
        assert isinstance(current_snaps, dict)

        snaps = current_snaps.get("snaps", [])
        installed_snaps = snaps_dict.get("snaps", [])

        installed_snap_names: list[str] = [snap.get("name") for snap in installed_snaps]
        current_snap_names: list[str] = [snap.get("name") for snap in snaps]

        snaps_to_install = [snap for snap in installed_snaps if snap.get("name") not in current_snap_names]
        snaps_to_remove = [snap for snap in snaps if snap.get("name") not in installed_snap_names]
        snaps_to_refresh = [snap for snap in installed_snaps if snap.get("name") in current_snap_names]

        for snap in snaps_to_install:
            snap_name = snap.get("name")
            assert isinstance(snap_name, str)

            snap_channel = snap.get("channel")
            assert isinstance(snap_channel, str)

            snap_confinement = snap.get("confinement")
            assert isinstance(snap_confinement, str)

            self.snapper_ops.install_snap(snap_name, snap_channel, snap_confinement)
    
        for snap in snaps_to_remove:
            snap_name = snap.get("name")
            assert isinstance(snap_name, str)
            self.snapper_ops.remove_snap(snap_name)
    
        for snap in snaps_to_refresh:
            snap_name = snap.get("name")
            assert isinstance(snap_name, str)

            snap_channel = snap.get("channel")
            assert isinstance(snap_channel, str)

            snap_confinement = snap.get("confinement")
            assert isinstance(snap_confinement, str)

            self.snapper_ops.refresh_snap(snap_name, snap_channel, snap_confinement)

        self._stored.snaps = snaps_dict

        # apply configurations
        for snap in installed_snaps:
            snap_name = snap.get("name")
            assert isinstance(snap_name, str)

            snap_config: dict[Any, Any] | None = snap.get("config")
            if snap_config:
                assert isinstance(snap_config, dict)
                self.snapper_ops.config_snap(snap_name, snap_config)

    def _on_stop(self, event: ops.StopEvent) -> None:
        """Handle the stop event."""
        # stop all snaps
        stored_snaps = self._stored.snaps
        assert isinstance(stored_snaps, dict)
        snaps = stored_snaps.get("snaps", [])
        for snap in snaps:
            snap_name = snap.get("name")
            assert isinstance(snap_name, str)
            self.snapper_ops.stop_snap(snap_name)

    def _on_remove(self, event: ops.RemoveEvent) -> None:
        """Handle the remove event."""
        # remove all snaps
        stored_snaps = self._stored.snaps
        assert isinstance(stored_snaps, dict)
        snaps = stored_snaps.get("snaps", [])
        for snap in snaps:
            snap_name = snap.get("name")
            assert isinstance(snap_name, str)
            self.snapper_ops.remove_snap(snap_name)


if __name__ == "__main__":  # pragma: nocover
    ops.main(SnapperCharm)  # type: ignore
