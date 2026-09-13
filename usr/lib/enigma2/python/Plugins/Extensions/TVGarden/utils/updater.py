#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TV Garden Plugin - Updater Module

Update manager for TVGarden.

Repository:
    https://github.com/speedy005/TVGarden

Installer:
    https://raw.githubusercontent.com/speedy005/TVGarden/refs/heads/master/installer.sh
"""

import time
import shutil
import subprocess
import os

from re import sub, search
from os import makedirs
from os.path import join, exists
from urllib.request import urlopen, Request

from ..helpers import log
from .. import _, PLUGIN_VERSION, PLUGIN_PATH, USER_AGENT


class PluginUpdater:
    """TVGarden plugin update manager"""

    # ==========================================================
    # Repository information
    # ==========================================================

    REPO_OWNER = "speedy005"
    REPO_NAME = "TVGarden"
    REPO_BRANCH = "master"

    RAW_CONTENT = "https://raw.githubusercontent.com"

    INSTALLER_URL = (
        "%s/%s/%s/refs/heads/%s/installer.sh"
        % (
            RAW_CONTENT,
            REPO_OWNER,
            REPO_NAME,
            REPO_BRANCH
        )
    )

    REPO_URL = (
        "https://github.com/%s/%s"
        % (
            REPO_OWNER,
            REPO_NAME
        )
    )

    BACKUP_DIR = "/tmp/tvgarden_backup"

    INSTALLER_PATH = "/tmp/tvgarden-installer.sh"

    # ==========================================================
    # Init
    # ==========================================================

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
            "Installer URL: %s"
            % self.INSTALLER_URL,
            module="Updater"
        )

        try:
            if not exists(self.BACKUP_DIR):
                makedirs(
                    self.BACKUP_DIR,
                    mode=0o755
                )
        except Exception as e:
            log.error(
                "Could not create backup directory: %s"
                % e,
                module="Updater"
            )

    # ==========================================================
    # Get latest version
    # ==========================================================

    def get_latest_version(self):
        """Get latest version from installer.sh."""

        response = None

        try:
            log.debug(
                "Checking version from: %s"
                % self.INSTALLER_URL,
                module="Updater"
            )

            headers = {
                "User-Agent": self.user_agent
            }

            request = Request(
                self.INSTALLER_URL,
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
                "installer.sh downloaded successfully: %d bytes"
                % len(raw_content),
                module="Updater"
            )

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
                    content
                )

                if match:

                    version = match.group(1)

                    log.info(
                        "Found latest version: %s"
                        % version,
                        module="Updater"
                    )

                    return version

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
                    "Fallback found version: %s"
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
    # Compare versions
    # ==========================================================

    def compare_versions(self, v1, v2):
        """Compare version strings."""

        try:

            if v1 is None or v2 is None:
                return 0

            v1_clean = sub(
                r"[^\d.]",
                "",
                str(v1)
            )

            v2_clean = sub(
                r"[^\d.]",
                "",
                str(v2)
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

            for i in range(max_len):

                if v1_parts[i] > v2_parts[i]:
                    return 1

                if v1_parts[i] < v2_parts[i]:
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
    # Check update
    # ==========================================================

    def check_update(self, callback=None):
        """Check if a newer TVGarden version is available."""

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

            is_newer = (
                self.compare_versions(
                    latest,
                    self.current_version
                ) > 0
            )

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
        """Create backup and install latest TVGarden version."""

        log.info(
            "Starting TVGarden update process...",
            module="Updater"
        )

        success = False
        message = ""

        try:

            # --------------------------------------------------
            # Backup
            # --------------------------------------------------

            log.info(
                "Creating backup before update...",
                module="Updater"
            )

            if not self.create_backup():

                message = _(
                    "Failed to create backup. Update cancelled."
                )

                if callback:
                    callback(
                        False,
                        message
                    )

                return

            # --------------------------------------------------
            # Installer
            # --------------------------------------------------

            log.info(
                "Downloading and running TVGarden installer...",
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

                log.error(
                    "Installer failed. Restoring backup...",
                    module="Updater"
                )

                if self.restore_backup():

                    message = _(
                        "Update failed. Restored from backup."
                    )

                else:

                    message = _(
                        "Update failed and backup restore also failed!"
                    )

        except Exception as e:

            log.error(
                "Update process error: %s"
                % e,
                module="Updater"
            )

            try:
                self.restore_backup()
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
    # Execute installer
    # ==========================================================

    def download_and_run_installer(self):
        """
        Download installer.sh and execute it.

        Installer stdout/stderr is captured and written
        to the TVGarden log.
        """

        installer_path = self.INSTALLER_PATH

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
            # Remove old installer
            # --------------------------------------------------

            try:

                if exists(installer_path):
                    os.remove(installer_path)

            except Exception as e:

                log.warning(
                    "Could not remove old installer: %s"
                    % e,
                    module="Updater"
                )

            # --------------------------------------------------
            # Download installer
            # --------------------------------------------------

            cmd = (
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

            result = subprocess.call(
                cmd,
                shell=True
            )

            if result != 0:

                log.error(
                    "Installer download failed "
                    "(exit code: %d)"
                    % result,
                    module="Updater"
                )

                return False

            # --------------------------------------------------
            # Verify downloaded installer
            # --------------------------------------------------

            if not exists(installer_path):

                log.error(
                    "Installer file does not exist after download",
                    module="Updater"
                )

                return False

            try:

                with open(
                    installer_path,
                    "rb"
                ) as installer_file:

                    installer_data = installer_file.read()

            except Exception as e:

                log.error(
                    "Could not read installer: %s"
                    % e,
                    module="Updater"
                )

                return False

            installer_size = len(installer_data)

            if installer_size < 100:

                log.error(
                    "Downloaded installer is too small: %d bytes"
                    % installer_size,
                    module="Updater"
                )

                return False

            log.info(
                "Installer downloaded: %d bytes"
                % installer_size,
                module="Updater"
            )

            # --------------------------------------------------
            # Validate shell script
            # --------------------------------------------------

            header = installer_data[:512]

            if (
                b"#!/bin/bash" not in header
                and
                b"#!/bin/sh" not in header
            ):

                log.warning(
                    "Installer does not contain a valid shell "
                    "shebang",
                    module="Updater"
                )

            # --------------------------------------------------
            # Determine shell
            # --------------------------------------------------

            if exists("/bin/bash"):

                shell_bin = "/bin/bash"

                log.debug(
                    "Using installer interpreter: /bin/bash",
                    module="Updater"
                )

            elif exists("/usr/bin/bash"):

                shell_bin = "/usr/bin/bash"

                log.debug(
                    "Using installer interpreter: /usr/bin/bash",
                    module="Updater"
                )

            else:

                shell_bin = "/bin/sh"

                log.debug(
                    "bash not found, using /bin/sh",
                    module="Updater"
                )

            # --------------------------------------------------
            # Execute installer
            # --------------------------------------------------

            log.info(
                "Executing TVGarden installer...",
                module="Updater"
            )

            command = [
                shell_bin,
                installer_path
            ]

            log.debug(
                "Installer command: %s"
                % " ".join(command),
                module="Updater"
            )

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )

            # --------------------------------------------------
            # Capture installer output
            # --------------------------------------------------

            output_lines = []

            while True:

                line = process.stdout.readline()

                if not line:
                    break

                line = line.rstrip()

                if not line:
                    continue

                output_lines.append(line)

                # Write every installer line to TVGarden log
                log.info(
                    "[Installer] %s"
                    % line,
                    module="Updater"
                )

            process.stdout.close()

            return_code = process.wait()

            # --------------------------------------------------
            # Installer result
            # --------------------------------------------------

            if return_code == 0:

                log.info(
                    "TVGarden installer completed successfully",
                    module="Updater"
                )

                return True

            log.error(
                "TVGarden installer failed with exit code: %d"
                % return_code,
                module="Updater"
            )

            # --------------------------------------------------
            # Print useful summary
            # --------------------------------------------------

            if output_lines:

                log.error(
                    "Installer produced %d output lines"
                    % len(output_lines),
                    module="Updater"
                )

                # Last 10 lines are particularly useful
                last_lines = output_lines[-10:]

                for line in last_lines:

                    log.error(
                        "[Installer last] %s"
                        % line,
                        module="Updater"
                    )

            else:

                log.error(
                    "Installer produced no output",
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

                    os.remove(
                        installer_path
                    )

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
                "Creating backup to: %s"
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

            if exists(PLUGIN_PATH):

                shutil.rmtree(
                    PLUGIN_PATH
                )

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
    """Perform a TVGarden update."""

    updater = PluginUpdater()

    return updater.download_update(
        callback
    )
