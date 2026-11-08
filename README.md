# cost-router

Cost-aware model routing - project #6 ("Cost-Aware Model Router") from the
TOP 1% AI projects list. Sends each request to the cheapest model that can
actually handle it, and refuses to spend over budget.

## Why

Naive agent stacks send every prompt to the frontier model. Most prompts
(greetings, formatting, simple Q&A) don't need it. Routing is where the money
is saved - but the routing decision itself must be nearly free and fully
auditable, so this router is deliberately **rule-based**, not another LLM call.

## What it does

- **classifier**: maps a prompt to the minimum capability tier it needs
  (trivial -> frontier), using inspectable heuristics: task-type signals and
  context length. No model call, no network.
- **router**: picks the cheapest provider that meets the required tier and
  context window, with latency tie-breaks. Raises instead of overspending
  when a `--budget` cap would be exceeded.
- **ledger**: per-call cost accounting with time-windowed totals, saved as
  JSON - the receipt trail a spending firewall (see `leash`) can audit.

## Scope

Deterministic and offline by design. The bundled provider catalog uses
illustrative prices - swap in real rate cards before production use. Pair with
`trajectory-eval` to measure whether routing down ever hurts quality, and with
`agent-lab` as the requesting agent.

## Run it

```bash
python -m costrouter "summarize this diff" --explain
python -m costrouter "prove the halting lemma" --budget 0.001   # refused
```

## Test

```bash
python -m unittest discover -s tests
```

15 tests cover tier classification, cheapest-capable routing, context-window
rejection, budget enforcement, ledger accounting, and the CLI.

## Demo

`demo.py` reproduces the recorded demo run end to end, offline (standard
library only, no model calls):

    python demo.py

It executes the library's real code path and prints the same output shown in
the recorded demo video.
