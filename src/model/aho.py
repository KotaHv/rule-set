import ahocorasick

from utils import generate_cache_key

AHO_CACHE: dict[str, ahocorasick.Automaton] = {}


class Aho:
    def __init__(self, keywords: list[str]):
        cache_key = generate_cache_key(keywords)
        self.aho = AHO_CACHE.get(cache_key)
        if self.aho is None:
            self.aho = ahocorasick.Automaton()
            for keyword in keywords:
                self.aho.add_word(keyword, keyword)
            self.aho.make_automaton()
            AHO_CACHE[cache_key] = self.aho

    def matched(self, text: str) -> tuple[bool, str | None]:
        for _, keyword in self.aho.iter(text):
            return True, keyword
        return False, None

    def is_duplicate(self, text: str) -> tuple[bool, str | None]:
        for _, keyword in self.aho.iter(text):
            if keyword != text:
                return True, keyword
        return False, None
