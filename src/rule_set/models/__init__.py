"""
Models package for rule-set project.
Contains all data models and related types.
"""

from .artifact import ArtifactKind
from .enum import DomainType, ProcessingRuleType, SerializeFormat
from .metadata import MetadataRecord
from .option import (
    GeoIPOption,
    Option,
    ProcessingOption,
    SerializationOption,
    V2rayDomainAttrs,
    V2rayDomainOption,
)
from .resource import (
    BaseResource,
    ContentResource,
    DomainSetResource,
    MaxMindDBResource,
    ResourceList,
    RuleSetResource,
    SourceReference,
    V2rayDomainResource,
)
from .rule import (
    RuleModel,
    SerializableRuleModel,
    V2rayDomainResult,
)
from .source import SourceModel
from .type import SerializeFormats, Source

# For backward compatibility and convenience
__all__ = [
    # Types
    "Source",
    # Enums
    "SerializeFormat",
    "DomainType",
    "ProcessingRuleType",
    "ArtifactKind",
    "MetadataRecord",
    # Options
    "SerializeFormats",
    "V2rayDomainAttrs",
    "SerializationOption",
    "ProcessingOption",
    "V2rayDomainOption",
    "GeoIPOption",
    "Option",
    # Resources
    "BaseResource",
    "ContentResource",
    "RuleSetResource",
    "DomainSetResource",
    "V2rayDomainResource",
    "MaxMindDBResource",
    "SourceReference",
    "ResourceList",
    # Rules
    "RuleModel",
    "V2rayDomainResult",
    "SerializableRuleModel",
    # Sources
    "SourceModel",
]
