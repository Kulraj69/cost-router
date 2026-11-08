"""Provider catalog: static capability + price cards for model providers.

Prices are USD per 1M tokens (input, output) and are illustrative defaults -
swap in real rate cards from each provider's pricing page before production
use. capability is an integer tier: higher tiers can handle everything lower
tiers can (0=trivial, 1=simple, 2=standard, 3=hard reasoning, 4=frontier).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCard:
    name: str
    tier: int                 # capability tier this model tops out at
    input_per_mtok: float     # USD per 1M input tokens
    output_per_mtok: float    # USD per 1M output tokens
    max_context: int          # tokens
    avg_latency_ms: int       # rough p50 latency, for tie-breaking

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens * self.input_per_mtok
                + output_tokens * self.output_per_mtok) / 1_000_000


# Offline default catalog (illustrative prices, not live quotes).
DEFAULT_CATALOG = [
    ProviderCard("local-7b",      tier=1, input_per_mtok=0.0,  output_per_mtok=0.0,  max_context=8_192,   avg_latency_ms=800),
    ProviderCard("cheap-small",   tier=1, input_per_mtok=0.10, output_per_mtok=0.40, max_context=32_000,  avg_latency_ms=300),
    ProviderCard("mid-general",   tier=2, input_per_mtok=0.80, output_per_mtok=2.40, max_context=128_000, avg_latency_ms=900),
    ProviderCard("strong-reason", tier=3, input_per_mtok=3.00, output_per_mtok=9.00, max_context=200_000, avg_latency_ms=2500),
    ProviderCard("frontier-max",  tier=4, input_per_mtok=15.0, output_per_mtok=60.0, max_context=200_000, avg_latency_ms=4000),
]
