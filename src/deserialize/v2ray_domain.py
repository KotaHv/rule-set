import re
from model import RuleModel, V2rayDomainResult, V2rayDomainOption, DomainType

EXPLICIT_RULE = re.compile(
    r"^(domain|keyword|full|regexp):(.+?)(?:\s+(@\w+(?:\s+@\w+)*))?$"
)


def deserialize(data: str, option: V2rayDomainOption) -> V2rayDomainResult:
    """
    V2Ray domain syntax:
        - Lines starting with '#' are comments and ignored.
        - 'include:' reference external files.
        - 'domain:' defines a domain-suffix rule (prefix can be omitted).
        - 'keyword:' defines a domain-keyword rule.
        - 'regexp:' ignored.
        - 'full:' defines a domain rule.
        - Domain rules (domain, keyword, regexp, full) may include one or more
          attributes, each beginning with '@' and separated by spaces (e.g., @ads @cn).
    """
    attrs = option.attrs
    exclude_includes = option.exclude_includes
    rules = RuleModel()
    includes = []

    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("include:"):
            include = line[8:].strip()
            if include not in exclude_includes:
                includes.append(include)
            continue
        line = line.split("#", 1)[0].strip()
        explicit_match = EXPLICIT_RULE.match(line)
        if explicit_match:
            rule_type, rule, attributes = explicit_match.groups()
            attributes = attributes.split() if attributes else []
        else:
            rule_type = "domain"
            rule, *attributes = line.split()
        if not attrs.filter_attrs(attributes):
            continue
        if rule_type == "domain":
            rules.domain_trie.add(rule, DomainType.DOMAIN_SUFFIX)
        elif rule_type == "keyword":
            rules.domain_keyword.add(rule)
        elif rule_type == "full":
            rules.domain_trie.add(rule, DomainType.DOMAIN)

    return V2rayDomainResult(rules=rules, includes=includes)
