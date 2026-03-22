"""
Models package for rule-set project.
Contains all data models and related types.
"""

from .enum import DomainType, SerializeFormat
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
    DomainSetResource,
    MaxMindDBResource,
    ResourceList,
    ResourceType,
    RuleSetResource,
    SourceReference,
    V2rayDomainResource,
)
from .rule import (
    RuleModel,
    SerializableRuleModel,
    V2rayDomainInclude,
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
    "RuleSetResource",
    "DomainSetResource",
    "V2rayDomainResource",
    "MaxMindDBResource",
    "SourceReference",
    "ResourceType",
    "ResourceList",
    # Rules
    "RuleModel",
    "V2rayDomainResult",
    "V2rayDomainInclude",
    "SerializableRuleModel",
    # Sources
    "SourceModel",
]
