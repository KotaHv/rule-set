"""
Core services for generating HTML pages
"""

import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .config import config
from .models import DirNode, FileNode, PathTree, PathInfo
from .utils import (
    format_datetime,
    format_iso,
    format_name,
    format_file_size,
    is_valid_filename,
)


class PageGenerator:
    """Main class for generating HTML pages"""

    def __init__(self, rule_set_path: Path):
        self.rule_set_path = rule_set_path
        self.templates_dir = config.templates_path
        self.icons_dir = config.icons_path

        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self.path_tree = PathTree(
            root=DirNode(
                info=PathInfo(
                    name=rule_set_path.name,
                    size=0,
                    mtime=0,
                    path=rule_set_path,
                ),
                parent=None,
            )
        )
        self._build_tree(self.path_tree.root)
        self._copy_icons()

    def _build_tree(self, node: DirNode):
        """Build the file system tree structure"""
        for child in node.info.path.iterdir():
            if not is_valid_filename(child.name):
                continue
            if child.is_dir():
                child_node = DirNode(
                    info=PathInfo(name=child.name, size=0, mtime=0, path=child),
                    parent=node,
                )
                self._build_tree(child_node)
            else:
                stat = child.stat()
                child_node = FileNode(
                    info=PathInfo(
                        name=child.name,
                        size=stat.st_size,
                        mtime=stat.st_mtime,
                        path=child,
                    ),
                    parent=node,
                )
            node.children.append(child_node)
            if child_node.info.mtime > node.info.mtime:
                node.info.mtime = child_node.info.mtime

    def _copy_icons(self):
        """Copy icons from package icons directory to rule-set directory"""
        target_icons_dir = self.rule_set_path / "icons"

        if not self.icons_dir.exists():
            print(f"Warning: {self.icons_dir} directory not found")
            return

        # Create target directory
        target_icons_dir.mkdir(exist_ok=True)

        # Copy all icon files
        for icon_file in self.icons_dir.iterdir():
            if icon_file.is_file() and not icon_file.name.startswith("."):
                shutil.copy2(icon_file, target_icons_dir)
                print(f"Copied: {icon_file.name} to {target_icons_dir}")

    def _get_icon_data(self, icon_prefix: str = "") -> dict:
        """Get icon data for templates"""
        return {
            "clash": f"""<img src="{icon_prefix}icons/clash.svg" alt="Clash" class="w-8 h-8">""",
            "surge": f"""<img src="{icon_prefix}icons/surge.svg" alt="Surge" class="w-8 h-8">""",
            "sing-box": f"""<img src="{icon_prefix}icons/sing-box.svg" alt="Sing-Box" class="w-8 h-8">""",
            "loon": f"""<img src="{icon_prefix}icons/loon.svg" alt="Loon" class="w-8 h-8">""",
            "egern": f"""<img src="{icon_prefix}icons/egern.svg" alt="Egern" class="w-8 h-8">""",
            "geoip": """<svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            </svg>""",
        }

    def _get_directory_icon_data(self, icon_prefix: str = "") -> dict:
        """Get icon data for directory templates"""
        return {
            "clash": f"""<img src="{icon_prefix}icons/clash.svg" alt="Clash" class="w-6 h-6">""",
            "surge": f"""<img src="{icon_prefix}icons/surge.svg" alt="Surge" class="w-6 h-6">""",
            "sing-box": f"""<img src="{icon_prefix}icons/sing-box.svg" alt="Sing-Box" class="w-6 h-6">""",
            "loon": f"""<img src="{icon_prefix}icons/loon.svg" alt="Loon" class="w-6 h-6">""",
            "egern": f"""<img src="{icon_prefix}icons/egern.svg" alt="Egern" class="w-6 h-6">""",
            "geoip": """<svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            </svg>""",
        }

    def generate_root_index(self) -> str:
        """Generate root index.html content using Jinja2 template"""
        template = self.env.get_template("root_index.html")

        latest_update_time = self.path_tree.root.info.mtime
        icons = self._get_icon_data()

        context = {
            "latest_update_time": latest_update_time,
            "icons": icons,
            "directories": [
                child
                for child in self.path_tree.root.children
                if isinstance(child, DirNode)
            ],
            "format_datetime": format_datetime,
            "format_iso": format_iso,
            "format_name": format_name,
            "enumerate": enumerate,
        }

        return template.render(context)

    def generate_directory_index(self, node: DirNode) -> str:
        """Generate index.html content for a directory using Jinja2 template"""
        template = self.env.get_template("directory_index.html")

        dirs: list[DirNode] = []
        files: list[FileNode] = []
        for child in node.children:
            if isinstance(child, DirNode):
                dirs.append(child)
            else:
                files.append(child)

        parent = node
        icon_depth = 0
        app_name = None
        while parent != self.path_tree.root:
            icon_depth += 1
            app_name = parent.info.name
            parent = parent.parent

        icon_prefix = "../" * icon_depth
        icons = self._get_directory_icon_data(icon_prefix)

        context = {
            "node": node,
            "directories": dirs,
            "files": files,
            "icons": icons,
            "app_name": app_name,
            "format_datetime": format_datetime,
            "format_iso": format_iso,
            "format_name": format_name,
            "format_file_size": format_file_size,
        }

        return template.render(context)

    def generate_all_indexes(self):
        """Generate index.html files for all directories"""
        if not self.rule_set_path.exists():
            print(f"Error: {self.rule_set_path} directory not found")
            return

        # Generate root index
        root_html = self.generate_root_index()
        with open(self.rule_set_path / "index.html", "w", encoding="utf-8") as f:
            f.write(root_html)
        print(f"Generated: {self.rule_set_path}/index.html")

        dirs = [
            child
            for child in self.path_tree.root.children
            if isinstance(child, DirNode)
        ]

        while dirs:
            dir_node = dirs.pop()
            html_content = self.generate_directory_index(dir_node)
            with open(dir_node.info.path / "index.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"Generated: {dir_node.info.path}/index.html")
            dirs.extend(
                child for child in dir_node.children if isinstance(child, DirNode)
            )
