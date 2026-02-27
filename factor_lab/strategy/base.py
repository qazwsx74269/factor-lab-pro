from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

@dataclass
class StrategySignal:
    name: str
    weights: pd.Series  # symbol -> target weight
    meta: dict

class Strategy:
    name: str = "base"
    def on_bar(self, t, panel_t: pd.DataFrame) -> StrategySignal:
        raise NotImplementedError
