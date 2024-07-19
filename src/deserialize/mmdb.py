from pathlib import Path

import maxminddb

from model import RuleModel


def deserialize(filepath: Path) -> RuleModel:
    rules = RuleModel()
    with maxminddb.open_database(filepath) as reader:
        for ip, _ in reader:
            ip_cidr_list = rules.ip_cidr if ip.version == 4 else rules.ip_cidr6
            ip_cidr_list.add(str(ip))
    return rules
