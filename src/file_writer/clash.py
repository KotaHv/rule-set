import subprocess
from pathlib import Path

from loguru import logger

from config import settings
from .write import write


class FileWriter:
    def __init__(
        self, *, data: tuple[str, str] | list[tuple[str, str]], target_path: Path
    ) -> None:
        self.base_dir = settings.build_dir / "clash"
        self.target_path = target_path
        data = [data] if isinstance(data, tuple) else data
        self.file_data_map: dict[Path, str] = {}
        self._prepare_filepaths(data)

    def _prepare_filepaths(self, data: list[tuple[str, str]]) -> None:
        for behavior, content in data:
            dir_path = self.base_dir / behavior / self.target_path.parent
            filepath = dir_path / self.target_path.with_suffix(".yaml").name
            dir_path.mkdir(parents=True, exist_ok=True)
            self.file_data_map[filepath] = (behavior, content)

    def write(self) -> None:
        for filepath, (behavior, content) in self.file_data_map.items():
            write(filepath, content)
            if behavior in ("domain", "ipcidr"):
                msr_path = filepath.with_suffix(".mrs")
                result = subprocess.run(
                    ["mihomo", "convert-ruleset", behavior, "yaml", filepath, msr_path],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    logger.success(f"{msr_path} generated successfully")
                else:
                    logger.error(
                        f"{msr_path} generated failed, result: {result.stderr}"
                    )
