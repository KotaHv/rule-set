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


config = GenPagesConfig()
