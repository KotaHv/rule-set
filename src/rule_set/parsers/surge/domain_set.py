from loguru import logger

from rule_set.models import DomainType, RuleModel
from rule_set.utils import validate_domain

from .base import BaseParser


class DomainSetParser(BaseParser):
    def parse(self) -> RuleModel:
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
