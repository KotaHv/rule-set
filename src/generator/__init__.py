import ipaddress
from loguru import logger

from model import RuleModel, SourceModel, ClientEnum

from .egern import EgernGenerator
from .loon import LoonGenerator
from .surge import SurgeGenerator

CLIENT_GENERATOR = {
    ClientEnum.Egern: EgernGenerator,
    ClientEnum.Loon: LoonGenerator,
    ClientEnum.Surge: SurgeGenerator,
}


class Generator:
    def __init__(self, *, info: SourceModel, rules: RuleModel) -> None:
        self.info = info
        self.rules = rules
        self.sort()

    def sort(self):
        rules = self.rules.model_dump()
        for key, value in rules.items():
            if key == "ip_cidr":
                rules[key] = sorted(
                    value,
                    key=lambda x: ipaddress.IPv4Network(x).network_address,
                )
            elif key == "ip_cidr6":
                rules[key] = sorted(
                    value,
                    key=lambda x: ipaddress.IPv6Network(x).network_address,
                )
            elif key == "ip_asn":
                rules[key] = sorted(
                    value,
                    key=lambda x: int(x),
                )
            else:
                rules[key] = sorted(value)
        self.rules = RuleModel(**rules)

    def generate(self):
        logger.info(f"Start generating {self.info.filename}")
        clients = list(CLIENT_GENERATOR.keys())
        if self.info.include:
            clients = self.info.include
        elif self.info.exclude:
            for client in self.info.exclude:
                clients.remove(client)
        for client in clients:
            CLIENT_GENERATOR[client](info=self.info, rules=self.rules).generate()
