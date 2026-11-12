from typing import override

from loguru import logger

from rule_set.models import RuleModel
from rule_set.utils import validate_domain

from .base import BaseParser


class DomainSetParser(BaseParser):
    @override
    def parse(self) -> RuleModel:
        for domain in self.data_lines:
            if domain.startswith("."):
                domain = domain.lstrip(".")
                if not validate_domain(domain):
                    logger.warning(f"Invalid domain: '{domain}'")
                    continue
                self.result.domain_suffix.add(domain)
            else:
                if not validate_domain(domain):
                    logger.warning(f"Invalid domain: '{domain}'")
                    continue
                self.result.domain.add(domain)
        return self.result
