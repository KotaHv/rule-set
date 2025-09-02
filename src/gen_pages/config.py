"""
Configuration for gen_pages package
"""

from pathlib import Path


class GenPagesConfig:
    """Configuration for gen_pages package"""

    def __init__(self):
        self.templates_dir = Path(__file__).parent / "templates"
        self.static_dir = Path(__file__).parent / "static"
        self.icons_dir = self.static_dir / "icons"

    @property
    def templates_path(self) -> Path:
        """Get templates directory path"""
        return self.templates_dir

    @property
    def static_path(self) -> Path:
        """Get static files directory path"""
        return self.static_dir

    @property
    def icons_path(self) -> Path:
        """Get icons directory path"""
        return self.icons_dir


# Global configuration instance
config = GenPagesConfig()
