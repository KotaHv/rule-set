from pydantic import BaseModel, SerializeAsAny, computed_field

from .option import V2rayDomainOption
from .type import Source


class BaseResource(BaseModel):
    """Base class for all resources"""

    @computed_field
    @property
    def kind(self) -> str:
        return type(self).__name__


class ContentResource(BaseResource):
    """Base class for resources with a source"""

    source: Source


class RuleSetResource(ContentResource):
    """Rule set resource"""

    pass


class DomainSetResource(ContentResource):
    """Domain set resource"""

    pass


class V2rayDomainResource(ContentResource):
    """V2Ray domain resource"""

    option: V2rayDomainOption = V2rayDomainOption()


class MaxMindDBResource(ContentResource):
    """MaxMind database resource"""

    pass


class SourceReference(BaseResource):
    """Resource referencing another source's generated output"""

    target: str


# Resource list type
type ResourceList = list[SerializeAsAny[BaseResource]]
