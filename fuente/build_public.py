#!/usr/bin/env python3
"""Arma la versión pública (sin login) del tablero "Crecida del Paraná · Resistencia".

Uso: python3 -I build_public.py PAGE_HTML DATA_DIR OUT_HTML SHARE_URL
  PAGE_HTML: el texto de files/index.html del Dashboard
  DATA_DIR:  carpeta con parana_barranqueras.json, umbrales.json, pronostico.json, situacion.json, lluvia.json, historicos.json, satelite.json
  SHARE_URL: link que usa el botón Compartir
La página resultante se publica con el Artifact tool (sin doctype/head/body), junto a d3.min.js.
"""
import json, sys, os, re

page_path, data_dir, out_path, share_url = sys.argv[1:5]
page = open(page_path, encoding="utf-8").read()
ids = ["parana_barranqueras", "umbrales", "pronostico", "situacion", "lluvia", "historicos", "satelite"]
data = {i: json.load(open(os.path.join(data_dir, i + ".json"), encoding="utf-8")) for i in ids}

# Botón compartir: link público
page = re.sub(r"const URL_TABLERO = '[^']*';", "const URL_TABLERO = " + json.dumps(share_url) + ";", page)

TOKENS = """
<title>Crecida del Paraná · Resistencia</title>
<style>
:root {
  --font-anthropic-sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-anthropic-serif: Georgia, "Times New Roman", serif;
  --cds-font-size-caption: 12px; --cds-font-size-body: 14px; --cds-font-size-heading: 16px; --cds-font-size-title: 30px;
  --cds-font-weight-medium: 600;
  --cds-gap-xs: 4px; --cds-gap-sm: 8px; --cds-gap-md: 14px; --cds-gap-lg: 22px;
  --cds-pad-xs: 4px; --cds-pad-sm: 8px; --cds-pad-md: 12px; --cds-pad-lg: 18px;
  --cds-radius: 10px; --cds-dur-slow: .3s;
  --color-bg: #f7f6f2; --color-panel: #ffffff; --color-fg: #1f1e1b; --color-fg-muted: #6b6860;
  --color-border-line: #e3e0d8; --color-ok: #2e7d4f; --color-warn: #c46a12; --color-bad: #c0392b;
  --cds-chart-grid: #ece9e1; --cds-chart-axis: #c9c5bb; --cds-chart-reference: #a8a49a;
  --cds-surface-popover: #ffffff; --cds-border: #e3e0d8; --cds-text-secondary: #6b6860;
  --cds-shadow-popover: 0 6px 20px rgba(0,0,0,.12);
  --rp-c1: #2f6fd0; --rp-c2: #3a9bbf;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --color-bg: #191917; --color-panel: #23221f; --color-fg: #ecebe6; --color-fg-muted: #a3a097;
    --color-border-line: #3a3833; --color-ok: #5fbf85; --color-warn: #f0a04b; --color-bad: #ef6f61;
    --cds-chart-grid: #302f2b; --cds-chart-axis: #55524b; --cds-chart-reference: #77736a;
    --cds-surface-popover: #2b2a26; --cds-border: #3a3833; --cds-text-secondary: #a3a097;
    --cds-shadow-popover: 0 6px 20px rgba(0,0,0,.5);
    --rp-c1: #6ea3ff; --rp-c2: #5cc2e0;
  }
}
:root[data-theme="dark"] {
  --color-bg: #191917; --color-panel: #23221f; --color-fg: #ecebe6; --color-fg-muted: #a3a097;
  --color-border-line: #3a3833; --color-ok: #5fbf85; --color-warn: #f0a04b; --color-bad: #ef6f61;
  --cds-chart-grid: #302f2b; --cds-chart-axis: #55524b; --cds-chart-reference: #77736a;
  --cds-surface-popover: #2b2a26; --cds-border: #3a3833; --cds-text-secondary: #a3a097;
  --cds-shadow-popover: 0 6px 20px rgba(0,0,0,.5);
  --rp-c1: #6ea3ff; --rp-c2: #5cc2e0;
}
html, body { margin: 0; background: var(--color-bg); color: var(--color-fg); font-family: var(--font-anthropic-sans); -webkit-text-size-adjust: 100%; }
#dash-root { --dash-gutter: 16px; padding: 20px var(--dash-gutter) 32px; box-sizing: border-box; }
#dash-root *, #dash-root *::before, #dash-root *::after { box-sizing: border-box; }
@media (min-width: 700px) { #dash-root { padding-top: 28px; } }
</style>
<script src="d3.min.js"></script>
"""

SHIM = """
<script>
(() => {
  const RAW = %s;
  const calcs = {};
  const listeners = [];
  const data = (id) => {
    if (calcs[id]) {
      const c = calcs[id];
      try { return { status: 'ok', data: c.fn(...c.inputs.map((i) => data(i).data)), meta: [] }; }
      catch (e) { return { status: 'error', data: [], message: String(e) }; }
    }
    if (!(id in RAW)) return { status: 'missing', data: [] };
    const rows = RAW[id];
    return { status: 'ok', data: rows, columns: rows.length ? Object.keys(rows[0]) : [], meta: [], refreshing: false };
  };
  let t = null;
  window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(() => listeners.forEach((f) => f()), 120); });
  window.dash = {
    data,
    onData: (fn) => { listeners.push(fn); fn(); },
    calc: (id, o) => { calcs[id] = o; },
    loader: () => {},
    colors: ['var(--rp-c1)', 'var(--rp-c2)', 'var(--color-warn)', 'var(--color-ok)'],
    refresh: () => {}, params: () => ({}), setParams: () => {}, resetParams: () => {}, setLink: () => {},
  };
})();
</script>
"""

out = TOKENS + SHIM % json.dumps(data, ensure_ascii=False) + '<div id="dash-root">\n' + page + "\n</div>\n"
open(out_path, "w", encoding="utf-8").write(out)
print("ok", len(out))
