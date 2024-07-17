from model import RuleModel
from .base import BaseDeserialize


class DomainSetDeserialize(BaseDeserialize):
    def deserialize(self) -> RuleModel:
        for hostname in self.data_lines:
            if hostname.startswith("."):
                self.result.domain_suffix.add(hostname.lstrip("."))
            else:
                self.result.domain.add(hostname)
        return self.result
