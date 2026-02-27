# 配置说明（configs/*.yaml）

## data
- `source`: `binance` / `local`
- `binance.base_url`: REST base url（默认 https://api.binance.com）
- `binance.proxy`: 可选代理（也支持 HTTP(S)_PROXY 环境变量）
- `binance.days`: 拉取近 N 天数据（默认 30）
- `cache.enabled`: 是否缓存到 runs/cache/ 或自定义目录
- `cache.dir`: 缓存目录（parquet）

## universe
- `symbols`: 合约列表（示例 spot：BTCUSDT 等）

## backtest
- `base_tf`: 基准时间轴
- `fwd_period`: label 未来多少期（4×15m=1h）
- `top_n/bottom_n`: 每期多空数量
- `fee_rate/slippage`: 成本
- `capital`: 资金规模
- `index_mode`: union/intersection

## mining
- `enabled`: 是否自动挖掘
- `ic_window`: IC 统计窗口
- `ic_min_abs`: |mean IC| 门槛
- `icir_min_abs`: |ICIR| 门槛
- `max_valid`: 最多保留多少个有效因子

## optimizer
CVXPy 因子权重优化：
- `lam_risk`: 风险/共线惩罚
- `lam_l1`: 稀疏惩罚
- `lam_tc`: 换手惩罚
- `w_max`: 单因子权重上限
- `l1_cap`: 因子权重 L1 上限

## strategy_pool
- `max_active`: 同时活跃策略数（建议 3–10）
- `replace_each_n_steps`: 每隔多少步检查替换
- `score_window`: 计算策略健康分的窗口长度
