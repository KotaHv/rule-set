from dataclasses import dataclass
from pathlib import Path

from .config import settings
from .models.artifact import ArtifactKind


@dataclass(frozen=True)
class OutputSpec:
    directory: Path
    suffix: str

    def relative_path(self, source_name: Path) -> Path:
        return self.directory / source_name.with_suffix(self.suffix)

    def path(self, source_name: Path) -> Path:
        return settings.build_dir / self.relative_path(source_name)


SURGE_OUTPUT = OutputSpec(Path("surge"), ".list")
LOON_OUTPUT = OutputSpec(Path("loon"), ".list")
EGERN_OUTPUT = OutputSpec(Path("egern"), ".yaml")
GEOIP_OUTPUT = OutputSpec(Path("geoip"), ".dat")
SING_BOX_OUTPUT = OutputSpec(Path("sing-box"), ".json")
SING_BOX_SRS_OUTPUT = OutputSpec(Path("sing-box"), ".srs")

CLASH_OUTPUTS: dict[ArtifactKind, OutputSpec] = {
    ArtifactKind.DOMAIN: OutputSpec(Path("clash/domain"), ".yaml"),
    ArtifactKind.IPCIDR: OutputSpec(Path("clash/ipcidr"), ".yaml"),
    ArtifactKind.CLASSICAL: OutputSpec(Path("clash/classical"), ".yaml"),
}

CLASH_MRS_OUTPUTS: dict[ArtifactKind, OutputSpec] = {
    ArtifactKind.DOMAIN: OutputSpec(Path("clash/domain"), ".mrs"),
    ArtifactKind.IPCIDR: OutputSpec(Path("clash/ipcidr"), ".mrs"),
}
