#!/usr/bin/env python3
"""
Generate index.html files for GitHub Pages directory browsing
"""

import pathlib
from typing import List

from pydantic import BaseModel

from config import settings


class FileInfo(BaseModel):
    name: str
    size: str
    is_dir: bool
    path: str


def get_file_info(file_path: pathlib.Path) -> FileInfo:
    """Get file information for display"""
    stat = file_path.stat()
    size = stat.st_size

    # Format file size
    if size < 1024:
        size_str = f"{size} B"
    elif size < 1024 * 1024:
        size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = f"{size / (1024 * 1024):.1f} MB"

    return FileInfo(
        name=file_path.name,
        size=size_str,
        is_dir=file_path.is_dir(),
        path=str(file_path),
    )


def generate_directory_index(directory: pathlib.Path, parent_path: str = "") -> str:
    """Generate index.html content for a directory"""

    # Get all items in directory
    items: List[FileInfo] = []
    for item in sorted(directory.iterdir()):
        if item.name.startswith(".") or item.name == "index.html":
            continue
        items.append(get_file_info(item))

    # Separate files and directories
    dirs = [item for item in items if item.is_dir]
    files = [item for item in items if not item.is_dir]

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{directory.name} - Rule Set</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        
        h1 {{
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        .breadcrumb {{
            font-size: 14px;
            opacity: 0.8;
        }}
        
        .breadcrumb a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        .breadcrumb a:hover {{
            text-decoration: underline;
        }}
        
        .back-link {{
            display: inline-block;
            margin: 20px;
            padding: 8px 16px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .back-link:hover {{
            background: #2980b9;
        }}
        
        .content {{
            padding: 20px;
        }}
        
        .section {{
            margin-bottom: 30px;
        }}
        
        .section h2 {{
            color: #2c3e50;
            font-size: 1.3rem;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #ecf0f1;
        }}
        
        .item-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }}
        
        .item {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 15px;
            transition: all 0.2s ease;
        }}
        
        .item:hover {{
            background: #e9ecef;
            border-color: #3498db;
        }}
        
        .item a {{
            text-decoration: none;
            color: inherit;
            display: block;
        }}
        
        .item-name {{
            font-weight: 500;
            color: #2c3e50;
            margin-bottom: 5px;
            word-break: break-all;
        }}
        
        .item-size {{
            font-size: 12px;
            color: #6c757d;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 40px 20px;
            color: #6c757d;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .item-list {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{directory.name}</h1>"""

    # Add breadcrumb navigation
    if parent_path:
        path_parts = parent_path.strip("/").split("/")
        current_path = ""
        html += """
            <div class="breadcrumb">"""
        for part in path_parts:
            current_path += f"/{part}"
            html += f'<a href="{current_path}/">{part}</a> / '
        html += f"{directory.name}"
        html += """
            </div>"""

    html += """
        </div>
        
        <a href=".." class="back-link">← 返回上级</a>
        
        <div class="content">"""

    # Directories section
    if dirs:
        html += """
            <div class="section">
                <h2>目录</h2>
                <div class="item-list">"""

        for dir_item in dirs:
            html += f"""
                    <div class="item">
                        <a href="{dir_item.name}/">
                            <div class="item-name">{dir_item.name}</div>
                        </a>
                    </div>"""

        html += """
                </div>
            </div>"""

    # Files section
    if files:
        html += """
            <div class="section">
                <h2>文件</h2>
                <div class="item-list">"""

        for file_item in files:
            html += f"""
                    <div class="item">
                        <a href="{file_item.name}">
                            <div class="item-name">{file_item.name}</div>
                            <div class="item-size">{file_item.size}</div>
                        </a>
                    </div>"""

        html += """
                </div>
            </div>"""

    # Empty state
    if not dirs and not files:
        html += """
            <div class="empty-state">
                <h3>此目录为空</h3>
                <p>没有找到任何文件或子目录</p>
            </div>"""

    html += """
        </div>
    </div>
</body>
</html>"""

    return html


def generate_root_index(rule_set_dir: pathlib.Path) -> str:
    """Generate root index.html content"""

    # Get main directories
    dirs: List[dict[str, str]] = []
    for item in sorted(rule_set_dir.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            dirs.append({"name": item.name, "path": str(item)})

    # Define descriptions for each directory
    descriptions = {
        "clash": "Clash 代理工具规则集",
        "surge": "Surge 代理工具规则集",
        "sing-box": "Sing-Box 代理工具规则集",
        "loon": "Loon 代理工具规则集",
        "egern": "Egern 代理工具规则集",
        "geoip": "V2ray dat 格式 IP 数据库",
    }

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rule Set - 规则集</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .header {
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        h1 {
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .subtitle {
            opacity: 0.8;
            font-size: 1.1rem;
        }
        
        .directory-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
        }
        
        .directory-item {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 25px;
            text-align: center;
            transition: all 0.2s ease;
        }
        
        .directory-item:hover {
            background: #e9ecef;
            border-color: #3498db;
            transform: translateY(-2px);
        }
        
        .directory-link {
            text-decoration: none;
            color: inherit;
            display: block;
        }
        
        .directory-name {
            font-size: 1.3rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            text-transform: capitalize;
        }
        
        .directory-desc {
            font-size: 0.9rem;
            color: #6c757d;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .directory-grid {
                grid-template-columns: 1fr;
                padding: 20px;
            }
            
            .header {
                padding: 20px;
            }
            
            h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Rule Set</h1>
            <p class="subtitle">选择代理工具类型查看对应的规则集</p>
        </div>

        <div class="directory-grid">"""

    for dir_item in dirs:
        desc = descriptions.get(dir_item["name"], "规则集目录")

        html += f"""
            <div class="directory-item">
                <a href="{dir_item["name"]}/" class="directory-link">
                    <div class="directory-name">{dir_item["name"]}</div>
                    <div class="directory-desc">{desc}</div>
                </a>
            </div>"""

    html += """
        </div>
    </div>
</body>
</html>"""

    return html


def generate_all_indexes() -> None:
    """Generate index.html files for all directories"""
    rule_set_path = settings.dir_path

    if not rule_set_path.exists():
        print(f"Error: {rule_set_path} directory not found")
        return

    # Generate root index (this will be the index.html for the release branch root)
    root_html = generate_root_index(rule_set_path)
    with open(rule_set_path / "index.html", "w", encoding="utf-8") as f:
        f.write(root_html)
    print(f"Generated: {rule_set_path}/index.html")

    # Generate index files for all subdirectories using pathlib
    for directory in rule_set_path.rglob("*"):
        if not directory.is_dir() or directory == rule_set_path:
            continue

        # Skip hidden directories
        if directory.name.startswith("."):
            continue

        # Calculate relative path for breadcrumb
        rel_path = directory.relative_to(rule_set_path)
        parent_path = (
            str(rel_path.parent) if rel_path.parent != pathlib.Path(".") else ""
        )

        # Generate index.html for this directory
        html_content = generate_directory_index(directory, parent_path)
        index_file = directory / "index.html"

        with open(index_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Generated: {index_file}")


if __name__ == "__main__":
    generate_all_indexes()
