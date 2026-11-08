import re

from loguru import logger

from rule_set.models import (
    DomainType,
    RuleModel,
    V2rayDomainAttrs,
    V2rayDomainOption,
    V2rayDomainResource,
    V2rayDomainResult,
)
from rule_set.utils import build_v2ray_include_url, validate_domain

LINE_PATTERN = re.compile(
    r"^(?P<type>domain|keyword|full|regexp|include):(?P<rule>.+?)(?:\s+(?P<attrs>@-?!?\w+(?:\s+@-?!?\w+)*))?$"
)

_DOMAIN_RULE_TYPES: dict[str, DomainType] = {
    "domain": DomainType.DOMAIN_SUFFIX,
    "full": DomainType.DOMAIN,
}


def parse(data: str, resource: V2rayDomainResource) -> V2rayDomainResult:
    """
    V2Ray domain syntax:
        - Lines starting with '#' are comments and ignored.
        - 'include:' reference external files;
          with optional attributes (e.g., @attr1 @-attr2),
          only rules with @attr1 and without @attr2 are included.
        - 'domain:' defines a domain-suffix rule (prefix can be omitted).
        - 'keyword:' defines a domain-keyword rule.
        - 'regexp:' defines a domain-regex rule.
        - 'full:' defines a domain rule.
        - Domain rules (domain, keyword, regexp, full) may include one or more
          attributes, each beginning with '@' and separated by spaces (e.g., @ads @cn).
    """
    rules = RuleModel()
    resources: list[V2rayDomainResource] = []

    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = line.split("#", 1)[0].strip()
        match = LINE_PATTERN.match(line)
        if match:
            rule_type, rule, attributes_str = match.group("type", "rule", "attrs")
            attributes = attributes_str.split() if attributes_str else []
        else:
            rule_type = "domain"
            rule, *attributes = line.split()
        if rule_type == "include":
            if rule in resource.option.exclude_includes:
                continue
            include_attrs: list[str] = []
            exclude_attrs: list[str] = []
            for attr in attributes:
                if attr.startswith("@-"):
                    exclude_attrs.append(attr[2:])
                else:
                    include_attrs.append(attr[1:])
            resources.append(
                V2rayDomainResource(
                    source=build_v2ray_include_url(resource.source, rule),
                    option=V2rayDomainOption(
                        attrs=V2rayDomainAttrs(
                            include_attrs=include_attrs
                            + resource.option.attrs.include_attrs,
                            exclude_attrs=exclude_attrs
                            + resource.option.attrs.exclude_attrs,
                        ),
                        exclude_includes=resource.option.exclude_includes,
                    ),
                )
            )
            continue
        if not resource.option.attrs.matches(attributes):
            continue
        if domain_type := _DOMAIN_RULE_TYPES.get(rule_type):
            if not validate_domain(rule):
                logger.warning(f"Invalid domain: '{rule}'")
                continue
            rules.domain_trie.add(rule, domain_type)
        elif rule_type == "keyword":
            rules.domain_keyword.add(rule)
        elif rule_type == "regexp":
            rules.domain_regex.add(rule)

    return V2rayDomainResult(rules=rules, resources=resources)
