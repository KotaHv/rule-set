"""
Models package for rule-set project.
Contains all data models and related types.
"""

from .type import Source, AnyTreeNode, SerializeFormats
from .enum import SerializeFormat, V2rayAttrMode
from .option import (
    V2rayDomainAttr,
    SerializationOption,
    ProcessingOption,
    V2rayDomainOption,
    GeoIPOption,
    Option,
)
from .resource import (
    BaseResource,
    RuleSetResource,
    DomainSetResource,
    V2rayDomainResource,
    MaxMindDBResource,
    SourceReference,
    ResourceType,
    ResourceList,
)
from .rule import RuleModel, V2rayDomainResult
from .source import SourceModel

# For backward compatibility and convenience
__all__ = [
    # Types
    "Source",
    "AnyTreeNode",
    # Enums
    "SerializeFormat",
    "V2rayAttrMode",
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
    # Sources
    "SourceModel",
]
