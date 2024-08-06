from pathlib import Path

from config import DIR_PATH
from .write import write


class FileWriter:
    def __init__(
        self, *, data: tuple[str, str] | list[tuple[str, str]], target_path: Path
    ) -> None:
        self.base_dir = DIR_PATH / "Clash"
        self.target_path = target_path
        data = [data] if isinstance(data, tuple) else data
        self.file_data_map: dict[Path, str] = {}
        self._prepare_filepaths(data)

    def _prepare_filepaths(self, data: list[tuple[str, str]]) -> None:
        single_entry = len(data) == 1
        parent_path = self.base_dir / self.target_path.parent

        for behavior, content in data:
            is_special = behavior in ("domain", "ipcidr")
            dir_path = (
                parent_path / behavior if is_special and single_entry else parent_path
            )
            suffix = f".{behavior}.yaml" if is_special and not single_entry else ".yaml"
            filepath = dir_path / self.target_path.with_suffix(suffix).name
            dir_path.mkdir(parents=True, exist_ok=True)
            self.file_data_map[filepath] = content

    def write(self) -> None:
        for filepath, content in self.file_data_map.items():
            write(filepath, content)
