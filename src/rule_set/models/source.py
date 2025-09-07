from pathlib import Path
from typing import Self

from pydantic import BaseModel, model_validator

from .option import Option
from .resource import ResourceList
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
        expanded_resources = []

        for resource in self.resources:
            if (
                hasattr(resource, "source")  # Check if it's a BaseResource
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
    def merge_v2ray_domain_options(self) -> Self:
        """Merge V2rayDomainOption from global option to individual V2rayDomainResource"""
        for resource in self.resources:
            if hasattr(resource, "option") and hasattr(
                resource.option, "attrs"
            ):  # V2rayDomainResource
                # Merge attrs field
                if resource.option.attrs is None:
                    resource.option.attrs = self.option.v2ray_domain.attrs

                # Merge exclude_includes field
                if resource.option.exclude_includes is None:
                    resource.option.exclude_includes = (
                        self.option.v2ray_domain.exclude_includes
                    )

        return self

    def __repr__(self) -> str:
        return f"{self.name}: {self.resources}"

    def __str__(self) -> str:
        return self.__repr__()
