"""Spend ledger: per-call cost accounting with budget windows."""

import json
import time
from dataclasses import asdict, dataclass, field


@dataclass
class SpendRecord:
    ts: float
    provider: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


@dataclass
class Ledger:
    records: list[SpendRecord] = field(default_factory=list)

    def add(self, provider: str, input_tokens: int, output_tokens: int, cost_usd: float) -> SpendRecord:
        rec = SpendRecord(time.time(), provider, input_tokens, output_tokens, cost_usd)
        self.records.append(rec)
        return rec

    def total(self, since: float | None = None) -> float:
        return sum(r.cost_usd for r in self.records if since is None or r.ts >= since)

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in self.records], f, indent=2)

    @classmethod
    def load(cls, path: str) -> "Ledger":
        try:
            with open(path, encoding="utf-8") as f:
                return cls([SpendRecord(**r) for r in json.load(f)])
        except FileNotFoundError:
            return cls()
