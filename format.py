from collections import defaultdict
from pathlib import Path
import ipaddress

RULE_TYPES = [
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-SET",
    "DOMAIN-WILDCARD",
    "IP-CIDR",
    "IP-CIDR6",
    "GEOIP",
    "IP-ASN",
    "USER-AGENT",
    "URL-REGEX",
    "PROCESS-NAME",
    "SUBNET",
    "DEST-PORT",
    "IN-PORT",
    "SRC-PORT",
    "SRC-IP",
    "PROTOCOL",
    "SCRIPT",
    "CELLULAR-RADIO",
    "DEVICE-NAME",
    "RULE-SET",
    "AND",
    "NOT",
    "OR",
]

COMMENTS = ["#", ";", "//"]


class Format:
    def __init__(self, filepath: str | Path) -> None:
        if isinstance(filepath, str):
            filepath = Path(filepath)
        self.filepath = filepath
        with filepath.open() as f:
            self.data = f.readlines()
        self.result: list[dict[str, list[str]]] = [defaultdict(list)]
        self.comments: list[None | str] = [None]
        self.comment_rules = []

    def parse(self):
        for rule in self.data:
            rule = rule.strip()
            if not rule:
                continue
            if self.is_comment(rule):
                comment_rule = rule[1:]
                comment_rule = comment_rule.split(",")
                comment_rule[0] = comment_rule[0].strip().upper()
                if comment_rule[0] in RULE_TYPES:
                    rule = ",".join(comment_rule)
                    self.comment_rules.append(rule)

                else:
                    self.comments.append(rule)
                    self.result.append(defaultdict(list))
                    continue
            rule = rule.split(",")
            rule_type, rule = rule[0], ",".join(rule[1:])
            rule_type = rule_type.upper()
            self.result[-1][rule_type].append(rule)

    def sort(self):
        for group_rules in self.result:
            for rule_type, rules in group_rules.items():
                if rule_type == "IP-CIDR":
                    rules = sorted(
                        rules, key=lambda x: ipaddress.IPv4Network(x).network_address
                    )
                elif rule_type == "IP-CIDR6":
                    rules = sorted(
                        rules, key=lambda x: ipaddress.IPv6Network(x).network_address
                    )
                elif rule_type == "ip_asn":
                    rules = sorted(
                        rules,
                        key=lambda x: int(x),
                    )
                else:
                    rules = sorted(rules, key=str.lower)
                group_rules[rule_type] = rules

    def output(self):
        contents = []
        for i, group_rules in enumerate(self.result):
            comment = self.comments[i]
            if comment is not None:
                contents.append(comment)
            for rule_type, rules in group_rules.items():
                contents.extend([f"{rule_type},{rule}" for rule in rules])
        for comment_rule in self.comment_rules:
            index = contents.index(comment_rule)
            contents[index] = "# " + comment_rule
        with self.filepath.open("w") as f:
            f.write("\n".join(contents))

    def format(self):
        self.parse()
        self.sort()
        self.output()

    def is_comment(self, rule: str) -> bool:
        for comment in COMMENTS:
            if rule.startswith(comment):
                return True


if __name__ == "__main__":
    parent_dir = Path(__file__).parent
    for format_dir in [parent_dir / "my-rules", parent_dir / "sources"]:
        for filepath in format_dir.iterdir():
            if filepath.suffix in [".txt", ".list"]:
                print(filepath)
                f = Format(filepath)
                f.format()
