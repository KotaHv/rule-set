# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
from pathlib import Path

import maxminddb

from rule_set.models import RuleModel


def parse(filepath: Path, country_code: str | None = None) -> RuleModel:
    rules = RuleModel()
    with maxminddb.open_database(filepath) as reader:
        if country_code is None:
            for ip, _ in reader:
                ip_cidr = rules.ip_cidr if ip.version == 4 else rules.ip_cidr6
                ip_cidr.add(str(ip))
        else:
            for ip, info in reader:
                if not info:
                    continue
                if info["country"]["iso_code"] == country_code:
                    ip_cidr = rules.ip_cidr if ip.version == 4 else rules.ip_cidr6
                    ip_cidr.add(str(ip))
    return rules
