from anytree import RenderTree


class UnsupportedRuleTypeError(Exception):
    def __init__(self, rule_type: str):
        super().__init__(f"Unsupported rule type: {rule_type}")


class SerializeError(Exception):
    def __init__(self, err: str, node=None):
        if node:
            err_list = [
                "",
                *[f"{pre}{node.name}" for pre, _, node in RenderTree(node)],
                err,
            ]
        else:
            err_list = [err]
        super().__init__("\n".join(err_list))
