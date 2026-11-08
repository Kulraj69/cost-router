"""Reproduces the demo video's real output: tiered routing + budget cap."""
from costrouter.router import route

CASES = [
    ("What is the capital of France?", None),
    ("Summarize this 3-line email in one sentence.", None),
    ("Refactor this distributed lock manager to avoid split-brain under network partition, then prove liveness. " * 8, None),
    ("Refactor this distributed lock manager to avoid split-brain under network partition, then prove liveness. " * 8, 0.001),
]
if __name__ == "__main__":
    for prompt, cap in CASES:
        print(prompt[:60] + ("..." if len(prompt) > 60 else ""))
        try:
            d = route(prompt, max_cost_usd=cap)
            print(f"  -> {d.provider.name} (tier {d.required_tier}) ~${d.estimated_cost:.6f}")
            for name, why in d.rejected:
                print(f"     rejected {name}: {why}")
        except Exception as e:
            print(f"  x {type(e).__name__}: {e}")
