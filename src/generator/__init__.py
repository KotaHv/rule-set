import ipaddress
from loguru import logger

from model import RuleModel, SourceModel, ClientEnum


class Generator:
    def __init__(self, *, info: SourceModel, rules: RuleModel) -> None:
        self.info = info
        self.rules = rules
        self.sort()
        from .egern import EgernGenerator
        from .loon import LoonGenerator
        from .surge import SurgeGenerator
        from .clash import ClashGenerator
        from .sing_box import SingBoxGenerator

        self.client_generator = {
            ClientEnum.Egern: EgernGenerator,
            ClientEnum.Loon: LoonGenerator,
            ClientEnum.Surge: SurgeGenerator,
            ClientEnum.Clash: ClashGenerator,
            ClientEnum.Sing_Box: SingBoxGenerator,
        }

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
        clients = list(self.client_generator.keys())
        if self.info.include:
            clients = self.info.include
        elif self.info.exclude:
            for client in self.info.exclude:
                clients.remove(client)
        for client in clients:
            self.client_generator[client](info=self.info, rules=self.rules).generate()