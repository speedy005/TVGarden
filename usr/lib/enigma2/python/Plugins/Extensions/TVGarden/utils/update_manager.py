#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TV Garden Plugin - Update Manager

Centralized update functions using PluginUpdater.
"""

from Screens.MessageBox import MessageBox

from .updater import PluginUpdater
from ..helpers import log
from .. import _


class UpdateManager:
    """Centralized update manager using PluginUpdater."""

    # ==========================================================
    # Check for updates
    # ==========================================================

    @staticmethod
    def check_for_updates(session, status_label=None):
        """Check whether a newer TVGarden version is available."""

        log.debug(
            "UpdateManager.check_for_updates called",
            module="UpdateManager"
        )

        if status_label:
            status_label.setText(
                _("Checking for updates...")
            )

        try:

            updater = PluginUpdater()

            log.debug(
                "PluginUpdater created successfully",
                module="UpdateManager"
            )

            def update_callback(result):

                log.debug(
                    "Update check callback result: %s"
                    % result,
                    module="UpdateManager"
                )

                # --------------------------------------------------
                # Error
                # --------------------------------------------------

                if result is None:

                    if status_label:
                        status_label.setText(
                            _("Update check failed")
                        )

                    session.open(
                        MessageBox,
                        _(
                            "Could not check for updates.\n\n"
                            "Please check your internet connection."
                        ),
                        MessageBox.TYPE_ERROR
                    )

                    return

                # --------------------------------------------------
                # Update available
                # --------------------------------------------------

                if result:

                    if status_label:
                        status_label.setText(
                            _("Update available!")
                        )

                    UpdateManager.ask_to_update(
                        session,
                        status_label,
                        updater
                    )

                    return

                # --------------------------------------------------
                # Already up to date
                # --------------------------------------------------

                if status_label:
                    status_label.setText(
                        _("Plugin is up to date")
                    )

                session.open(
                    MessageBox,
                    _(
                        "You have the latest version "
                        "of TVGarden."
                    ),
                    MessageBox.TYPE_INFO
                )

            log.debug(
                "Calling PluginUpdater.check_update()",
                module="UpdateManager"
            )

            updater.check_update(
                update_callback
            )

        except Exception as e:

            log.error(
                "Error in check_for_updates: %s"
                % e,
                module="UpdateManager"
            )

            if status_label:
                status_label.setText(
                    _("Update check error")
                )

            session.open(
                MessageBox,
                _(
                    "Could not check for updates:\n\n%s"
                ) % str(e),
                MessageBox.TYPE_ERROR
            )

    # ==========================================================
    # Ask user
    # ==========================================================

    @staticmethod
    def ask_to_update(
        session,
        status_label=None,
        updater=None
    ):
        """Ask the user whether the update should be installed."""

        log.debug(
            "ask_to_update called",
            module="UpdateManager"
        )

        if updater is None:
            updater = PluginUpdater()

        def update_confirmed(result):

            log.debug(
                "User update confirmation: %s"
                % result,
                module="UpdateManager"
            )

            if result:

                UpdateManager.perform_update(
                    session,
                    status_label,
                    updater
                )

            else:

                log.info(
                    "User cancelled update",
                    module="UpdateManager"
                )

                if status_label:
                    status_label.setText(
                        _("Update cancelled")
                    )

        message = _(
            "A new version of TVGarden is available!\n\n"
            "Do you want to update now?\n\n"
            "A backup will be created automatically."
        )

        session.openWithCallback(
            update_confirmed,
            MessageBox,
            message,
            MessageBox.TYPE_YESNO
        )

    # ==========================================================
    # Perform update
    # ==========================================================

    @staticmethod
    def perform_update(
        session,
        status_label=None,
        updater=None
    ):
        """Perform the TVGarden update."""

        log.debug(
            "UpdateManager.perform_update called",
            module="UpdateManager"
        )

        if updater is None:
            updater = PluginUpdater()

        if status_label:
            status_label.setText(
                _("Updating plugin... Please wait")
            )

        def update_progress(
            success,
            message
        ):

            log.debug(
                "Update result: success=%s, message=%s"
                % (
                    success,
                    message
                ),
                module="UpdateManager"
            )

            # --------------------------------------------------
            # Update successful
            # --------------------------------------------------

            if success:

                log.info(
                    "TVGarden update successful",
                    module="UpdateManager"
                )

                if status_label:
                    status_label.setText(
                        _("Update successful!")
                    )

                restart_message = _(
                    "%s\n\n"
                    "Restart Enigma2 now for the "
                    "changes to take effect?"
                ) % message

                session.openWithCallback(
                    lambda result:
                    UpdateManager.restart_enigma2(
                        session,
                        result
                    ),
                    MessageBox,
                    restart_message,
                    MessageBox.TYPE_YESNO
                )

                return

            # --------------------------------------------------
            # Update failed
            # --------------------------------------------------

            log.error(
                "TVGarden update failed: %s"
                % message,
                module="UpdateManager"
            )

            if status_label:
                status_label.setText(
                    _("Update failed")
                )

            session.open(
                MessageBox,
                message,
                MessageBox.TYPE_ERROR
            )

        log.debug(
            "Starting PluginUpdater.download_update()",
            module="UpdateManager"
        )

        updater.download_update(
            update_progress
        )

    # ==========================================================
    # Restart Enigma2
    # ==========================================================

    @staticmethod
    def restart_enigma2(
        session,
        result
    ):
        """Restart Enigma2 if the user confirms."""

        log.debug(
            "Restart Enigma2 confirmation: %s"
            % result,
            module="UpdateManager"
        )

        if not result:

            log.info(
                "User chose not to restart Enigma2",
                module="UpdateManager"
            )

            return

        try:

            log.info(
                "Restarting Enigma2...",
                module="UpdateManager"
            )

            from enigma import quitMainloop

            # 3 = restart Enigma2 GUI
            quitMainloop(3)

        except Exception as e:

            log.error(
                "Failed to restart Enigma2: %s"
                % e,
                module="UpdateManager"
            )

            try:

                session.open(
                    MessageBox,
                    _(
                        "The update was installed successfully, "
                        "but Enigma2 could not be restarted "
                        "automatically.\n\n"
                        "Please restart Enigma2 manually."
                    ),
                    MessageBox.TYPE_INFO
                )

            except Exception as message_error:

                log.error(
                    "Could not show restart error: %s"
                    % message_error,
                    module="UpdateManager"
                )

