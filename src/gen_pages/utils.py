"""
Utility functions for gen_pages package
"""

from datetime import datetime, timezone
from pathlib import Path


def format_datetime(timestamp: float) -> str:
    """Format timestamp to human readable datetime string"""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def format_iso(timestamp: float) -> str:
    """Format timestamp to ISO format string"""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def format_name(name: str) -> str:
    """Format directory name for display"""
    if name == "geoip":
        return "GeoIP"
    return name.title()


def format_file_size(size: int) -> str:
    """Format file size for display"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"


def get_icon_path(icon_name: str, icon_prefix: str = "") -> str:
    """Get icon path with prefix"""
    return f"{icon_prefix}icons/{icon_name}.svg"


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if not"""
    path.mkdir(parents=True, exist_ok=True)


def is_valid_filename(filename: str) -> bool:
    """Check if filename is valid for web display"""
    return not filename.startswith(".") and filename not in ["icons", "index.html"]
