from pathlib import Path

import maxminddb

from model import RuleModel


def deserialize(filepath: Path, country_code: str | None = None) -> RuleModel:
    rules = RuleModel()
    with maxminddb.open_database(filepath) as reader:
        if country_code is None:
            for ip, _ in reader:
                rules.ip_trie.add(str(ip))
        else:
            for ip, info in reader:
                if not info:
                    continue
                if info["country"]["iso_code"] == country_code:
                    rules.ip_trie.add(str(ip))
    return rules
