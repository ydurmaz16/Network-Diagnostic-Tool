import sys


def current_os() -> str:
    """Return 'windows', 'macos' or 'linux'."""
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"
