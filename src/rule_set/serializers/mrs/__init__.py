"""Pure Python mihomo rule-set (MRS) encoder."""

from .encoder import MrsBehavior, encode_domain, encode_ipcidr

__all__ = ["MrsBehavior", "encode_domain", "encode_ipcidr"]
