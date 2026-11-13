from pathlib import Path
from typing import Self

from pydantic import BaseModel, model_validator

from .option import Option
from .resource import (
    ContentResource,
    MaxMindDBResource,
    ResourceList,
    V2rayDomainResource,
)
from .type import SerializeFormats


class SourceModel(BaseModel):
    resources: ResourceList
    name: Path
    exclude: SerializeFormats = []
    include: SerializeFormats | None = None
    option: Option = Option()
    split_resources: bool = False

    @model_validator(mode="after")
    def expand_directory_resources(self) -> Self:
        """Expand directory resources to individual file resources"""
        expanded_resources: ResourceList = []

        for resource in self.resources:
            if (
                isinstance(resource, ContentResource)
                and isinstance(resource.source, Path)
                and resource.source.is_dir()
            ):
                # Recursively find all files in directory and subdirectories
                for root, _, files in resource.source.walk():
                    for file in files:
                        filepath = root / file
                        expanded_resources.append(
                            resource.model_copy(update={"source": filepath})
                        )
            else:
                expanded_resources.append(resource)
        self.resources = expanded_resources
        return self

    @model_validator(mode="after")
    def merge_resource_options(self) -> Self:
        """Merge source-level options into individual resources"""
        for resource in self.resources:
            if isinstance(resource, V2rayDomainResource):
                if "attrs" not in resource.option.model_fields_set:
                    resource.option.attrs = self.option.v2ray_domain.attrs

                if "exclude_includes" not in resource.option.model_fields_set:
                    resource.option.exclude_includes = (
                        self.option.v2ray_domain.exclude_includes
                    )
            elif isinstance(resource, MaxMindDBResource):
                if "option" not in resource.model_fields_set:
                    resource.option = self.option.geo_ip

        return self
