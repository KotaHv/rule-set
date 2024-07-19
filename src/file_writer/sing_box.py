import subprocess

from loguru import logger

from .base import BaseFileWriter


class FileWriter(BaseFileWriter):
    @property
    def base_path(self) -> str:
        return "sing-box"

    @property
    def suffix(self) -> str:
        return ".json"

    def write(self):
        super().write()
        srs_path = self.filepath.with_suffix(".srs")
        result = subprocess.run(
            ["sing-box", "rule-set", "compile", self.filepath],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.success(f"{srs_path} generated successfully")
        else:
            logger.error(f"{srs_path} generated failed, result: {result.stderr}")
