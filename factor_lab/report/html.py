from __future__ import annotations
import os
import math
from datetime import datetime

import numpy as np
import pandas as pd
from jinja2 import Template

TPL = Template("""<!doctype html>
<html><head><meta charset="utf-8"/>
<title>{{ title }}</title>
<style>
:root{
  --bg:#f6f8fb;
  --card:#ffffff;
  --text:#18212f;
  --muted:#64748b;
  --border:#dbe3ee;
  --green:#16a34a;
  --red:#dc2626;
  --blue:#2563eb;
  --amber:#d97706;
}
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial;margin:0;background:var(--bg);color:var(--text);line-height:1.55;}
.wrapper{max-width:1180px;margin:0 auto;padding:24px;}
.hero{background:linear-gradient(135deg,#0f172a,#1d4ed8);color:#fff;border-radius:18px;padding:24px 28px;margin-bottom:18px;box-shadow:0 10px 30px rgba(15,23,42,.18);}
.hero h1{margin:0 0 8px 0;font-size:30px;}
.hero p{margin:8px 0;color:rgba(255,255,255,.88)}
.hero .muted{color:rgba(255,255,255,.72);font-size:14px}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px;margin-bottom:16px;}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:18px;box-shadow:0 4px 14px rgba(15,23,42,.05);}
.span-12{grid-column:span 12}
.span-8{grid-column:span 8}
.span-6{grid-column:span 6}
.span-4{grid-column:span 4}
.span-3{grid-column:span 3}
h2{margin:0 0 12px 0;font-size:20px}
h3{margin:0 0 10px 0;font-size:16px}
p,li{font-size:14px}
small,.muted{color:var(--muted)}
.metric{display:flex;flex-direction:column;gap:6px}
.metric .label{font-size:13px;color:var(--muted)}
.metric .value{font-size:28px;font-weight:700;letter-spacing:-.02em}
.good{color:var(--green)}
.bad{color:var(--red)}
.neutral{color:var(--blue)}
.kbd{display:inline-block;padding:2px 8px;border:1px solid var(--border);border-radius:999px;background:#f8fafc;color:#334155;font-size:12px}
.note{padding:12px 14px;border-radius:12px;background:#eff6ff;border:1px solid #bfdbfe;color:#1e3a8a;font-size:14px}
.warn{background:#fff7ed;border-color:#fdba74;color:#9a3412}
.goodbox{background:#f0fdf4;border-color:#86efac;color:#166534}
.table-wrap{overflow:auto;border:1px solid var(--border);border-radius:12px}
table{border-collapse:collapse;width:100%;background:white;}
th,td{border-bottom:1px solid #e6edf5;padding:9px 10px;font-size:12px;text-align:left;vertical-align:top;white-space:nowrap;}
th{background:#f8fafc;color:#334155;position:sticky;top:0}
tr:hover td{background:#fafcff}
.explain-list{padding-left:18px;margin:8px 0}
.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-bottom:8px}
.legend span::before{content:'';display:inline-block;width:10px;height:10px;border-radius:99px;margin-right:6px;vertical-align:middle}
.legend .blue::before{background:var(--blue)}
.legend .red::before{background:var(--red)}
.legend .green::before{background:var(--green)}
svg.chart{width:100%;height:auto;display:block;background:linear-gradient(180deg,#fff,#f8fbff);border:1px solid var(--border);border-radius:12px}
.footer{margin-top:18px;color:var(--muted);font-size:12px}
@media (max-width: 900px){
  .span-8,.span-6,.span-4,.span-3{grid-column:span 12}
  .hero h1{font-size:24px}
}
</style></head><body>
<div class="wrapper">
  <div class="hero">
    <h1>{{ title }}</h1>
    <p>{{ summary_sentence }}</p>
    <div class="muted">Generated at {{ gen_time }} · This page is written for both researchers and beginners.</div>
  </div>

  <div class="grid">
    <div class="card span-3"><div class="metric"><div class="label">最终资金曲线</div><div class="value {{ total_return_class }}">{{ final_equity }}</div><div class="muted">初始净值 = 1.0</div></div></div>
    <div class="card span-3"><div class="metric"><div class="label">总收益</div><div class="value {{ total_return_class }}">{{ total_return }}</div><div class="muted">看结果有没有真正赚到钱</div></div></div>
    <div class="card span-3"><div class="metric"><div class="label">最大回撤</div><div class="value {{ drawdown_class }}">{{ max_drawdown }}</div><div class="muted">亏得最难受的一段有多深</div></div></div>
    <div class="card span-3"><div class="metric"><div class="label">胜率 / 交易步数</div><div class="value neutral">{{ win_rate }}</div><div class="muted">{{ steps }} steps</div></div></div>
  </div>

  <div class="grid">
    <div class="card span-8">
      <h2>1. 这套东西到底能不能赚钱？</h2>
      <div class="legend"><span class="blue">资金曲线</span><span class="red">回撤</span></div>
      {{ equity_chart | safe }}
      <ul class="explain-list">
        <li><b>资金曲线向右上</b>：说明策略整体在赚钱。</li>
        <li><b>回撤太深</b>：说明虽然可能赚钱，但中间会很痛苦，很多人拿不住。</li>
        <li><b>如果收益不高、回撤很深</b>：这个因子/组合就算统计上好看，也不适合实盘。</li>
      </ul>
    </div>
    <div class="card span-4">
      <h2>2. 小白应该怎么用这份报告？</h2>
      <div class="note goodbox">先别急着追“神因子”。先看：<b>赚钱是否稳定</b>、<b>回撤能不能扛</b>、<b>成本吃不吃掉利润</b>。</div>
      <ol class="explain-list">
        <li>先看 <b>总收益</b> 是否明显大于 0。</li>
        <li>再看 <b>最大回撤</b> 是否在你能接受范围内。</li>
        <li>再看 <b>Top factors</b> 里哪些因子长期稳定排前面。</li>
        <li>最后才考虑实盘：优先用 <b>高 ICIR + 低回撤 + 成本后仍赚钱</b> 的组合。</li>
      </ol>
      <div class="note warn">一个实用原则：<b>先找稳，再找猛</b>。稳定赚钱的慢系统，通常比忽上忽下的暴利曲线更容易落地。</div>
    </div>
  </div>

  <div class="grid">
    <div class="card span-6">
      <h2>3. 因子质量怎么看</h2>
      <ul class="explain-list">
        <li><b>IC</b>：因子和未来收益的相关性。绝对值越大，说明越有预测力。</li>
        <li><b>ICIR</b>：IC 的稳定性。越大说明不是“碰巧这几次有效”。</li>
        <li><b>|ICIR| 高但收益差</b>：可能方向对了，但成本、换手、组合方式拖了后腿。</li>
        <li><b>收益高但 ICIR 很飘</b>：可能只是样本运气好，小白别直接上真钱。</li>
      </ul>
      <div class="note">实战上，优先挑 <b>ICIR 更稳定</b> 的因子，再去做组合优化，比只看单次爆发收益靠谱。</div>
    </div>
    <div class="card span-6">
      <h2>4. 这几个回测指标是什么意思</h2>
      <ul class="explain-list">
        <li><b>ret_hold</b>：不考虑交易成本时，这一步本来能赚多少。</li>
        <li><b>ret</b>：扣掉费率、滑点、冲击成本后，真正落袋的收益。</li>
        <li><b>equity</b>：累计资金曲线。</li>
        <li><b>cost</b> 很高：说明这个策略可能理论赚钱、实盘不赚钱。</li>
      </ul>
      <div class="note warn">如果 <b>ret_hold 很漂亮，但 ret 很一般</b>，说明你赚到的是“纸面利润”，不是能真正拿到手的钱。</div>
    </div>
  </div>

  <div class="grid">
    <div class="card span-12">
      <h2>5. Top Factors（重点看稳定性）</h2>
      {{ factor_table | safe }}
    </div>
  </div>

  <div class="grid">
    <div class="card span-12">
      <h2>6. 最近回测明细</h2>
      {{ tail_table | safe }}
    </div>
  </div>

  <div class="grid">
    <div class="card span-12">
      <h2>7. Strategy Pool Scores</h2>
      {{ pool_table | safe }}
    </div>
  </div>

  <div class="footer">
    <div>Tips for beginners: 不要把这份报告当成“买卖指令”，而要当成“筛选系统”。先用它找出 <b>稳定因子</b>，再决定是否实盘。</div>
  </div>
</div>
</body></html>""")


def _safe_float(x, default=0.0):
    try:
        v = float(x)
        if math.isfinite(v):
            return v
    except Exception:
        pass
    return default


def _pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def _to_html_table(df: pd.DataFrame, n=20):
    if df is None or df.empty:
        return "<div class='muted'>(empty)</div>"
    return f"<div class='table-wrap'>{df.head(n).to_html(index=False, escape=True, float_format=lambda x: f'{x:.6g}')}</div>"


def _build_equity_metrics(df: pd.DataFrame):
    if df.empty or "equity" not in df.columns:
        return {
            "final_equity": 1.0,
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "equity_curve": pd.Series([1.0]),
            "drawdown_curve": pd.Series([0.0]),
        }

    equity = df["equity"].astype(float).replace([np.inf, -np.inf], np.nan).ffill().dropna()
    if equity.empty:
        equity = pd.Series([1.0])
    peak = equity.cummax()
    drawdown = equity / peak - 1.0

    ret = df.get("ret", pd.Series(dtype=float))
    ret = ret.astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    win_rate = float((ret > 0).mean()) if len(ret) else 0.0

    return {
        "final_equity": _safe_float(equity.iloc[-1], 1.0),
        "total_return": _safe_float(equity.iloc[-1] - 1.0, 0.0),
        "max_drawdown": _safe_float(drawdown.min(), 0.0),
        "win_rate": win_rate,
        "equity_curve": equity.reset_index(drop=True),
        "drawdown_curve": drawdown.reset_index(drop=True),
    }


def _series_to_path(values: pd.Series, width=900, height=280, pad=28):
    vals = [float(v) for v in values.tolist()] if len(values) else [0.0]
    if len(vals) == 1:
        vals = vals * 2
    vmin, vmax = min(vals), max(vals)
    if abs(vmax - vmin) < 1e-12:
        vmax += 1e-9
        vmin -= 1e-9

    xs = np.linspace(pad, width - pad, len(vals))
    ys = [height - pad - (v - vmin) / (vmax - vmin) * (height - 2 * pad) for v in vals]
    path = "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in zip(xs, ys))
    return path, vmin, vmax, xs, ys


def _svg_line_chart(equity: pd.Series, drawdown: pd.Series):
    width, height, pad = 920, 320, 32
    e_path, e_min, e_max, xs, ys = _series_to_path(equity, width=width, height=height, pad=pad)
    d_path, d_min, d_max, _, dys = _series_to_path(drawdown, width=width, height=height, pad=pad)

    grid = []
    for i in range(5):
        y = pad + i * (height - 2 * pad) / 4
        grid.append(f'<line x1="{pad}" y1="{y:.2f}" x2="{width-pad}" y2="{y:.2f}" stroke="#e2e8f0" stroke-width="1" />')

    last_x = xs[-1] if len(xs) else width - pad
    last_y = ys[-1] if len(ys) else height / 2
    last_dy = dys[-1] if len(dys) else height / 2

    return f"""
    <svg class='chart' viewBox='0 0 {width} {height}' preserveAspectRatio='none' aria-label='equity and drawdown chart'>
      {''.join(grid)}
      <path d='{d_path}' fill='none' stroke='#dc2626' stroke-width='2' opacity='0.65'></path>
      <path d='{e_path}' fill='none' stroke='#2563eb' stroke-width='3'></path>
      <circle cx='{last_x:.2f}' cy='{last_y:.2f}' r='4' fill='#2563eb'></circle>
      <circle cx='{last_x:.2f}' cy='{last_dy:.2f}' r='4' fill='#dc2626'></circle>
      <text x='{pad}' y='20' fill='#334155' font-size='12'>Equity {e_min:.3f} → {e_max:.3f}</text>
      <text x='{width-220}' y='20' fill='#991b1b' font-size='12'>Drawdown {d_min*100:.1f}% → {d_max*100:.1f}%</text>
    </svg>
    """


def _summary_sentence(total_return: float, max_drawdown: float, win_rate: float) -> str:
    if total_return > 0.10 and max_drawdown > -0.15:
        return "这次回测属于‘能赚钱且回撤还算可控’的一类，值得继续观察和做参数稳定性验证。"
    if total_return > 0 and max_drawdown <= -0.20:
        return "这次回测虽然赚了钱，但中间波动比较大，真正实盘时可能很难拿住。"
    if total_return <= 0:
        return "这次回测没有证明系统能稳定赚钱，当前更适合继续研究因子质量和交易成本，而不是直接实盘。"
    if win_rate < 0.45:
        return "系统可能依赖少数大赚时刻，赚钱方式偏‘低胜率换高赔率’，实盘前要特别重视风险承受能力。"
    return "这次回测有一定正向结果，但还需要继续看稳定性、成本和不同样本期表现。"


def build_report(out_path: str, ledger: list[dict], factor_tab: pd.DataFrame, pool_scores: pd.DataFrame, title="Factor Lab Pro Report"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df = pd.DataFrame(ledger)
    metrics = _build_equity_metrics(df)

    final_equity = metrics["final_equity"]
    total_return = metrics["total_return"]
    max_drawdown = metrics["max_drawdown"]
    win_rate = metrics["win_rate"]

    total_return_class = "good" if total_return > 0 else "bad"
    drawdown_class = "good" if max_drawdown > -0.15 else ("neutral" if max_drawdown > -0.25 else "bad")

    html_str = TPL.render(
        title=title,
        gen_time=datetime.now().isoformat(timespec="seconds"),
        steps=len(df),
        final_equity=f"{final_equity:.4f}",
        total_return=_pct(total_return),
        max_drawdown=_pct(max_drawdown),
        win_rate=f"{win_rate*100:.1f}%",
        total_return_class=total_return_class,
        drawdown_class=drawdown_class,
        summary_sentence=_summary_sentence(total_return, max_drawdown, win_rate),
        equity_chart=_svg_line_chart(metrics["equity_curve"], metrics["drawdown_curve"]),
        tail_table=_to_html_table(df.tail(50), n=50),
        factor_table=_to_html_table(factor_tab, n=30),
        pool_table=_to_html_table(pool_scores, n=30),
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_str)
    return out_path
