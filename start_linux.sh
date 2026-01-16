#!/bin/bash
# Chaos Foundry Unified Publishing Service - Linux Launcher

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "Starting Unified Publisher..."

# Ensure python3 is available
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Please install Python 3."
    exit 1
fi

# Check if venv exists (or create it)
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Dependency/version check
echo "Checking dependency versions..."
python - <<'PY'
import sys
from importlib import metadata

try:
    from packaging.requirements import Requirement
except Exception:
    print("Missing packaging; reinstalling dependencies.")
    sys.exit(1)

def iter_requirements(path):
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
            yield line

needs = []
for req_line in iter_requirements("requirements.txt"):
    try:
        req = Requirement(req_line)
    except Exception:
        needs.append(req_line)
        continue
    try:
        installed = metadata.version(req.name)
    except metadata.PackageNotFoundError:
        needs.append(f"{req.name} (missing)")
        continue
    if req.specifier and not req.specifier.contains(installed, prereleases=True):
        needs.append(f"{req.name} (installed {installed}, requires {req.specifier})")

if needs:
    print("Dependency updates required:")
    for item in needs:
        print(f" - {item}")
    sys.exit(1)

print("Dependencies look up-to-date.")
PY

if [ $? -ne 0 ]; then
    echo "Installing/updating dependencies..."
    pip install -r requirements.txt --upgrade
fi

# Set Qt environment variables for NVIDIA + Wayland compatibility
export QT_QPA_PLATFORM=wayland
export QT_WAYLAND_DISABLE_WINDOWDECORATION=0
# Fix NVIDIA/Wayland rendering issues
export QTWEBENGINE_CHROMIUM_FLAGS="--enable-gpu-rasterization --disable-gpu --enable-software-rasterization --disable-web-security --disable-features=VizDisplayCompositor"
export EGL_PLATFORM=wayland
export __GLX_VENDOR_LIBRARY_NAME=nvidia

# Run the application
echo "Launching Unified Publisher..."
echo "Note: Running in software rendering mode to fix NVIDIA Wayland issues."
python -m publisherlogic.main
