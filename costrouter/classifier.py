"""Rule-based request classifier: maps a prompt to the minimum capability tier.

Deliberately deterministic and inspectable - the point of cost-aware routing
is that the routing decision itself must be nearly free and fully auditable.
"""

import re

HARD_SIGNALS = [
    r"\bprove\b", r"\btheorem\b", r"\bformal(ly|ize)?\b", r"\bderive\b",
    r"\barchitect(ure)?\b", r"\boptimize.*(complexity|proof)\b",
    r"\bmulti[- ]?step reasoning\b", r"\bnovel\b",
]
STANDARD_SIGNALS = [
    r"\bcode\b", r"\bfunction\b", r"\bdebug\b", r"\brefactor\b",
    r"\bexplain\b", r"\bsummar(ize|y)\b", r"\bcompare\b", r"\banalyz",
    r"\bwrite\b", r"\bdraft\b",
]
TRIVIAL_SIGNALS = [
    r"^(hi|hello|hey|thanks|ok|yes|no)\b",
    r"\btranslate\b", r"\bspell\b", r"\bdefine\b", r"\bformat\b",
]

LONG_CONTEXT_TOKENS = 24_000   # needs at least mid-tier context
HARD_CONTEXT_TOKENS = 100_000  # needs strong-tier context


def classify(prompt: str, approx_tokens: int | None = None) -> int:
    """Return the minimum capability tier (0-4) a prompt likely needs."""
    tokens = approx_tokens if approx_tokens is not None else len(prompt) // 4
    text = prompt.lower()

    if tokens >= HARD_CONTEXT_TOKENS:
        return 3
    tier = 0
    if any(re.search(p, text) for p in TRIVIAL_SIGNALS):
        tier = 1
    if any(re.search(p, text) for p in STANDARD_SIGNALS):
        tier = max(tier, 2)
    if any(re.search(p, text) for p in HARD_SIGNALS):
        tier = max(tier, 3)
    if tokens >= LONG_CONTEXT_TOKENS:
        tier = max(tier, 2)
    return tier
