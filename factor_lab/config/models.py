from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, HttpUrl, model_validator

class BinanceCfg(BaseModel):
    base_url: str = "https://api.binance.com"
    proxy: str = ""
    days: int = 30
    rate_limit_sleep_ms: int = 200
    timeout_s: int = 20

class CacheCfg(BaseModel):
    enabled: bool = True
    dir: str = "./runs/cache"

class DataCfg(BaseModel):
    source: Literal["binance", "local"] = "binance"
    binance: BinanceCfg = BinanceCfg()
    cache: CacheCfg = CacheCfg()
    local_path: Optional[str] = None

class UniverseCfg(BaseModel):
    symbols: List[str]

class BacktestCfg(BaseModel):
    base_tf: str = "15m"
    fwd_period: int = 4
    top_n: int = 3
    bottom_n: int = 3
    fee_rate: float = 0.0005
    slippage: float = 0.0002
    capital: float = 1_000_000
    index_mode: Literal["union","intersection"] = "union"

class MiningCfg(BaseModel):
    enabled: bool = True
    ic_window: int = 256
    ic_min_abs: float = 0.02
    icir_min_abs: float = 0.30
    max_valid: int = 10
    min_cs: int = 6

class ResearchCfg(BaseModel):
    winsor_p: float = 0.01
    use_orthogonal: bool = True

class OptimizerCfg(BaseModel):
    lam_risk: float = 3.0
    lam_l1: float = 0.08
    lam_tc: float = 0.15
    w_max: float = 0.60
    l1_cap: float = 1.0

class StrategyPoolCfg(BaseModel):
    enabled: bool = True
    max_active: int = 6
    score_window: int = 192
    replace_each_n_steps: int = 96

class ExecutionCfg(BaseModel):
    n_slices: int = 4
    impact_c: float = 0.10
    impact_p: float = 0.50

class ReportCfg(BaseModel):
    out_dir: str = "./runs"
    topk: int = 10

class AppCfg(BaseModel):
    data: DataCfg
    universe: UniverseCfg
    timeframes: List[str] = Field(default_factory=lambda: ["1m","5m","15m","1h"])
    backtest: BacktestCfg = BacktestCfg()
    mining: MiningCfg = MiningCfg()
    research: ResearchCfg = ResearchCfg()
    optimizer: OptimizerCfg = OptimizerCfg()
    strategy_pool: StrategyPoolCfg = StrategyPoolCfg()
    execution: ExecutionCfg = ExecutionCfg()
    report: ReportCfg = ReportCfg()

    @model_validator(mode="after")
    def _check(self):
        if self.backtest.top_n <= 0 or self.backtest.bottom_n <= 0:
            raise ValueError("top_n/bottom_n must be > 0")
        if self.backtest.fwd_period <= 0:
            raise ValueError("fwd_period must be > 0")
        if self.mining.max_valid <= 0:
            raise ValueError("mining.max_valid must be > 0")
        return self
