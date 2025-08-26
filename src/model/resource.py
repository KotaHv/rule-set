from pydantic import BaseModel

from .type import Source
from .option import V2rayDomainOption


class BaseResource(BaseModel):
    """Base class for actual resources"""

    source: Source


class RuleSetResource(BaseResource):
    """Rule set resource"""

    pass


class DomainSetResource(BaseResource):
    """Domain set resource"""

    pass


class V2rayDomainResource(BaseResource):
    """V2Ray domain resource"""

    option: V2rayDomainOption = V2rayDomainOption()


class MaxMindDBResource(BaseResource):
    """MaxMind database resource"""

    pass


class SourceReference(BaseModel):
    """Source reference - not an actual resource"""

    target: str


type ResourceType = (
    RuleSetResource
    | DomainSetResource
    | V2rayDomainResource
    | MaxMindDBResource
    | SourceReference
)

# Resource list type
type ResourceList = list[ResourceType]
