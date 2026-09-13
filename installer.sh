#!/bin/bash

# =========================================================
# TV Garden Installer for Enigma2
# =========================================================
#
# Install:
# wget -q --no-check-certificate \
# "https://raw.githubusercontent.com/speedy005/TVGarden/refs/heads/master/installer.sh" \
# -O - | /bin/sh
#
# =========================================================

VERSION="0.0"

REPO_OWNER="speedy005"
REPO_NAME="TVGarden"
REPO_BRANCH="master"

REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/${REPO_BRANCH}.tar.gz"

TMPPATH="/tmp/TVGarden-install"
FILEPATH="/tmp/TVGarden-${REPO_BRANCH}.tar.gz"
EXTRACTPATH="${TMPPATH}/TVGarden-${REPO_BRANCH}"

echo ""
echo "========================================================="
echo "              TVGarden Installer"
echo "========================================================="
echo "TVGarden Version: $VERSION"
echo ""
echo "Changelog:"
echo "- Add youtube streaming on player"
echo "- Fix Problematic Channels"
echo ""
echo "Repository:"
echo "https://github.com/${REPO_OWNER}/${REPO_NAME}"
echo ""
echo "Branch: $REPO_BRANCH"
echo "========================================================="
echo ""

echo "Starting TVGarden installation..."

# =========================================================
# Plugin path
# =========================================================

if [ ! -d /usr/lib64 ]; then
    PLUGINPATH="/usr/lib/enigma2/python/Plugins/Extensions/TVGarden"
else
    PLUGINPATH="/usr/lib64/enigma2/python/Plugins/Extensions/TVGarden"
fi

echo "Plugin path: $PLUGINPATH"

# =========================================================
# Cleanup
# =========================================================

cleanup() {
    echo "Cleaning up temporary files..."

    [ -d "$TMPPATH" ] && rm -rf "$TMPPATH"
    [ -f "$FILEPATH" ] && rm -f "$FILEPATH"
    [ -d "/tmp/TVGarden-${REPO_BRANCH}" ] && rm -rf "/tmp/TVGarden-${REPO_BRANCH}"
}

# =========================================================
# Detect OS
# =========================================================

detect_os() {

    if [ -f /var/lib/dpkg/status ]; then

        OSTYPE="DreamOs"
        STATUS="/var/lib/dpkg/status"

    elif [ -f /etc/opkg/opkg.conf ] || [ -f /var/lib/opkg/status ]; then

        OSTYPE="OE"
        STATUS="/var/lib/opkg/status"

    else

        OSTYPE="Unknown"
        STATUS=""

    fi

    echo "Detected OS type: $OSTYPE"
}

detect_os

# =========================================================
# Start clean
# =========================================================

cleanup

mkdir -p "$TMPPATH"

if [ ! -d "$TMPPATH" ]; then
    echo "ERROR: Could not create temporary directory:"
    echo "$TMPPATH"
    exit 1
fi

# =========================================================
# Check wget
# =========================================================

if ! command -v wget >/dev/null 2>&1; then

    echo "wget not found."
    echo "Installing wget..."

    case "$OSTYPE" in

        DreamOs)

            if ! command -v apt-get >/dev/null 2>&1; then
                echo "ERROR: apt-get not available."
                exit 1
            fi

            apt-get update

            if ! apt-get install -y wget; then
                echo "ERROR: Failed to install wget."
                exit 1
            fi

            ;;

        OE)

            if ! command -v opkg >/dev/null 2>&1; then
                echo "ERROR: opkg not available."
                exit 1
            fi

            opkg update

            if ! opkg install wget; then
                echo "ERROR: Failed to install wget."
                exit 1
            fi

            ;;

        *)

            echo "ERROR: Unsupported OS type."
            exit 1

            ;;

    esac
fi

echo "wget: OK"

# =========================================================
# Detect Python
# =========================================================

if command -v python3 >/dev/null 2>&1; then

    PYTHON="PY3"
    PYTHON_BIN="python3"
    PACKAGE_SIX="python3-six"

    echo "Python3 detected: $(python3 --version 2>&1)"

elif command -v python >/dev/null 2>&1; then

    PYTHON_VERSION=$(python --version 2>&1)

    case "$PYTHON_VERSION" in

        "Python 3."*)

            PYTHON="PY3"
            PYTHON_BIN="python"
            PACKAGE_SIX="python3-six"

            ;;

        *)

            PYTHON="PY2"
            PYTHON_BIN="python"
            PACKAGE_SIX="python-six"

            ;;

    esac

    echo "Python detected: $PYTHON_VERSION"

else

    echo "ERROR: Python not found."
    exit 1

fi

# =========================================================
# Package installation helper
# =========================================================

install_pkg() {

    PKG="$1"

    if [ -z "$PKG" ]; then
        return 0
    fi

    if [ -n "$STATUS" ] && grep -qs "^Package: $PKG$" "$STATUS" 2>/dev/null; then

        echo "$PKG already installed"
        return 0

    fi

    echo "Installing package: $PKG"

    case "$OSTYPE" in

        DreamOs)

            if ! command -v apt-get >/dev/null 2>&1; then
                echo "WARNING: apt-get not available."
                return 1
            fi

            apt-get update >/dev/null 2>&1

            if ! apt-get install -y "$PKG"; then
                echo "WARNING: Could not install $PKG"
                return 1
            fi

            ;;

        OE)

            if ! command -v opkg >/dev/null 2>&1; then
                echo "WARNING: opkg not available."
                return 1
            fi

            opkg update >/dev/null 2>&1

            if ! opkg install "$PKG"; then
                echo "WARNING: Could not install $PKG"
                return 1
            fi

            ;;

        *)

            echo "WARNING: Cannot install $PKG on unknown OS."
            return 1

            ;;

    esac

    return 0
}

# =========================================================
# Python dependencies
# =========================================================

if [ "$PYTHON" = "PY3" ]; then

    echo "Checking python3-six..."
    install_pkg "$PACKAGE_SIX"

fi

# =========================================================
# Requests
# =========================================================

if [ "$OSTYPE" = "DreamOs" ]; then

    if command -v apt-get >/dev/null 2>&1; then

        echo "Checking Python requests..."

        if ! "$PYTHON_BIN" -c "import requests" >/dev/null 2>&1; then

            echo "Python requests not installed."

            if ! apt-get update >/dev/null 2>&1; then
                echo "WARNING: apt-get update failed."
            fi

            if [ "$PYTHON" = "PY3" ]; then
                install_pkg "python3-requests"
            else
                install_pkg "python-requests"
            fi

        else

            echo "Python requests: OK"

        fi

    fi

elif [ "$OSTYPE" = "OE" ]; then

    echo "Checking Python requests..."

    if ! "$PYTHON_BIN" -c "import requests" >/dev/null 2>&1; then

        if [ "$PYTHON" = "PY3" ]; then
            install_pkg "python3-requests"
        else
            install_pkg "python-requests"
        fi

    else

        echo "Python requests: OK"

    fi

fi

# =========================================================
# Multimedia packages
# =========================================================

if [ "$OSTYPE" = "OE" ]; then

    echo ""
    echo "Installing/checking multimedia packages..."

    for pkg in \
        ffmpeg \
        gstplayer \
        exteplayer3 \
        enigma2-plugin-systemplugins-serviceapp
    do

        install_pkg "$pkg"

    done

fi

# =========================================================
# Download TVGarden
# =========================================================

echo ""
echo "========================================================="
echo "Downloading TVGarden..."
echo "========================================================="
echo ""
echo "URL:"
echo "$REPO_URL"
echo ""

rm -f "$FILEPATH"

if ! wget --no-check-certificate \
    --timeout=30 \
    --tries=3 \
    "$REPO_URL" \
    -O "$FILEPATH"
then

    echo ""
    echo "ERROR: Failed to download TVGarden package!"
    echo "URL: $REPO_URL"

    cleanup
    exit 1

fi

# =========================================================
# Validate downloaded archive
# =========================================================

if [ ! -f "$FILEPATH" ]; then

    echo "ERROR: Downloaded archive does not exist."

    cleanup
    exit 1

fi

FILESIZE=$(wc -c < "$FILEPATH" 2>/dev/null)

echo ""
echo "Downloaded archive size: ${FILESIZE} bytes"

if [ -z "$FILESIZE" ] || [ "$FILESIZE" -lt 1024 ]; then

    echo "ERROR: Downloaded archive is too small."
    echo "Possible GitHub download failure."

    echo ""
    echo "Archive contents:"
    head -c 200 "$FILEPATH" 2>/dev/null
    echo ""

    cleanup
    exit 1

fi

# =========================================================
# Extract
# =========================================================

echo ""
echo "========================================================="
echo "Extracting package..."
echo "========================================================="
echo ""

if ! tar -xzf "$FILEPATH" -C "$TMPPATH"; then

    echo "ERROR: Failed to extract TVGarden package!"

    cleanup
    exit 1

fi

echo "Archive extracted successfully."

# =========================================================
# Show extracted structure
# =========================================================

echo ""
echo "Extracted directories:"
find "$TMPPATH" -maxdepth 3 -type d 2>/dev/null | head -30

# =========================================================
# Find plugin source
# =========================================================

echo ""
echo "========================================================="
echo "Searching for TVGarden plugin..."
echo "========================================================="

SOURCE_DIR=""

SEARCH_PATHS="
$TMPPATH/TVGarden-master/TVGarden
$TMPPATH/TVGarden-master
$TMPPATH/TVGarden-master/usr/lib/enigma2/python/Plugins/Extensions/TVGarden
$TMPPATH/TVGarden-master/usr/lib64/enigma2/python/Plugins/Extensions/TVGarden
"

for search_path in $SEARCH_PATHS
do

    if [ -d "$search_path" ] && [ -f "$search_path/plugin.py" ]; then

        SOURCE_DIR="$search_path"

        echo ""
        echo "Plugin source found:"
        echo "$SOURCE_DIR"

        break

    fi

done

# =========================================================
# Fallback search
# =========================================================

if [ -z "$SOURCE_DIR" ]; then

    echo ""
    echo "Normal plugin path not found."
    echo "Searching archive recursively..."

    FOUND_PLUGIN=$(find "$TMPPATH" \
        -type f \
        -name "plugin.py" \
        2>/dev/null | head -1)

    if [ -n "$FOUND_PLUGIN" ]; then

        SOURCE_DIR=$(dirname "$FOUND_PLUGIN")

        echo ""
        echo "Plugin found by recursive search:"
        echo "$SOURCE_DIR"

    fi

fi

# =========================================================
# Plugin source validation
# =========================================================

if [ -z "$SOURCE_DIR" ]; then

    echo ""
    echo "ERROR: Could not find TVGarden plugin files."
    echo ""
    echo "Python files found in archive:"

    find "$TMPPATH" \
        -type f \
        -name "*.py" \
        2>/dev/null | head -30

    echo ""

    echo "Directory structure:"
    find "$TMPPATH" \
        -maxdepth 5 \
        -type d \
        2>/dev/null | head -50

    cleanup
    exit 1

fi

# =========================================================
# Prepare plugin directory
# =========================================================

echo ""
echo "========================================================="
echo "Installing plugin files..."
echo "========================================================="

mkdir -p "$PLUGINPATH"

if [ ! -d "$PLUGINPATH" ]; then

    echo "ERROR: Could not create plugin directory:"
    echo "$PLUGINPATH"

    cleanup
    exit 1

fi

echo "Source:"
echo "$SOURCE_DIR"

echo ""
echo "Destination:"
echo "$PLUGINPATH"

# =========================================================
# Copy plugin
# =========================================================

echo ""
echo "Copying plugin files..."

if ! cp -a "$SOURCE_DIR"/. "$PLUGINPATH"/; then

    echo "ERROR: Failed to copy plugin files."

    echo ""
    echo "Source directory:"
    ls -la "$SOURCE_DIR" 2>/dev/null

    echo ""
    echo "Destination directory:"
    ls -la "$PLUGINPATH" 2>/dev/null

    cleanup
    exit 1

fi

# =========================================================
# Permissions
# =========================================================

echo ""
echo "Setting permissions..."

chmod -R 755 "$PLUGINPATH" 2>/dev/null

find "$PLUGINPATH" \
    -type f \
    -name "*.py" \
    -exec chmod 644 {} \; \
    2>/dev/null

find "$PLUGINPATH" \
    -type f \
    -name "*.sh" \
    -exec chmod 755 {} \; \
    2>/dev/null

# =========================================================
# Verify installation
# =========================================================

sync

echo ""
echo "========================================================="
echo "Verifying installation..."
echo "========================================================="

if [ ! -f "$PLUGINPATH/plugin.py" ]; then

    echo "ERROR: plugin.py is missing."
    echo ""
    echo "Installed directory:"
    ls -la "$PLUGINPATH" 2>/dev/null

    cleanup
    exit 1

fi

if [ ! -f "$PLUGINPATH/__init__.py" ]; then

    echo "ERROR: __init__.py is missing."
    echo ""
    echo "Installed directory:"
    ls -la "$PLUGINPATH" 2>/dev/null

    cleanup
    exit 1

fi

echo ""
echo "Plugin successfully installed."
echo ""
echo "Plugin path:"
echo "$PLUGINPATH"

echo ""
echo "Main files:"

ls -la \
    "$PLUGINPATH/plugin.py" \
    "$PLUGINPATH/__init__.py" \
    2>/dev/null

# =========================================================
# Cleanup
# =========================================================

cleanup

sync

# =========================================================
# Debug information
# =========================================================

FILE="/etc/image-version"

box_type=$(sed -n '1p' /etc/hostname 2>/dev/null || echo "Unknown")

distro_value="Unknown"
distro_version="Unknown"

if [ -r /etc/os-release ]; then

    distro_value=$(grep '^NAME=' /etc/os-release 2>/dev/null | cut -d'"' -f2)
    distro_version=$(grep '^VERSION_ID=' /etc/os-release 2>/dev/null | cut -d'"' -f2)

elif [ -r /etc/issue ]; then

    distro_value=$(head -n 1 /etc/issue 2>/dev/null | awk '{print $1}')
    distro_version=$(head -n 1 /etc/issue 2>/dev/null | awk '{print $2}')

elif [ -r /etc/vtiversion.info ]; then

    distro_value=$(head -n 1 /etc/vtiversion.info 2>/dev/null)

elif [ -r /etc/issue.net ]; then

    distro_value=$(head -n 1 /etc/issue.net 2>/dev/null | awk '{print $1}')
    distro_version=$(head -n 1 /etc/issue.net 2>/dev/null | awk '{print $2}')

fi

[ -z "$distro_value" ] && distro_value="Unknown"
[ -z "$distro_version" ] && distro_version="Unknown"

python_vers=$("$PYTHON_BIN" --version 2>&1)

# =========================================================
# Success
# =========================================================

echo ""
echo ""
echo "#########################################################"
echo "#               INSTALLED SUCCESSFULLY                  #"
echo "#                developed by LULULLA                   #"
echo "#               https://corvoboys.org                   #"
echo "#########################################################"
echo "#           your Device will RESTART Now                #"
echo "#########################################################"
echo "^^^^^^^^^^Debug information:"
echo "BOX MODEL: $box_type"
echo "OS SYSTEM: $OSTYPE"
echo "PYTHON: $python_vers"
echo "IMAGE NAME: ${distro_value:-Unknown}"
echo "IMAGE VERSION: ${distro_version:-Unknown}"
echo "PLUGIN PATH: $PLUGINPATH"
echo "PLUGIN VERSION: $VERSION"
echo "REPOSITORY: ${REPO_OWNER}/${REPO_NAME}"
echo "BRANCH: $REPO_BRANCH"
echo "#########################################################"
echo ""

exit 0
