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
  --slate:#334155;
}
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial;margin:0;background:var(--bg);color:var(--text);line-height:1.6;}
.wrapper{max-width:1200px;margin:0 auto;padding:24px;}
.hero{background:linear-gradient(135deg,#0f172a,#1d4ed8);color:#fff;border-radius:18px;padding:24px 28px;margin-bottom:18px;box-shadow:0 10px 30px rgba(15,23,42,.18);}
.hero h1{margin:0 0 8px 0;font-size:30px;}
.hero p{margin:8px 0;color:rgba(255,255,255,.9)}
.hero .muted{color:rgba(255,255,255,.72);font-size:14px}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px;margin-bottom:16px;}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:18px;box-shadow:0 4px 14px rgba(15,23,42,.05);}
.span-12{grid-column:span 12}
.span-8{grid-column:span 8}
.span-6{grid-column:span 6}
.span-5{grid-column:span 5}
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
.warntext{color:var(--amber)}
.badge{display:inline-flex;align-items:center;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid var(--border);background:#f8fafc;color:var(--slate)}
.badge.good{background:#f0fdf4;border-color:#86efac;color:#166534}
.badge.bad{background:#fef2f2;border-color:#fca5a5;color:#991b1b}
.badge.warntext{background:#fff7ed;border-color:#fdba74;color:#9a3412}
.note{padding:12px 14px;border-radius:12px;background:#eff6ff;border:1px solid #bfdbfe;color:#1e3a8a;font-size:14px}
.warn{background:#fff7ed;border-color:#fdba74;color:#9a3412}
.goodbox{background:#f0fdf4;border-color:#86efac;color:#166534}
.dangerbox{background:#fef2f2;border-color:#fca5a5;color:#991b1b}
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
.callout{padding:14px;border-radius:14px;border:1px solid var(--border);background:#fff}
.callout h3{margin-bottom:6px}
.footer{margin-top:18px;color:var(--muted);font-size:12px}
.two-col{columns:2;column-gap:24px}
@media (max-width: 900px){
  .span-8,.span-6,.span-5,.span-4,.span-3{grid-column:span 12}
  .hero h1{font-size:24px}
  .two-col{columns:1}
}
</style></head><body>
<div class="wrapper">
  <div class="hero">
    <h1>{{ title }}</h1>
    <p>{{ summary_sentence }}</p>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;">
      <span class="badge {{ verdict_badge_class }}">{{ verdict_label }}</span>
      <span class="badge {{ risk_badge_class }}">风险等级：{{ risk_label }}</span>
      <span class="badge">建议：{{ action_label }}</span>
    </div>
    <div class="muted" style="margin-top:10px;">Generated at {{ gen_time }} · 面向小白和研究者的解释型报告</div>
  </div>

  <div class="grid">
    <div class="card span-3"><div class="metric"><div class="label">最终净值</div><div class="value {{ total_return_class }}">{{ final_equity }}</div><div class="muted">初始资金 = 1.0</div></div></div>
    <div class="card span-3"><div class="metric"><div class="label">总收益</div><div class="value {{ total_return_class }}">{{ total_return }}</div><div class="muted">这次回测最终赚/亏了多少</div></div></div>
    <div class="card span-3"><div class="metric"><div class="label">最大回撤</div><div class="value {{ drawdown_class }}">{{ max_drawdown }}</div><div class="muted">中途最难受的亏损幅度</div></div></div>
    <div class="card span-3"><div class="metric"><div class="label">胜率 / 有效交易步</div><div class="value neutral">{{ win_rate }}</div><div class="muted">{{ active_steps }} / {{ steps }}</div></div></div>
  </div>

  <div class="grid">
    <div class="card span-8">
      <h2>1. 先看这张图：钱是怎么变的？</h2>
      <div class="legend"><span class="blue">资金曲线</span><span class="red">回撤</span></div>
      {{ equity_chart | safe }}
      <ul class="explain-list">
        <li><b>蓝线向右上</b>：整体在赚钱。</li>
        <li><b>红线越往下</b>：中间越痛苦，说明你实盘更可能中途扛不住。</li>
        <li><b>如果蓝线不强、红线很深</b>：这不是一个适合小白直接拿真钱测试的系统。</li>
      </ul>
    </div>
    <div class="card span-4">
      <h2>2. 一句话结论</h2>
      <div class="callout {{ verdict_box_class }}">
        <h3>{{ verdict_label }}</h3>
        <p>{{ verdict_reason }}</p>
      </div>
      <div style="height:10px"></div>
      <div class="callout">
        <h3>小白怎么利用这份报告赚钱？</h3>
        <ol class="explain-list">
          <li>先筛掉 <b>总收益 ≤ 0</b> 的方案。</li>
          <li>再筛掉 <b>回撤过深</b>、你拿不住的方案。</li>
          <li>优先保留 <b>ICIR 更稳</b> 的因子。</li>
          <li>最后只拿 <b>小资金</b> 做真实验证，不要一上来重仓。</li>
        </ol>
      </div>
    </div>
  </div>

  <div class="grid">
    <div class="card span-4">
      <h2>3. 回测过程发生了什么</h2>
      <ul class="explain-list">
        <li><b>Warmup</b>：前期攒样本，先不交易。</li>
        <li><b>Hold</b>：这一步沿用之前仓位，不重新调仓。</li>
        <li><b>Ok</b>：真实产生一次回测收益。</li>
        <li><b>No future</b>：数据尾部不够了，无法再看未来收益。</li>
      </ul>
      <div class="note">这能帮助你理解：回测不是每一步都在疯狂交易，而是在固定节奏里决定“什么时候该动、什么时候该等”。</div>
    </div>
    <div class="card span-4">
      <h2>4. 回测数据怎么读</h2>
      <ul class="explain-list">
        <li><b>ret_hold</b>：理论收益，不算手续费和滑点。</li>
        <li><b>ret</b>：真实收益，已经扣除交易成本。</li>
        <li><b>equity</b>：累计净值。</li>
        <li><b>top_factor</b>：当前最重要的主导因子。</li>
        <li><b>top_factor_w</b>：这个因子当下权重有多高。</li>
      </ul>
      <div class="note warn">重点不是“理论上赚多少”，而是 <b>扣掉成本后还剩多少</b>。</div>
    </div>
    <div class="card span-4">
      <h2>5. 小白最该看的 4 件事</h2>
      <ul class="explain-list">
        <li><b>总收益</b>：有没有正收益。</li>
        <li><b>最大回撤</b>：你扛不扛得住。</li>
        <li><b>胜率</b>：赚钱是靠稳定小胜，还是少数暴击。</li>
        <li><b>主导因子是否稳定</b>：是不是今天一个说法，明天一个说法。</li>
      </ul>
      <div class="note goodbox">能长期赚钱的系统，往往不是“最刺激”的，而是“最稳定”的。</div>
    </div>
  </div>

  <div class="grid">
    <div class="card span-6">
      <h2>6. 因子报告怎么用</h2>
      <ul class="explain-list">
        <li><b>IC</b>：因子和未来收益是否同方向。</li>
        <li><b>ICIR</b>：因子是不是长期稳定有效。</li>
        <li><b>优先用 ICIR 高的</b>：因为它更不容易只是运气。</li>
        <li><b>多个因子组合</b>：通常比押注单一因子更稳。</li>
      </ul>
      <div class="note">如果你想利用这个系统赚钱，最合理的动作不是“盲信一个神指标”，而是找到 <b>稳定有效的一组因子</b> 做组合。</div>
    </div>
    <div class="card span-6">
      <h2>7. 实盘使用建议</h2>
      <div class="two-col">
        <div>
          <h3>适合做的</h3>
          <ul class="explain-list">
            <li>先用小资金验证。</li>
            <li>优先看回撤和稳定性。</li>
            <li>保留表现持续好的因子。</li>
            <li>每隔一段时间重新评估。</li>
          </ul>
        </div>
        <div>
          <h3>不要做的</h3>
          <ul class="explain-list">
            <li>看到一次回测赚钱就重仓。</li>
            <li>忽略交易成本。</li>
            <li>把偶然暴利当稳定系统。</li>
            <li>看不懂回撤还硬上。</li>
          </ul>
        </div>
      </div>
    </div>
  </div>

  <div class="grid">
    <div class="card span-12">
      <h2>8. 机器给你的结论卡</h2>
      <div class="grid" style="margin-bottom:0;">
        <div class="span-4">
          <div class="callout {{ verdict_box_class }}"><h3>是否值得继续</h3><p>{{ verdict_reason }}</p></div>
        </div>
        <div class="span-4">
          <div class="callout"><h3>风险等级</h3><p>{{ risk_reason }}</p></div>
        </div>
        <div class="span-4">
          <div class="callout"><h3>建议动作</h3><p>{{ action_reason }}</p></div>
        </div>
      </div>
    </div>
  </div>

  <div class="grid">
    <div class="card span-12">
      <h2>9. Top Factors（重点看稳定性）</h2>
      {{ factor_table | safe }}
    </div>
  </div>

  <div class="grid">
    <div class="card span-12">
      <h2>10. 回测摘要表（给小白看的翻译版）</h2>
      {{ summary_table | safe }}
    </div>
  </div>

  <div class="grid">
    <div class="card span-12">
      <h2>11. 最近回测明细</h2>
      {{ tail_table | safe }}
    </div>
  </div>

  <div class="grid">
    <div class="card span-12">
      <h2>12. Strategy Pool Scores</h2>
      {{ pool_table | safe }}
    </div>
  </div>

  <div class="footer">
    <div>核心原则：<b>先证明它稳定赚钱，再考虑放大仓位</b>。回测是过滤器，不是提款机。</div>
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
            "active_steps": 0,
            "status_counts": {},
            "top_factor": None,
            "top_factor_share": 0.0,
        }

    equity = df["equity"].astype(float).replace([np.inf, -np.inf], np.nan).ffill().dropna()
    if equity.empty:
        equity = pd.Series([1.0])
    peak = equity.cummax()
    drawdown = equity / peak - 1.0

    ret = df.get("ret", pd.Series(dtype=float))
    ret = ret.astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    win_rate = float((ret > 0).mean()) if len(ret) else 0.0
    active_steps = int(len(ret))

    status_counts = {}
    if "status" in df.columns:
        status_counts = df["status"].fillna("unknown").value_counts().to_dict()

    top_factor = None
    top_factor_share = 0.0
    if "top_factor" in df.columns:
        s = df["top_factor"].dropna().astype(str)
        if not s.empty:
            vc = s.value_counts()
            top_factor = str(vc.index[0])
            top_factor_share = float(vc.iloc[0] / len(s))

    return {
        "final_equity": _safe_float(equity.iloc[-1], 1.0),
        "total_return": _safe_float(equity.iloc[-1] - 1.0, 0.0),
        "max_drawdown": _safe_float(drawdown.min(), 0.0),
        "win_rate": win_rate,
        "equity_curve": equity.reset_index(drop=True),
        "drawdown_curve": drawdown.reset_index(drop=True),
        "active_steps": active_steps,
        "status_counts": status_counts,
        "top_factor": top_factor,
        "top_factor_share": top_factor_share,
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


def _decision(total_return: float, max_drawdown: float, win_rate: float):
    if total_return <= 0:
        return {
            "verdict_label": "暂不适合实盘",
            "verdict_badge_class": "bad",
            "verdict_box_class": "dangerbox",
            "verdict_reason": "因为这次回测最终没有证明系统能赚钱，所以更适合继续优化因子和组合，而不是直接上真钱。",
            "action_label": "继续研究，不下场",
            "action_reason": "先优化因子稳定性、减少成本、扩大样本，再做下一轮验证。",
        }
    if total_return > 0 and max_drawdown <= -0.25:
        return {
            "verdict_label": "能赚钱，但风险偏大",
            "verdict_badge_class": "warntext",
            "verdict_box_class": "warn",
            "verdict_reason": "虽然回测结果是正收益，但中间回撤较深，小白大概率扛不住，直接实盘容易中途放弃。",
            "action_label": "只能小资金观察",
            "action_reason": "如果一定要试，只能轻仓、小资金、短周期跟踪，绝对不建议重仓。",
        }
    if total_return > 0.10 and max_drawdown > -0.15 and win_rate >= 0.45:
        return {
            "verdict_label": "可以小资金验证",
            "verdict_badge_class": "good",
            "verdict_box_class": "goodbox",
            "verdict_reason": "这次结果显示收益、回撤、稳定性都相对平衡，已经到了可以做小资金实盘验证的阶段。",
            "action_label": "小资金试运行",
            "action_reason": "拿可承受亏损的小资金做真实验证，继续盯滑点、手续费和行为稳定性。",
        }
    return {
        "verdict_label": "适合继续观察",
        "verdict_badge_class": "neutral",
        "verdict_box_class": "note",
        "verdict_reason": "当前结果有一定正向价值，但还没强到足以让人放心上真钱，更适合继续观察和滚动验证。",
        "action_label": "继续观察",
        "action_reason": "保留这套组合，持续跑更多样本期，再决定是否做小资金测试。",
    }


def _risk_label(max_drawdown: float):
    if max_drawdown <= -0.30:
        return "高", "bad", "回撤已经深到多数普通人会中途扛不住，心理和资金压力都很大。"
    if max_drawdown <= -0.15:
        return "中", "warntext", "这类系统可能能赚钱，但过程不会很舒服，需要较强纪律性。"
    return "低", "good", "回撤相对可控，更适合逐步验证和长期跟踪。"


def _summary_table(metrics: dict, steps: int):
    rows = [
        {"问题": "这次最终赚了吗？", "结论": _pct(metrics["total_return"]), "怎么理解": "正数代表赚钱，负数代表亏钱。"},
        {"问题": "过程痛苦吗？", "结论": _pct(metrics["max_drawdown"]), "怎么理解": "越负说明中途越难受，越容易拿不住。"},
        {"问题": "赚钱稳定吗？", "结论": f"{metrics['win_rate']*100:.1f}% 胜率", "怎么理解": "胜率高不代表一定更赚钱，但能帮助理解收益风格。"},
        {"问题": "真正发生了多少次有效交易？", "结论": str(metrics["active_steps"]), "怎么理解": f"总步数 {steps} 中，真正产生收益记录的次数。"},
        {"问题": "最常主导的因子是谁？", "结论": str(metrics.get("top_factor") or "N/A"), "怎么理解": "它是这个样本期里最常站在 C 位的因子。"},
        {"问题": "主导因子稳定吗？", "结论": _pct(metrics.get("top_factor_share", 0.0)), "怎么理解": "占比越高，说明这个主导因子越稳定地反复出现。"},
    ]
    return pd.DataFrame(rows)


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
    risk_label, risk_badge_class, risk_reason = _risk_label(max_drawdown)
    decision = _decision(total_return, max_drawdown, win_rate)

    html_str = TPL.render(
        title=title,
        gen_time=datetime.now().isoformat(timespec="seconds"),
        steps=len(df),
        active_steps=metrics["active_steps"],
        final_equity=f"{final_equity:.4f}",
        total_return=_pct(total_return),
        max_drawdown=_pct(max_drawdown),
        win_rate=f"{win_rate*100:.1f}%",
        total_return_class=total_return_class,
        drawdown_class=drawdown_class,
        summary_sentence=_summary_sentence(total_return, max_drawdown, win_rate),
        equity_chart=_svg_line_chart(metrics["equity_curve"], metrics["drawdown_curve"]),
        factor_table=_to_html_table(factor_tab, n=30),
        pool_table=_to_html_table(pool_scores, n=30),
        tail_table=_to_html_table(df.tail(50), n=50),
        summary_table=_to_html_table(_summary_table(metrics, len(df)), n=20),
        risk_label=risk_label,
        risk_badge_class=risk_badge_class,
        risk_reason=risk_reason,
        **decision,
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_str)
    return out_path
