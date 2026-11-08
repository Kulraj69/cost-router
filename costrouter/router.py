"""The router: pick the cheapest provider that meets the request's needs."""

from dataclasses import dataclass

from .classifier import classify
from .providers import DEFAULT_CATALOG, ProviderCard


@dataclass(frozen=True)
class RouteDecision:
    provider: ProviderCard
    required_tier: int
    estimated_cost: float
    estimated_input_tokens: int
    estimated_output_tokens: int
    rejected: tuple  # (provider_name, reason) for every card not chosen


class NoCapableProvider(Exception):
    pass


class BudgetExceeded(Exception):
    pass


def estimate_tokens(prompt: str, expected_output: int = 512) -> tuple[int, int]:
    return max(1, len(prompt) // 4), expected_output


def route(prompt: str,
          catalog: list[ProviderCard] | None = None,
          expected_output_tokens: int = 512,
          max_cost_usd: float | None = None) -> RouteDecision:
    """Choose the cheapest provider that can handle the prompt.

    Raises NoCapableProvider if nothing in the catalog can meet the required
    tier/context, BudgetExceeded if the cheapest capable provider would cost
    more than max_cost_usd.
    """
    catalog = catalog or DEFAULT_CATALOG
    in_tok, out_tok = estimate_tokens(prompt, expected_output_tokens)
    tier = classify(prompt, in_tok)

    rejected = []
    candidates = []
    for card in catalog:
        if card.tier < tier:
            rejected.append((card.name, f"capability tier {card.tier} < required {tier}"))
        elif card.max_context < in_tok + out_tok:
            rejected.append((card.name, f"context {card.max_context} < needed {in_tok + out_tok}"))
        else:
            candidates.append(card)
    if not candidates:
        raise NoCapableProvider(f"no provider meets tier {tier} / {in_tok + out_tok} tokens")

    # cheapest first; latency breaks ties
    candidates.sort(key=lambda c: (c.estimate_cost(in_tok, out_tok), c.avg_latency_ms))
    best = candidates[0]
    cost = best.estimate_cost(in_tok, out_tok)
    if max_cost_usd is not None and cost > max_cost_usd:
        raise BudgetExceeded(f"cheapest capable provider {best.name} costs ${cost:.6f} > budget ${max_cost_usd:.6f}")
    rejected.extend((c.name, "more expensive") for c in candidates[1:])
    return RouteDecision(best, tier, cost, in_tok, out_tok, tuple(rejected))
