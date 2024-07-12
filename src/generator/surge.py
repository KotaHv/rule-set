from loguru import logger

from model import RuleModel, SourceModel
from config import DIR_PATH


class SurgeGenerator:
    def __init__(self, *, info: SourceModel, rules: RuleModel) -> None:
        self.info = info
        self.rules = rules
        dir_path = DIR_PATH / "Surge"
        dir_path.mkdir(exist_ok=True)
        self.path = dir_path / (info.filename + ".list")

    def generate(self):
        content = ""
        if self.rules.logical:
            content += "\n".join(self.rules.logical)
            content += "\n"
        if self.rules.domain:
            content += "\n".join([f"DOMAIN,{domain}" for domain in self.rules.domain])
            content += "\n"
        if self.rules.domain_suffix:
            content += "\n".join(
                [
                    f"DOMAIN-SUFFIX,{domain_suffix}"
                    for domain_suffix in self.rules.domain_suffix
                ]
            )
            content += "\n"
        if self.rules.domain_keyword:
            content += "\n".join(
                [
                    f"DOMAIN-KEYWORD,{domain_keyword}"
                    for domain_keyword in self.rules.domain_keyword
                ]
            )
            content += "\n"
        if self.rules.domain_wildcard:
            content += "\n".join(
                [
                    f"DOMAIN-WILDCARD,{domain_wildcard}"
                    for domain_wildcard in self.rules.domain_wildcard
                ]
            )
            content += "\n"
        if self.info.no_resolve:
            if self.rules.ip_cidr:
                content += "\n".join(
                    [f"IP-CIDR,{ip_cidr},no-resolve" for ip_cidr in self.rules.ip_cidr]
                )
                content += "\n"
            if self.rules.ip_cidr6:
                content += "\n".join(
                    [
                        f"IP-CIDR6,{ip_cidr6},no-resolve"
                        for ip_cidr6 in self.rules.ip_cidr6
                    ]
                )
                content += "\n"
            if self.rules.ip_asn:
                content += "\n".join(
                    [f"IP-ASN,{ip_asn},no-resolve" for ip_asn in self.rules.ip_asn]
                )
                content += "\n"
        else:
            if self.rules.ip_cidr:
                content += "\n".join(
                    [f"IP-CIDR,{ip_cidr}" for ip_cidr in self.rules.ip_cidr]
                )
                content += "\n"
            if self.rules.ip_cidr6:
                content += "\n".join(
                    [f"IP-CIDR6,{ip_cidr6}" for ip_cidr6 in self.rules.ip_cidr6]
                )
                content += "\n"
            if self.rules.ip_asn:
                content += "\n".join(
                    [f"IP-ASN,{ip_asn}" for ip_asn in self.rules.ip_asn]
                )
                content += "\n"
        if self.rules.ua:
            content += "\n".join([f"USER-AGENT,{ua}" for ua in self.rules.ua])
            content += "\n"
        if self.rules.process:
            content += "\n".join(
                [f"PROCESS-NAME,{process}" for process in self.rules.process]
            )
            content += "\n"
        if content:
            with self.path.open("w") as f:
                f.write(content)
            logger.success(f"{self.path} generated successfully")
