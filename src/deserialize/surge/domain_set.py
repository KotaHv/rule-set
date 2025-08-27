from loguru import logger

from model import RuleModel, DomainType
from .base import BaseDeserialize
from utils import validate_domain


class DomainSetDeserialize(BaseDeserialize):
    def deserialize(self) -> RuleModel:
        for domain in self.data_lines:
            if domain.startswith("."):
                domain = domain.lstrip(".")
                if not validate_domain(domain):
                    logger.warning(f"Invalid domain: '{domain}'")
                    continue
                self.result.domain_trie.add(domain, DomainType.DOMAIN_SUFFIX)
            else:
                if not validate_domain(domain):
                    logger.warning(f"Invalid domain: '{domain}'")
                    continue
                self.result.domain_trie.add(domain, DomainType.DOMAIN)
        return self.result
