import json

from .base import BaseSerialize
from ..logical import sing_box_logical_serialize


class Serialize(BaseSerialize):
    def serialize(self) -> str:
        json_data = {"version": 1, "rules": [{}]}
        if rules := self.rules.domain:
            json_data["rules"][0]["domain"] = rules
        if rules := self.rules.domain_suffix:
            json_data["rules"][0]["domain_suffix"] = rules
        if rules := self.rules.domain_keyword:
            json_data["rules"][0]["domain_keyword"] = rules
        if rules := self.rules.ip_cidr:
            json_data["rules"][0]["ip_cidr"] = rules
        if rules := self.rules.ip_cidr6:
            if json_data["rules"][0]["ip_cidr"]:
                json_data["rules"][0]["ip_cidr"].extend(rules)
            else:
                json_data["rules"][0]["ip_cidr"] = rules
        if rules := self.rules.process:
            if json_data["rules"][0]:
                json_data["rules"].append({"process_name": rules})
            else:
                json_data["rules"][0]["process_name"] = rules
        if rules := self.rules.logical:
            for rule in rules:
                logical_rule = sing_box_logical_serialize(root_node=rule)
                if logical_rule:
                    json_data["rules"].append(logical_rule)
        if json_data["rules"][0]:
            return json.dumps(json_data)
        return ""
