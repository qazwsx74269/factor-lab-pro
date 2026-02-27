from __future__ import annotations
import os, json, html
import numpy as np
import pandas as pd
from datetime import datetime
from jinja2 import Template

TPL = Template("""<!doctype html>
<html><head><meta charset="utf-8"/>
<title>{{ title }}</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial;margin:24px;}
.card{border:1px solid #ddd;border-radius:10px;padding:14px;margin-bottom:16px;}
small{color:#666}
table{border-collapse:collapse;width:100%;}
th,td{border:1px solid #ddd;padding:6px 8px;font-size:12px;}
th{background:#f7f7f7;}
</style></head><body>
<h1>{{ title }}</h1>
<small>Generated at {{ gen_time }}</small>

<div class="card">
<h2>Summary</h2>
<ul>
<li>steps: {{ steps }}</li>
<li>final equity: {{ final_equity }}</li>
<li>total return: {{ total_return }}</li>
</ul>
</div>

<div class="card">
<h2>Equity (tail)</h2>
{{ tail_table | safe }}
</div>

<div class="card">
<h2>Top factors (by |ICIR|)</h2>
{{ factor_table | safe }}
</div>

<div class="card">
<h2>Strategy Pool Scores</h2>
{{ pool_table | safe }}
</div>

</body></html>""")

def _to_html_table(df: pd.DataFrame, n=20):
    if df is None or df.empty:
        return "<div>(empty)</div>"
    return df.head(n).to_html(index=False, escape=True, float_format=lambda x: f"{x:.6g}")

def build_report(out_path: str, ledger: list[dict], factor_tab: pd.DataFrame, pool_scores: pd.DataFrame, title="Factor Lab Pro Report"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df = pd.DataFrame(ledger)
    steps = len(df)
    final_equity = float(df["equity"].dropna().iloc[-1]) if steps and "equity" in df.columns else 1.0
    total_return = final_equity - 1.0

    html_str = TPL.render(
        title=title,
        gen_time=datetime.now().isoformat(timespec="seconds"),
        steps=steps,
        final_equity=f"{final_equity:.4f}",
        total_return=f"{total_return*100:.2f}%",
        tail_table=_to_html_table(df.tail(50), n=50),
        factor_table=_to_html_table(factor_tab, n=30),
        pool_table=_to_html_table(pool_scores, n=30),
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_str)
    return out_path
