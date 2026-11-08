import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from costrouter.classifier import classify
from costrouter.ledger import Ledger
from costrouter.providers import DEFAULT_CATALOG, ProviderCard
from costrouter.router import BudgetExceeded, NoCapableProvider, route
from costrouter import cli


class TestClassifier(unittest.TestCase):
    def test_trivial_greeting_is_tier1(self):
        self.assertEqual(classify("hello"), 1)

    def test_code_request_is_tier2(self):
        self.assertEqual(classify("write a function to sort a list"), 2)

    def test_proof_request_is_tier3(self):
        self.assertEqual(classify("prove this theorem about graphs"), 3)

    def test_huge_context_forces_tier3(self):
        self.assertEqual(classify("x " * 220_000), 3)

    def test_long_context_forces_at_least_tier2(self):
        self.assertEqual(classify("hi " * 40_000), 2)


class TestRouter(unittest.TestCase):
    def test_trivial_prompt_routes_to_free_local(self):
        d = route("hello")
        self.assertEqual(d.provider.name, "local-7b")
        self.assertEqual(d.estimated_cost, 0.0)

    def test_code_prompt_routes_to_mid(self):
        d = route("write a python function to parse csv")
        self.assertEqual(d.provider.name, "mid-general")

    def test_hard_prompt_routes_to_strong(self):
        d = route("prove the correctness of this algorithm and derive its complexity")
        self.assertEqual(d.provider.name, "strong-reason")

    def test_cheapest_capable_wins_not_highest_tier(self):
        d = route("hello")
        self.assertLess(d.provider.tier, 4)
        names = [n for n, _ in d.rejected]
        self.assertIn("frontier-max", names)

    def test_context_overflow_rejects_small_models(self):
        big = "word " * 40_000  # ~50k tokens
        d = route(big)
        self.assertGreaterEqual(d.provider.max_context, d.estimated_input_tokens)

    def test_no_capable_provider(self):
        tiny = [ProviderCard("weak", 0, 0.0, 0.0, 100, 10)]
        with self.assertRaises(NoCapableProvider):
            route("hello there friend", tiny)

    def test_budget_enforced(self):
        with self.assertRaises(BudgetExceeded):
            route("prove this theorem", max_cost_usd=0.0)

    def test_budget_passes_for_free_provider(self):
        d = route("hello", max_cost_usd=0.0)
        self.assertEqual(d.estimated_cost, 0.0)

    def test_rejections_are_explained(self):
        d = route("prove this theorem")
        reasons = dict(d.rejected)
        self.assertIn("mid-general", reasons)
        self.assertTrue(any("tier" in r or "expensive" in r for r in reasons.values()))


class TestLedger(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "ledger.json")
            led = Ledger()
            led.add("mid-general", 100, 200, 0.0005)
            led.add("local-7b", 10, 20, 0.0)
            led.save(p)
            loaded = Ledger.load(p)
            self.assertEqual(len(loaded.records), 2)
            self.assertAlmostEqual(loaded.total(), 0.0005)

    def test_total_since(self):
        led = Ledger()
        led.add("a", 1, 1, 1.0)
        led.records[0].ts = 0  # long ago
        led.add("b", 1, 1, 2.0)
        self.assertAlmostEqual(led.total(since=1), 2.0)


class TestCli(unittest.TestCase):
    def test_cli_explain(self):
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            rc = cli.main(["summarize this code", "--explain"])
        finally:
            sys.stdout = old
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("route:", out)
        self.assertIn("rejected:", out)

    def test_cli_budget_refusal(self):
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            rc = cli.main(["prove this theorem", "--budget", "0"])
        finally:
            sys.stdout = old
        self.assertEqual(rc, 2)
        self.assertIn("NO ROUTE", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
