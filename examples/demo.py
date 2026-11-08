"""Route a mix of prompts and show the bill."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from costrouter.ledger import Ledger
from costrouter.router import route

PROMPTS = [
    "hello",
    "translate 'good morning' to french",
    "write a function to dedupe a list",
    "explain how a hash map works",
    "prove that mergesort is O(n log n) and derive the recurrence",
]

ledger = Ledger()
for p in PROMPTS:
    d = route(p)
    ledger.add(d.provider.name, d.estimated_input_tokens, d.estimated_output_tokens, d.estimated_cost)
    print(f"{p[:45]:47} -> {d.provider.name:14} ${d.estimated_cost:.6f}")
print(f"\ntotal for {len(ledger.records)} calls: ${ledger.total():.6f}")
naive = sum(route(p).estimated_cost for p in PROMPTS)  # baseline below
# naive: everything to frontier
from costrouter.providers import DEFAULT_CATALOG
frontier = DEFAULT_CATALOG[-1]
naive = sum(frontier.estimate_cost(route(p).estimated_input_tokens, route(p).estimated_output_tokens) for p in PROMPTS)
print(f"naive all-frontier bill:           ${naive:.6f}")
