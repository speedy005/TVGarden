#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TV Garden Plugin - Updater Module

Updater for TVGarden.

Repository:
    https://github.com/speedy005/TVGarden

Installer:
    https://raw.githubusercontent.com/speedy005/TVGarden/refs/heads/master/installer.sh
"""

import time
import shutil
import subprocess

from re import sub, search
from os import makedirs
from os.path import join, exists
from urllib.request import urlopen, Request

from ..helpers import log
from .. import _, PLUGIN_VERSION, PLUGIN_PATH, USER_AGENT


class PluginUpdater:
    """TVGarden plugin update manager"""

    # ==========================================================
    # GitHub repository
    # ==========================================================

    REPO_OWNER = "speedy005"
    REPO_NAME = "TVGarden"
    REPO_BRANCH = "master"

    # GitHub raw content
    RAW_CONTENT = "https://raw.githubusercontent.com"

    # Installer
    INSTALLER_URL = (
        "%s/%s/%s/refs/heads/%s/installer.sh"
        % (
            RAW_CONTENT,
            REPO_OWNER,
            REPO_NAME,
            REPO_BRANCH
        )
    )

    # GitHub repository URL
    REPO_URL = (
        "https://github.com/%s/%s"
        % (
            REPO_OWNER,
            REPO_NAME
        )
    )

    # ==========================================================
    # Backup
    # ==========================================================

    BACKUP_DIR = "/tmp/tvgarden_backup"

    def __init__(self):
        self.current_version = str(PLUGIN_VERSION)
        self.user_agent = USER_AGENT
        self.backup_path = None

        log.debug(
            "PluginUpdater initialized - current version: %s"
            % self.current_version,
            module="Updater"
        )

        log.debug(
            "Repository: %s"
            % self.REPO_URL,
            module="Updater"
        )

        log.debug(
            "Installer: %s"
            % self.INSTALLER_URL,
            module="Updater"
        )

        # Create backup directory
        try:
            if not exists(self.BACKUP_DIR):
                makedirs(self.BACKUP_DIR, mode=0o755)
        except Exception as e:
            log.error(
                "Could not create backup directory: %s" % e,
                module="Updater"
            )

    # ==========================================================
    # Get latest version
    # ==========================================================

    def get_latest_version(self):
        """
        Get latest version from installer.sh.

        Expected installer format:

            version='2.7'

        or:

            version="2.7"
        """

        response = None

        try:
            installer_url = self.INSTALLER_URL

            log.debug(
                "Checking latest version from: %s"
                % installer_url,
                module="Updater"
            )

            headers = {
                "User-Agent": self.user_agent
            }

            request = Request(
                installer_url,
                headers=headers
            )

            response = urlopen(
                request,
                timeout=15
            )

            raw_content = response.read()

            try:
                content = raw_content.decode("utf-8")
            except UnicodeDecodeError:
                content = raw_content.decode(
                    "utf-8",
                    "ignore"
                )

            if not content:
                log.warning(
                    "installer.sh returned empty content",
                    module="Updater"
                )
                return None

            log.debug(
                "installer.sh downloaded successfully (%d bytes)"
                % len(raw_content),
                module="Updater"
            )

            # --------------------------------------------------
            # Version patterns
            # --------------------------------------------------

            patterns = [
                r"^\s*version\s*=\s*['\"]([0-9]+(?:\.[0-9]+)+)['\"]",
                r"^\s*VERSION\s*=\s*['\"]([0-9]+(?:\.[0-9]+)+)['\"]",
                r"version\s*=\s*['\"]([0-9]+(?:\.[0-9]+)+)['\"]",
                r"VERSION\s*=\s*['\"]([0-9]+(?:\.[0-9]+)+)['\"]",
                r"version\s*:\s*['\"]([0-9]+(?:\.[0-9]+)+)['\"]",
            ]

            for pattern in patterns:
                match = search(
                    pattern,
                    content,
                    flags=0
                )

                if match:
                    version = match.group(1)

                    log.info(
                        "Latest TVGarden version found: %s"
                        % version,
                        module="Updater"
                    )

                    return version

            # --------------------------------------------------
            # Fallback
            # --------------------------------------------------

            log.warning(
                "No explicit version pattern found in installer.sh",
                module="Updater"
            )

            fallback = search(
                r"\b([0-9]+\.[0-9]+(?:\.[0-9]+)*)\b",
                content
            )

            if fallback:
                version = fallback.group(1)

                log.info(
                    "Fallback version found: %s"
                    % version,
                    module="Updater"
                )

                return version

            log.warning(
                "Could not determine latest version",
                module="Updater"
            )

            return None

        except Exception as e:
            log.error(
                "Error getting latest version: %s"
                % e,
                module="Updater"
            )

            return None

        finally:
            if response:
                try:
                    response.close()
                except Exception:
                    pass

    # ==========================================================
    # Version comparison
    # ==========================================================

    def compare_versions(self, v1, v2):
        """
        Compare two version strings.

        Returns:
            1  -> v1 is newer
            0  -> versions are equal
           -1  -> v1 is older
        """

        try:
            if v1 is None or v2 is None:
                return 0

            v1 = str(v1)
            v2 = str(v2)

            # Keep only digits and dots
            v1_clean = sub(
                r"[^\d.]",
                "",
                v1
            )

            v2_clean = sub(
                r"[^\d.]",
                "",
                v2
            )

            if not v1_clean or not v2_clean:
                return 0

            v1_parts = [
                int(x)
                for x in v1_clean.split(".")
                if x != ""
            ]

            v2_parts = [
                int(x)
                for x in v2_clean.split(".")
                if x != ""
            ]

            if not v1_parts or not v2_parts:
                return 0

            # Pad with zeros
            max_len = max(
                len(v1_parts),
                len(v2_parts)
            )

            v1_parts += [0] * (
                max_len - len(v1_parts)
            )

            v2_parts += [0] * (
                max_len - len(v2_parts)
            )

            for index in range(max_len):

                if v1_parts[index] > v2_parts[index]:
                    return 1

                if v1_parts[index] < v2_parts[index]:
                    return -1

            return 0

        except Exception as e:
            log.error(
                "Version compare error: %s"
                % e,
                module="Updater"
            )

            return 0

    # ==========================================================
    # Check for update
    # ==========================================================

    def check_update(self, callback=None):
        """
        Check whether a newer TVGarden version is available.

        callback receives:

            True   -> update available
            False  -> already current
            None   -> check failed
        """

        log.debug(
            "PluginUpdater.check_update called",
            module="Updater"
        )

        try:
            latest = self.get_latest_version()

            log.debug(
                "Latest version: %s"
                % latest,
                module="Updater"
            )

            log.debug(
                "Current version: %s"
                % self.current_version,
                module="Updater"
            )

            if latest is None:
                log.warning(
                    "Could not get latest version",
                    module="Updater"
                )

                if callback:
                    callback(None)

                return

            comparison = self.compare_versions(
                latest,
                self.current_version
            )

            is_newer = comparison > 0

            log.info(
                "Version comparison: current=%s latest=%s update=%s"
                % (
                    self.current_version,
                    latest,
                    is_newer
                ),
                module="Updater"
            )

            if callback:
                callback(is_newer)

        except Exception as e:
            log.error(
                "Error in check_update: %s"
                % e,
                module="Updater"
            )

            if callback:
                callback(None)

    # ==========================================================
    # Download and install update
    # ==========================================================

    def download_update(self, callback=None):
        """
        Create backup, run installer and restore backup if
        the installer fails.
        """

        log.info(
            "Starting TVGarden update process...",
            module="Updater"
        )

        success = False
        message = ""

        try:

            # --------------------------------------------------
            # Step 1: Backup
            # --------------------------------------------------

            log.info(
                "Step 1: Creating plugin backup...",
                module="Updater"
            )

            if not self.create_backup():

                message = _(
                    "Failed to create backup. Update cancelled."
                )

                log.error(
                    "Update cancelled because backup failed",
                    module="Updater"
                )

                if callback:
                    callback(False, message)

                return

            # --------------------------------------------------
            # Step 2: Run installer
            # --------------------------------------------------

            log.info(
                "Step 2: Running TVGarden installer...",
                module="Updater"
            )

            if self.download_and_run_installer():

                success = True

                message = _(
                    "Update completed successfully!"
                )

                log.info(
                    "TVGarden update completed successfully",
                    module="Updater"
                )

            else:

                # --------------------------------------------------
                # Step 3: Restore backup
                # --------------------------------------------------

                log.error(
                    "Installer failed - attempting backup restore",
                    module="Updater"
                )

                if self.restore_backup():

                    message = _(
                        "Update failed. Restored from backup."
                    )

                    log.info(
                        "Backup restored successfully",
                        module="Updater"
                    )

                else:

                    message = _(
                        "Update failed and backup restore also failed!"
                    )

                    log.error(
                        "Backup restore failed",
                        module="Updater"
                    )

        except Exception as e:

            log.error(
                "Update process error: %s"
                % e,
                module="Updater"
            )

            # Try to restore backup
            try:
                if self.restore_backup():
                    log.info(
                        "Backup restored after exception",
                        module="Updater"
                    )
            except BaseException:
                pass

            message = _(
                "Update error: %s"
            ) % str(e)

        if callback:
            callback(
                success,
                message
            )

    # ==========================================================
    # Download and execute installer
    # ==========================================================

    def download_and_run_installer(self):
        """
        Download installer.sh from the configured repository
        and execute it with /bin/sh.

        Installer URL is always taken from INSTALLER_URL.
        """

        installer_path = "/tmp/tvgarden-installer.sh"

        try:

            log.info(
                "Downloading TVGarden installer...",
                module="Updater"
            )

            log.debug(
                "Installer URL: %s"
                % self.INSTALLER_URL,
                module="Updater"
            )

            # --------------------------------------------------
            # Download installer
            # --------------------------------------------------

            download_command = (
                'wget '
                '--no-check-certificate '
                '--timeout=30 '
                '--tries=3 '
                '-q '
                '"%s" '
                '-O "%s"'
                % (
                    self.INSTALLER_URL,
                    installer_path
                )
            )

            log.debug(
                "Downloading installer with wget",
                module="Updater"
            )

            result = subprocess.call(
                download_command,
                shell=True
            )

            if result != 0:

                log.error(
                    "Failed to download installer "
                    "(exit code: %d)"
                    % result,
                    module="Updater"
                )

                try:
                    if exists(installer_path):
                        shutil.rmtree(installer_path)
                except Exception:
                    pass

                return False

            # --------------------------------------------------
            # Verify downloaded file
            # --------------------------------------------------

            if not exists(installer_path):

                log.error(
                    "Installer file was not created",
                    module="Updater"
                )

                return False

            try:
                installer_size = 0

                with open(
                    installer_path,
                    "rb"
                ) as installer_file:

                    installer_data = installer_file.read()

                    installer_size = len(
                        installer_data
                    )

            except Exception as e:

                log.error(
                    "Could not read downloaded installer: %s"
                    % e,
                    module="Updater"
                )

                return False

            if installer_size < 100:

                log.error(
                    "Downloaded installer is too small: %d bytes"
                    % installer_size,
                    module="Updater"
                )

                return False

            log.info(
                "Installer downloaded successfully: %d bytes"
                % installer_size,
                module="Updater"
            )

            # --------------------------------------------------
            # Verify it looks like a shell script
            # --------------------------------------------------

            try:

                with open(
                    installer_path,
                    "rb"
                ) as installer_file:

                    first_bytes = installer_file.read(
                        512
                    )

                if (
                    b"#!/bin/sh" not in first_bytes
                    and
                    b"#!/bin/bash" not in first_bytes
                ):

                    log.warning(
                        "Downloaded installer does not contain "
                        "a shell shebang",
                        module="Updater"
                    )

            except Exception:
                pass

            # --------------------------------------------------
            # Execute installer
            # --------------------------------------------------

            log.info(
                "Executing TVGarden installer...",
                module="Updater"
            )

            command = (
                '/bin/sh "%s"'
                % installer_path
            )

            log.debug(
                "Executing installer: %s"
                % command,
                module="Updater"
            )

            result = subprocess.call(
                command,
                shell=True
            )

            # --------------------------------------------------
            # Result
            # --------------------------------------------------

            if result == 0:

                log.info(
                    "TVGarden installer completed successfully",
                    module="Updater"
                )

                return True

            log.error(
                "TVGarden installer failed with exit code: %d"
                % result,
                module="Updater"
            )

            return False

        except Exception as e:

            log.error(
                "Installer execution error: %s"
                % e,
                module="Updater"
            )

            return False

        finally:

            # --------------------------------------------------
            # Remove temporary installer
            # --------------------------------------------------

            try:

                if exists(installer_path):
                    import os
                    os.remove(installer_path)

                    log.debug(
                        "Temporary installer removed",
                        module="Updater"
                    )

            except Exception as e:

                log.warning(
                    "Could not remove temporary installer: %s"
                    % e,
                    module="Updater"
                )

    # ==========================================================
    # Create backup
    # ==========================================================

    def create_backup(self):
        """Create backup of current TVGarden plugin."""

        try:

            timestamp = time.strftime(
                "%Y%m%d_%H%M%S"
            )

            backup_name = (
                "backup_v%s_%s"
                % (
                    self.current_version,
                    timestamp
                )
            )

            self.backup_path = join(
                self.BACKUP_DIR,
                backup_name
            )

            if not exists(PLUGIN_PATH):

                log.error(
                    "Plugin path not found: %s"
                    % PLUGIN_PATH,
                    module="Updater"
                )

                return False

            log.info(
                "Creating backup: %s"
                % self.backup_path,
                module="Updater"
            )

            shutil.copytree(
                PLUGIN_PATH,
                self.backup_path
            )

            log.info(
                "Backup created successfully",
                module="Updater"
            )

            return True

        except Exception as e:

            log.error(
                "Backup failed: %s"
                % e,
                module="Updater"
            )

            return False

    # ==========================================================
    # Restore backup
    # ==========================================================

    def restore_backup(self):
        """Restore TVGarden plugin from backup."""

        try:

            if not self.backup_path:

                log.error(
                    "No backup path available",
                    module="Updater"
                )

                return False

            if not exists(self.backup_path):

                log.error(
                    "Backup not found: %s"
                    % self.backup_path,
                    module="Updater"
                )

                return False

            log.info(
                "Restoring backup: %s"
                % self.backup_path,
                module="Updater"
            )

            # Remove current plugin
            if exists(PLUGIN_PATH):

                log.debug(
                    "Removing current plugin: %s"
                    % PLUGIN_PATH,
                    module="Updater"
                )

                shutil.rmtree(
                    PLUGIN_PATH
                )

            # Restore backup
            shutil.copytree(
                self.backup_path,
                PLUGIN_PATH
            )

            log.info(
                "Backup restored successfully",
                module="Updater"
            )

            return True

        except Exception as e:

            log.error(
                "Restore failed: %s"
                % e,
                module="Updater"
            )

            return False


def perform_update(callback=None):
    """Perform TVGarden update."""

    updater = PluginUpdater()

    return updater.download_update(
        callback
    )

