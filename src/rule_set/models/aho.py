# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnannotatedClassAttribute=false
import json
from collections.abc import Iterable

import ahocorasick

from rule_set.utils import generate_cache_key

AHO_CACHE: dict[str, ahocorasick.Automaton] = {}


class Aho:
    def __init__(self, keywords: Iterable[str]):
        keywords = sorted(set(keywords))
        cache_key = generate_cache_key(json.dumps(keywords))
        aho = AHO_CACHE.get(cache_key)
        if aho is None:
            aho = ahocorasick.Automaton()
            for keyword in keywords:
                aho.add_word(keyword, keyword)
            aho.make_automaton()
            AHO_CACHE[cache_key] = aho
        self.aho = aho

    def matched(self, text: str) -> tuple[bool, str | None]:
        for _, keyword in self.aho.iter(text):
            return True, keyword
        return False, None

    def is_duplicate(self, text: str) -> tuple[bool, str | None]:
        for _, keyword in self.aho.iter(text):
            if keyword != text:
                return True, keyword
        return False, None
