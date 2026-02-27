from __future__ import annotations
import os
from datetime import datetime
from jinja2 import Template

INDEX_TPL = Template("""<!doctype html><html><head><meta charset="utf-8"/>
<title>Factor Lab Pro Runs</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial;margin:24px;}
table{border-collapse:collapse;width:100%;}
th,td{border:1px solid #ddd;padding:6px 8px;font-size:12px;}
th{background:#f7f7f7;}
a{text-decoration:none;}
</style></head><body>
<h1>Factor Lab Pro — Runs</h1>
<p>Updated at {{ gen_time }}</p>
<table>
<tr><th>run</th><th>time</th><th>report</th></tr>
{% for r in runs %}
<tr>
<td>{{ r.name }}</td>
<td>{{ r.time }}</td>
<td><a href="{{ r.href }}">open</a></td>
</tr>
{% endfor %}
</table>
</body></html>""")

def build_runs_index(runs_dir: str):
    os.makedirs(runs_dir, exist_ok=True)
    items=[]
    for name in sorted(os.listdir(runs_dir), reverse=True):
        p=os.path.join(runs_dir,name)
        if not os.path.isdir(p):
            continue
        report=os.path.join(p,"report.html")
        if not os.path.exists(report):
            continue
        items.append({"name": name, "time": name, "href": f"{name}/report.html"})
    html = INDEX_TPL.render(gen_time=datetime.now().isoformat(timespec="seconds"), runs=items)
    out = os.path.join(runs_dir, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    return out
