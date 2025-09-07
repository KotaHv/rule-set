"""
Command line interface for gen_pages
"""

from pathlib import Path

import typer

from .services import PageGenerator


def main():
    """Main entry point"""
    typer.run(_main)


def _main(
    target_path: Path | None = typer.Option(
        None,
        "--target-path",
        "-t",
        help="Target path for generating pages, e.g., deploy_temp, ./rule-set, etc. If not specified, uses the default path from config file.",
    ),
) -> None:
    """Generate GitHub Pages navigation files for rule-set directories.

    This script generates index.html files for all directories in the rule-set,
    creating a beautiful GitHub Pages navigation interface.
    """
    if target_path:
        print(f"Generating pages for target path: {target_path}")
        generate_all_indexes(target_path)
    else:
        print("Generating pages for default path from settings")
        generate_all_indexes()


def generate_all_indexes(target_path: Path | None = None) -> None:
    """Generate index.html files for all directories"""
    if target_path:
        # Use the specified target path instead of settings.dir_path
        target_rule_set_path = Path(target_path)
        if not target_rule_set_path.exists():
            print(f"Error: Target path {target_path} does not exist")
            return
    else:
        # Use default path from settings
        from rule_set.config import settings

        target_rule_set_path = settings.build_dir

    generator = PageGenerator(target_rule_set_path)
    generator.generate_all_indexes()


if __name__ == "__main__":
    typer.run(_main)
