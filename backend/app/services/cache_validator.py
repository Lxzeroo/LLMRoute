import re
from collections import Counter


class CacheValidator:

    NEGATIONS = {
        "not", "never", "no", "without",
        "cannot", "isn't", "aren't", "don't",
        "doesn't", "won't", "can't"
    }

    VOLATILE_TERMS = {
        "today", "tomorrow", "yesterday",
        "latest", "current", "currently",
        "now", "live", "recent", "tonight"
    }

    INTENT_GROUPS = {
        "explanation": {
            "what", "explain", "define", "describe"
        },
        "comparison": {
            "compare", "difference", "versus", "vs"
        },
        "calculation": {
            "calculate", "compute", "solve"
        },
        "implementation": {
            "implement", "build", "create",
            "write", "generate"
        },
        "troubleshooting": {
            "debug", "fix", "error", "troubleshoot"
        }
    }

    @staticmethod
    def words(text):
        text = text.lower().replace("\u2019", "'")

        tokens = re.findall(r"\b[\w']+\b", text)

        return {
            token[:-2] if token.endswith("'s") else token
            for token in tokens
        }

    @staticmethod
    def numbers(text):
        return Counter(
            re.findall(
                r"(?<!\d)[+-]?\d+(?:\.\d+)*%?",
                text
            )
        )

    def intent(self, text):
        words = self.words(text)

        return {
            intent
            for intent, keywords in self.INTENT_GROUPS.items()
            if words & keywords
        }

    def cacheable(self, query):

        words = self.words(query)

        if words & self.VOLATILE_TERMS:
            return False

        return True

    def validate(self, query, cached_query):

        if not self.cacheable(query):
            return False, "Time-sensitive query"

        if not self.cacheable(cached_query):
            return False, "Time-sensitive cached query"

        if self.numbers(query) != self.numbers(cached_query):
            return False, "Numerical mismatch"

        query_negation = self.words(query) & self.NEGATIONS
        cached_negation = self.words(cached_query) & self.NEGATIONS

        if query_negation != cached_negation:
            return False, "Negation mismatch"

        query_intent = self.intent(query)
        cached_intent = self.intent(cached_query)

        if (
            query_intent
            and cached_intent
            and query_intent.isdisjoint(cached_intent)
        ):
            return False, "Intent mismatch"

        return True, "Validation passed"


cache_validator = CacheValidator()
