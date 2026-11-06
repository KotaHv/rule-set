from typing import Protocol

from rule_set.metadata import MetadataStore
from rule_set.models import WriteContext
from rule_set.models.metadata import MetadataRecord
from rule_set.serializers.mrs import MrsBehavior
from rule_set.serializers.mrs import encode_rule_set as encode_mrs
from rule_set.serializers.srs import encode_rule_set as encode_srs

from .write import write


class PostWriteMiddleware(Protocol):
    def after_write(self, context: WriteContext) -> None: ...


class PreWriteMiddleware(Protocol):
    def before_write(self, context: WriteContext) -> None: ...


class MetadataMiddleware:
    def __init__(self, metadata_store: MetadataStore) -> None:
        self.metadata_store: MetadataStore = metadata_store

    def before_write(self, context: WriteContext) -> None:
        self.metadata_store.update(
            MetadataRecord(path=context.filepath, timestamp=context.timestamp)
        )


class SingBoxSrsMiddleware:
    def __init__(self, metadata_store: MetadataStore) -> None:
        self.metadata_store: MetadataStore = metadata_store

    def after_write(self, context: WriteContext) -> None:
        srs_path = context.filepath.with_suffix(".srs")
        write(srs_path, encode_srs(context.filepath.read_bytes()))
        self.metadata_store.update(
            MetadataRecord(path=srs_path, timestamp=context.timestamp)
        )


class MihomoMrsMiddleware:
    def __init__(self, behavior: MrsBehavior, metadata_store: MetadataStore) -> None:
        self.behavior: MrsBehavior = behavior
        self.metadata_store: MetadataStore = metadata_store

    def after_write(self, context: WriteContext) -> None:
        mrs_path = context.filepath.with_suffix(".mrs")
        write(
            mrs_path,
            encode_mrs(context.filepath.read_bytes(), behavior=self.behavior),
        )
        self.metadata_store.update(
            MetadataRecord(path=mrs_path, timestamp=context.timestamp)
        )
