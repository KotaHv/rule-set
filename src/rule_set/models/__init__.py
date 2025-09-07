"""
Models package for rule-set project.
Contains all data models and related types.
"""

from .enum import DomainType, SerializeFormat, V2rayAttrMode
from .option import (
    GeoIPOption,
    Option,
    ProcessingOption,
    SerializationOption,
    V2rayDomainAttr,
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
from .rule import RuleModel, SerializableRuleModel, V2rayDomainResult
from .source import SourceModel
from .type import SerializeFormats, Source

# For backward compatibility and convenience
__all__ = [
    # Types
    "Source",
    # Enums
    "SerializeFormat",
    "V2rayAttrMode",
    "DomainType",
    # Options
    "SerializeFormats",
    "V2rayDomainAttr",
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
    "SerializableRuleModel",
    # Sources
    "SourceModel",
]
