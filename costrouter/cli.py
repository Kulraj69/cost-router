"""CLI: route a prompt, explain the decision, track spend.

    python -m costrouter "summarize this diff" --explain
    python -m costrouter "prove the halting lemma" --budget 0.001
"""

import argparse
import json
import sys

from .providers import DEFAULT_CATALOG
from .router import BudgetExceeded, NoCapableProvider, route


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="costrouter", description="Cost-aware model router (offline, rule-based).")
    ap.add_argument("prompt", nargs="?", help="prompt text; omit with --stdin")
    ap.add_argument("--stdin", action="store_true", help="read prompt from stdin")
    ap.add_argument("--budget", type=float, default=None, help="max USD allowed for this call")
    ap.add_argument("--expected-output", type=int, default=512, help="expected output tokens")
    ap.add_argument("--explain", action="store_true", help="show rejected providers and reasons")
    args = ap.parse_args(argv)

    prompt = sys.stdin.read() if args.stdin else (args.prompt or "")
    if not prompt.strip():
        ap.error("empty prompt")

    try:
        d = route(prompt, DEFAULT_CATALOG, args.expected_output, args.budget)
    except (NoCapableProvider, BudgetExceeded) as e:
        print(f"NO ROUTE: {e}")
        return 2

    print(f"route: {d.provider.name} (tier {d.provider.tier})")
    print(f"required tier: {d.required_tier}")
    print(f"est tokens: {d.estimated_input_tokens} in / {d.estimated_output_tokens} out")
    print(f"est cost: ${d.estimated_cost:.6f}")
    if args.explain:
        print("rejected:")
        for name, why in d.rejected:
            print(f"  - {name}: {why}")
    print(json.dumps({"provider": d.provider.name, "cost_usd": d.estimated_cost}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
