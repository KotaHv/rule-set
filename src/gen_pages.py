#!/usr/bin/env python3
"""
Generate index.html files for GitHub Pages directory browsing
"""

import pathlib
import shutil
from datetime import datetime


from pydantic import BaseModel

from config import settings


class FileInfo(BaseModel):
    name: str
    size: str
    is_dir: bool
    path: str
    mtime: float = 0


class PageGenerator:
    """Main class for generating HTML pages"""

    def __init__(self, rule_set_path: pathlib.Path):
        self.rule_set_path = rule_set_path
        self.directories: dict[str, dict[str, object]] = {}
        self.files: dict[str, dict[str, object]] = {}
        self.global_latest_time = 0

        # Scan filesystem once during initialization
        self._scan_filesystem()
        self._copy_icons()

    def _scan_filesystem(self):
        """Scan entire filesystem and build data structures"""
        # First pass: collect all directories and their files
        for root in pathlib.Path(self.rule_set_path).rglob("*"):
            if root.is_file():
                continue

            # Skip hidden and icons directories
            if root.name.startswith(".") or root.name == "icons":
                continue

            # Process files in this directory
            dir_items = []
            dir_latest_time = 0

            for file_path in root.iterdir():
                if file_path.is_file():
                    if file_path.name == "index.html":
                        continue

                    file_mtime = file_path.stat().st_mtime
                    file_size = file_path.stat().st_size

                    file_info = {
                        "name": file_path.name,
                        "size": file_size,
                        "mtime": file_mtime,
                        "path": str(file_path),
                        "is_dir": False,
                    }

                    dir_items.append(file_info)
                    self.files[str(file_path)] = file_info

                    if file_mtime > dir_latest_time:
                        dir_latest_time = file_mtime

                elif (
                    file_path.is_dir()
                    and not file_path.name.startswith(".")
                    and file_path.name != "icons"
                ):
                    # Calculate latest time for this subdirectory
                    subdir_latest_time = 0
                    try:
                        for subfile_path in file_path.rglob("*"):
                            if (
                                subfile_path.is_file()
                                and subfile_path.name != "index.html"
                            ):
                                subfile_mtime = subfile_path.stat().st_mtime
                                if subfile_mtime > subdir_latest_time:
                                    subdir_latest_time = subfile_mtime
                    except (OSError, PermissionError):
                        subdir_latest_time = file_path.stat().st_mtime

                    dir_info = {
                        "name": file_path.name,
                        "size": 0,
                        "mtime": subdir_latest_time,
                        "path": str(file_path),
                        "is_dir": True,
                    }

                    dir_items.append(dir_info)

                    if subdir_latest_time > dir_latest_time:
                        dir_latest_time = subdir_latest_time

            # Store directory info
            if root != self.rule_set_path:  # Don't store root directory
                self.directories[str(root)] = {
                    "name": root.name,
                    "latest_time": dir_latest_time,
                    "items": dir_items,
                }

                if dir_latest_time > self.global_latest_time:
                    self.global_latest_time = dir_latest_time

    def _copy_icons(self):
        """Copy icons from fixed location to rule-set directory"""
        source_icons_dir = pathlib.Path("icons")
        target_icons_dir = self.rule_set_path / "icons"

        if not source_icons_dir.exists():
            print(f"Warning: {source_icons_dir} directory not found")
            return

        # Create target directory
        target_icons_dir.mkdir(exist_ok=True)

        # Copy all icon files
        for icon_file in source_icons_dir.iterdir():
            if icon_file.is_file() and not icon_file.name.startswith("."):
                shutil.copy2(icon_file, target_icons_dir)
                print(f"Copied: {icon_file.name} to {target_icons_dir}")

    def _format_file_size(self, size: int) -> str:
        """Format file size for display"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    def get_main_directories(self) -> list[dict[str, object]]:
        """Get main directories (direct children of root)"""
        main_dirs = []
        for path, dir_info in self.directories.items():
            if pathlib.Path(path).parent == self.rule_set_path:
                main_dirs.append(
                    {
                        "name": dir_info["name"],
                        "path": path,
                        "latest_time": dir_info["latest_time"],
                    }
                )
        return main_dirs

    def get_directory_items(self, directory_path: str) -> list[FileInfo]:
        """Get items in a specific directory"""
        items = []

        if directory_path in self.directories:
            dir_info = self.directories[directory_path]
            for item_info in dir_info["items"]:
                file_info = FileInfo(
                    name=item_info["name"],
                    size=self._format_file_size(item_info["size"])
                    if not item_info["is_dir"]
                    else "",
                    is_dir=item_info["is_dir"],
                    path=item_info["path"],
                    mtime=item_info["mtime"],
                )
                items.append(file_info)

        return items

    def generate_root_index(self) -> str:
        """Generate root index.html content"""
        dirs = self.get_main_directories()
        latest_update_time = self.global_latest_time

        icons = {
            "clash": """<img src="icons/clash.svg" alt="Clash" class="w-8 h-8">""",
            "surge": """<img src="icons/surge.svg" alt="Surge" class="w-8 h-8">""",
            "sing-box": """<img src="icons/sing-box.svg" alt="Sing-Box" class="w-8 h-8">""",
            "loon": """<img src="icons/loon.svg" alt="Loon" class="w-8 h-8">""",
            "egern": """<img src="icons/egern.svg" alt="Egern" class="w-8 h-8">""",
            "geoip": """<svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            </svg>""",
        }

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rule Set - 规则集</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    animation: {{
                        'fade-in': 'fadeIn 0.8s ease-out',
                        'slide-up': 'slideUp 0.6s ease-out',
                        'float': 'float 8s ease-in-out infinite',
                        'pulse-gentle': 'pulseGentle 4s ease-in-out infinite',
                    }},
                    keyframes: {{
                        fadeIn: {{
                            '0%': {{ opacity: '0', transform: 'translateY(30px)' }},
                            '100%': {{ opacity: '1', transform: 'translateY(0)' }}
                        }},
                        slideUp: {{
                            '0%': {{ opacity: '0', transform: 'translateY(40px)' }},
                            '100%': {{ opacity: '1', transform: 'translateY(0)' }}
                        }},
                        float: {{
                            '0%, 100%': {{ transform: 'translateY(0px)' }},
                            '50%': {{ transform: 'translateY(-20px)' }}
                        }},
                        pulseGentle: {{
                            '0%, 100%': {{ opacity: '0.4' }},
                            '50%': {{ opacity: '0.8' }}
                        }}
                    }}
                }}
            }}
        }}
    </script>
    <style>
        .glass {{
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(24px);
            border: 1px solid rgba(255, 255, 255, 0.15);
        }}
        .card-hover {{
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .card-hover:hover {{
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }}
        .gradient-text {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .glow {{
            box-shadow: 0 0 30px rgba(240, 147, 251, 0.3);
        }}
        .glow:hover {{
            box-shadow: 0 0 40px rgba(240, 147, 251, 0.5);
        }}
        .card-bg {{
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%);
            backdrop-filter: blur(20px);
        }}
    </style>
</head>
<body class="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 relative overflow-x-hidden">
    <!-- Background elements -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <div class="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-purple-200/40 to-pink-200/40 rounded-full mix-blend-multiply filter blur-3xl animate-float"></div>
        <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-pink-200/40 to-rose-200/40 rounded-full mix-blend-multiply filter blur-3xl animate-float" style="animation-delay: -4s;"></div>
        <div class="absolute top-40 left-40 w-80 h-80 bg-gradient-to-br from-purple-200/30 to-rose-200/30 rounded-full mix-blend-multiply filter blur-3xl animate-float" style="animation-delay: -2s;"></div>
        <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-purple-100/20 to-pink-100/20 rounded-full mix-blend-multiply filter blur-3xl animate-pulse-gentle"></div>
    </div>

    <div class="relative z-10 max-w-6xl mx-auto p-6 lg:p-8">
        <!-- Header -->
        <div class="text-center mb-16 animate-fade-in">
            <div class="glass rounded-3xl overflow-hidden shadow-2xl mb-8 glow">
                <div class="bg-gradient-to-r from-purple-900 via-pink-800 to-rose-800 px-8 py-12 relative">
                    <div class="relative z-10">
                        <h1 class="text-5xl font-bold text-white mb-4">Rule Set</h1>
                        <p class="text-purple-200 text-lg">更新时间：{datetime.fromtimestamp(latest_update_time).strftime("%Y-%m-%d %H:%M:%S") if latest_update_time > 0 else datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Directory Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">"""

        for i, dir_item in enumerate(dirs):
            icon = icons.get(
                dir_item["name"],
                """<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
                </svg>""",
            )

            html += f"""
            <div class="animate-slide-up" style="animation-delay: {i * 0.1}s;">
                <a href="{dir_item["name"]}/" class="group block card-hover">
                    <div class="card-bg rounded-3xl p-8 h-full border border-white/50 hover:border-purple-300/60 transition-all duration-300 shadow-xl hover:shadow-2xl">
                        <div class="flex flex-col items-center justify-center mb-6">
                            <div class="p-4 bg-gradient-to-br from-purple-100 to-pink-100 group-hover:from-purple-200 group-hover:to-pink-200 rounded-2xl mb-4 transition-all duration-300 shadow-lg group-hover:shadow-xl">
                                <div class="text-purple-600 group-hover:text-purple-700 transition-colors">
                                    {icon}
                                </div>
                            </div>
                            <div class="text-center">
                                <h3 class="text-2xl font-bold text-gray-800 group-hover:text-purple-700 transition-colors">{dir_item["name"].title() if dir_item["name"] != "geoip" else "GeoIP"}</h3>
                            </div>
                        </div>
                        <div class="text-center">
                            <p class="text-sm text-gray-600">更新时间：{datetime.fromtimestamp(dir_item["latest_time"]).strftime("%Y-%m-%d %H:%M:%S")}</p>
                        </div>
                    </div>
                </a>
            </div>"""

        html += """
        </div>
    </div>
</body>
</html>"""

        return html

    def generate_directory_index(
        self, directory: pathlib.Path, parent_path: str = ""
    ) -> str:
        """Generate index.html content for a directory"""
        items = self.get_directory_items(str(directory))

        # Separate files and directories
        dirs = [item for item in items if item.is_dir]
        files = [item for item in items if not item.is_dir]

        # Calculate the correct relative path for icons based on current directory depth
        icon_depth = (
            len(parent_path.strip("/").split("/")) + 2 if parent_path else 1
        )  # +2 for icons directory
        icon_prefix = "../" * icon_depth

        # Define icons for specific directories
        directory_icons = {
            "clash": f"""<img src="{icon_prefix}icons/clash.svg" alt="Clash" class="w-6 h-6">""",
            "surge": f"""<img src="{icon_prefix}icons/surge.svg" alt="Surge" class="w-6 h-6">""",
            "sing-box": f"""<img src="{icon_prefix}icons/sing-box.svg" alt="Sing-Box" class="w-6 h-6">""",
            "loon": f"""<img src="{icon_prefix}icons/loon.svg" alt="Loon" class="w-6 h-6">""",
            "egern": f"""<img src="{icon_prefix}icons/egern.svg" alt="Egern" class="w-6 h-6">""",
            "geoip": """<svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            </svg>""",
        }

        # Get the appropriate icon for this directory
        # For subdirectories, we need to get the parent directory name to determine the app icon
        # Get the first part of the path to determine the app (e.g., "clash" from "clash/domain/classical")
        path_parts = str(directory).split("/")
        app_name = None
        for part in path_parts:
            if part in directory_icons:
                app_name = part
                break

        icon = directory_icons.get(
            app_name,
            """<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
            </svg>""",
        )

        # Generate HTML with Tailwind CSS
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{directory.name} - Rule Set</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    animation: {{
                        'fade-in': 'fadeIn 0.6s ease-out',
                        'slide-up': 'slideUp 0.4s ease-out',
                        'float': 'float 6s ease-in-out infinite',
                    }},
                    keyframes: {{
                        fadeIn: {{
                            '0%': {{ opacity: '0', transform: 'translateY(20px)' }},
                            '100%': {{ opacity: '1', transform: 'translateY(0)' }}
                        }},
                        slideUp: {{
                            '0%': {{ opacity: '0', transform: 'translateY(30px)' }},
                            '100%': {{ opacity: '1', transform: 'translateY(0)' }}
                        }},
                        float: {{
                            '0%, 100%': {{ transform: 'translateY(0px)' }},
                            '50%': {{ transform: 'translateY(-15px)' }}
                        }}
                    }}
                }}
            }}
        }}
    </script>
    <style>
        .glass {{
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(24px);
            border: 1px solid rgba(255, 255, 255, 0.15);
        }}
        .card-hover {{
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .card-hover:hover {{
            transform: translateY(-6px) scale(1.02);
            box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.2);
        }}
        .glow {{
            box-shadow: 0 0 30px rgba(240, 147, 251, 0.3);
        }}
        .glow:hover {{
            box-shadow: 0 0 40px rgba(240, 147, 251, 0.5);
        }}
        .card-bg {{
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%);
            backdrop-filter: blur(20px);
        }}
    </style>
</head>
<body class="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-rose-50 relative overflow-x-hidden">
    <!-- Background decoration -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <div class="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-purple-200/30 to-rose-200/30 rounded-full mix-blend-multiply filter blur-3xl animate-float"></div>
        <div class="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-pink-200/30 to-rose-200/30 rounded-full mix-blend-multiply filter blur-3xl animate-float" style="animation-delay: -2s;"></div>
        <div class="absolute top-40 left-40 w-80 h-80 bg-gradient-to-br from-purple-200/20 to-rose-200/20 rounded-full mix-blend-multiply filter blur-3xl animate-float" style="animation-delay: -4s;"></div>
    </div>

    <div class="relative z-10 max-w-6xl mx-auto p-6 lg:p-8">
        <!-- Header -->
        <div class="mb-8 animate-fade-in">
            <div class="glass rounded-3xl overflow-hidden shadow-2xl glow">
                <div class="bg-gradient-to-r from-purple-900 via-pink-800 to-rose-800 px-6 py-6 relative">
                    <div class="relative z-10">
                        <div class="flex items-center justify-between">
                            <!-- Back Button -->
                            <div class="flex-shrink-0">
                                <a href=".." class="inline-flex items-center justify-center w-10 h-10 glass text-white rounded-xl hover:bg-white/20 transition-all duration-300 group card-hover">
                                    <svg class="w-5 h-5 group-hover:-translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
                                    </svg>
                                </a>
                            </div>
                            
                            <!-- Center content -->
                            <div class="flex items-center justify-center flex-1">
                                <div class="glass rounded-xl p-2 mr-2 shadow-lg w-10 h-10 flex items-center justify-center">
                                    {icon}
                                </div>
                                <h1 class="text-xl font-bold text-white drop-shadow-lg">
                                    {directory.name.title() if directory.name != "geoip" else "GeoIP"}
                                </h1>
                            </div>
                            
                            <!-- Spacer to balance the layout -->
                            <div class="flex-shrink-0 w-10"></div>
                        </div>"""

        html += """
                    </div>
                </div>
            </div>
        </div>

        <!-- Content -->
        <div class="space-y-8">"""

        # Directories section
        if dirs:
            html += """
            <div class="animate-slide-up">
                <div class="card-bg rounded-3xl overflow-hidden shadow-xl">
                    <div class="px-6 py-5 border-b border-purple-200/30 bg-gradient-to-r from-purple-50/50 to-pink-50/50">
                        <h2 class="text-xl font-bold text-gray-800 flex items-center">
                            <div class="p-2 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg mr-4 shadow-lg">
                                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
                                </svg>
                            </div>
                            目录
                        </h2>
                    </div>
                    <div class="p-6">
                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">"""

            for dir_item in dirs:
                # Get the appropriate icon for this directory
                icon = directory_icons.get(
                    dir_item.name,
                    """<svg class="w-7 h-7 text-purple-600 group-hover:text-purple-700 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
                    </svg>""",
                )

                html += f"""
                        <a href="{dir_item.name}/" class="group block card-hover">
                            <div class="card-bg rounded-2xl p-6 h-full border border-white/40 hover:border-purple-300/60 transition-all duration-300 shadow-xl hover:shadow-2xl">
                                <div class="flex items-center mb-4">
                                    <div class="p-3 bg-gradient-to-br from-purple-100 to-pink-100 group-hover:from-purple-200 group-hover:to-pink-200 rounded-xl mr-4 transition-all duration-300 shadow-lg group-hover:shadow-xl">
                                        {icon}
                                    </div>
                                    <div>
                                        <div class="font-bold text-gray-800 group-hover:text-purple-700 transition-colors text-lg">{dir_item.name.title() if dir_item.name != "geoip" else "GeoIP"}</div>
                                    </div>
                                </div>
                                <div class="text-center">
                                    <p class="text-sm text-gray-600">更新时间：{datetime.fromtimestamp(dir_item.mtime).strftime("%Y-%m-%d %H:%M:%S")}</p>
                                </div>
                            </div>
                        </a>"""

            html += """
                        </div>
                    </div>
                </div>
            </div>"""

        # Files section
        if files:
            html += """
            <div class="animate-slide-up" style="animation-delay: 0.1s;">
                <div class="card-bg rounded-3xl overflow-hidden shadow-xl">
                    <div class="px-6 py-5 border-b border-rose-200/30 bg-gradient-to-r from-rose-50/50 to-pink-50/50">
                        <h2 class="text-xl font-bold text-gray-800 flex items-center">
                            <div class="p-2 bg-gradient-to-br from-rose-500 to-pink-600 rounded-lg mr-4 shadow-lg">
                                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                </svg>
                            </div>
                            文件
                        </h2>
                    </div>
                    <div class="p-6">
                        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">"""

            for file_item in files:
                html += f"""
                            <a href="{file_item.name}" class="group block card-hover">
                                <div class="card-bg rounded-2xl p-6 h-full border border-white/40 hover:border-rose-300/60 transition-all duration-300 shadow-xl hover:shadow-2xl">
                                    <div class="flex items-center mb-4">
                                        <div class="p-3 bg-gradient-to-br from-rose-100 to-pink-100 group-hover:from-rose-200 group-hover:to-pink-200 rounded-xl mr-4 transition-all duration-300 shadow-lg group-hover:shadow-xl">
                                            <svg class="w-7 h-7 text-rose-600 group-hover:text-rose-700 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                            </svg>
                                        </div>
                                        <div class="min-w-0 flex-1">
                                            <div class="font-bold text-gray-800 group-hover:text-rose-700 transition-colors truncate text-lg">{file_item.name}</div>
                                            <div class="text-sm text-gray-600">{datetime.fromtimestamp(file_item.mtime).strftime("%Y-%m-%d %H:%M:%S")}</div>
                                            <div class="text-sm text-gray-600">{file_item.size}</div>
                                        </div>
                                    </div>
                                </div>
                            </a>"""

            html += """
                        </div>
                    </div>
                </div>
            </div>"""

        # Empty state
        if not dirs and not files:
            html += """
            <div class="animate-slide-up">
                <div class="card-bg rounded-3xl overflow-hidden shadow-xl">
                    <div class="p-20 text-center">
                        <div class="mx-auto w-20 h-20 bg-gradient-to-br from-purple-100 to-pink-100 rounded-full flex items-center justify-center mb-6 shadow-lg">
                            <svg class="w-10 h-10 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                            </svg>
                        </div>
                        <h3 class="text-2xl font-bold text-gray-800 mb-3">此目录为空</h3>
                        <p class="text-gray-600 text-lg">没有找到任何文件或子目录</p>
                    </div>
                </div>
            </div>"""

        html += """
        </div>
    </div>
</body>
</html>"""

        return html

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

        # Generate index files for all subdirectories
        for directory in self.rule_set_path.rglob("*"):
            if not directory.is_dir() or directory == self.rule_set_path:
                continue

            # Skip hidden directories and icons directory
            if directory.name.startswith(".") or directory.name == "icons":
                continue

            # Calculate relative path for breadcrumb
            rel_path = directory.relative_to(self.rule_set_path)
            parent_path = (
                str(rel_path.parent) if rel_path.parent != pathlib.Path(".") else ""
            )

            # Generate index.html for this directory
            html_content = self.generate_directory_index(directory, parent_path)
            index_file = directory / "index.html"

            with open(index_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"Generated: {index_file}")


def generate_all_indexes() -> None:
    """Generate index.html files for all directories"""
    generator = PageGenerator(settings.dir_path)
    generator.generate_all_indexes()


if __name__ == "__main__":
    generate_all_indexes()
