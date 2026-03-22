import re

from rule_set.models import (
    DomainType,
    RuleModel,
    V2rayDomainInclude,
    V2rayDomainOption,
    V2rayDomainResult,
)

LINE_PATTERN = re.compile(
    r"^(?P<type>domain|keyword|full|regexp|include):(?P<rule>.+?)(?:\s+(?P<attrs>@-?!?\w+(?:\s+@-?!?\w+)*))?$"
)


def parse(data: str, option: V2rayDomainOption) -> V2rayDomainResult:
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
    attrs = option.attrs
    exclude_includes = option.exclude_includes
    rules = RuleModel()
    includes: list[V2rayDomainInclude] = []

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
            if rule not in exclude_includes:
                include_attrs, exclude_attrs = [], []
                for attr in attributes:
                    if attr.startswith("@-"):
                        exclude_attrs.append(attr[2:])
                    else:
                        include_attrs.append(attr[1:])
                includes.append(
                    V2rayDomainInclude(
                        name=rule,
                        include_attrs=include_attrs,
                        exclude_attrs=exclude_attrs,
                    )
                )
            continue
        if not attrs.filter(attributes):
            continue
        if rule_type == "domain":
            rules.domain_trie.add(rule, DomainType.DOMAIN_SUFFIX)
        elif rule_type == "keyword":
            rules.domain_keyword.add(rule)
        elif rule_type == "full":
            rules.domain_trie.add(rule, DomainType.DOMAIN)
        elif rule_type == "regexp":
            rules.domain_trie.add(rule, DomainType.DOMAIN_REGEX)

    return V2rayDomainResult(rules=rules, includes=includes)
