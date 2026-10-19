#!/usr/bin/env python3
"""Tarjeta para compartir (og.png, 1200x630): la imagen que aparece al pegar el link en WhatsApp, X o Facebook.
Se arma con los mismos datos de la página cada vez que se arma el sitio, así siempre muestra la última altura.
Uso: python3 fuente/og.py  (escribe fuente/data/og.png). Devuelve sin error si falta Pillow y no se puede instalar."""
import datetime, json, os, subprocess, sys

F = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(F, "data")
FONTS = os.path.join(F, "fonts")
OUT = os.path.join(DATA, "og.png")
W, H, S = 1200, 630, 2  # se dibuja al doble y se achica, para que las líneas queden suaves

BG, PANEL, FG, MUTED, LINE = "#f7f6f2", "#ffffff", "#1f1e1b", "#6b6860", "#e3e0d8"
BLUE, WARN, BAD = "#2f6fd6", "#c46a12", "#d81e1e"
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _pil():
    try:
        from PIL import Image  # noqa
    except ImportError:
        import importlib, site
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--user", "--break-system-packages", "pillow"], capture_output=True)
        site.addsitedir(site.getusersitepackages()); importlib.invalidate_caches()
    from PIL import Image, ImageDraw, ImageFont
    return Image, ImageDraw, ImageFont


def f2(x):
    return f"{x:.2f}".replace(".", ",")


def datos():
    L = lambda n: json.load(open(os.path.join(DATA, n + ".json"), encoding="utf-8"))
    p = L("parana_barranqueras"); st = (L("situacion") or [{}])[0]; U = L("umbrales")
    ult = p[-1]; h = float(ult["altura_m"])
    ant = next((r for r in reversed(p[:-1]) if r["fecha"] < ult["fecha"]), None)
    hit = sorted([u for u in U if h >= float(u["altura_m"])], key=lambda u: -float(u["altura_m"]))
    if h >= 9.5: nivel, col = "Tope del dique", BAD
    elif not hit: nivel, col = "Sin aviso", MUTED
    elif hit[0]["tipo"] == "evacuacion": nivel, col = "Evacuación", BAD
    elif hit[0]["tipo"] == "alerta": nivel, col = "Alerta", WARN
    else: nivel, col = "Aviso", MUTED
    d = datetime.date.fromisoformat(ult["fecha"])
    hm = str(ult.get("hora") or "")
    hs = ""
    if len(hm) == 5 and hm != "00:00":
        hs = f", {int(hm[:2])}{'' if hm[3:] == '00' else ':' + hm[3:]} h"
    comp = str(st.get("compuertas_rio_negro") or "")
    comp = "cerradas" if "cerrad" in comp.lower() else "abiertas" if "abiert" in comp.lower() else ""
    serie = [(datetime.date.fromisoformat(r["fecha"]), float(r["altura_m"])) for r in p if r["fecha"] > (d - datetime.timedelta(days=15)).isoformat()]
    U2 = {u["tipo"]: float(u["altura_m"]) for u in U if u["tipo"] in ("alerta", "evacuacion")}
    return dict(h=h, nivel=nivel, col=col, cuando=f"{DIAS[d.weekday()]} {d.day} {MESES[d.month - 1]}{hs}",
                cambio=round((h - float(ant["altura_m"])) * 100) if ant else None, comp=comp, serie=serie,
                alerta=U2.get("alerta", 6.0), evac=U2.get("evacuacion", 6.5))


def generar(out=OUT):
    Image, ImageDraw, ImageFont = _pil()
    D = datos()
    fnt = lambda n, s: ImageFont.truetype(os.path.join(FONTS, n), s * S)
    serif, sans, bold = "LiberationSerif-Regular.ttf", "LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf"
    im = Image.new("RGB", (W * S, H * S), PANEL); g = ImageDraw.Draw(im)
    z = lambda *v: [x * S for x in v]
    # izquierda: el dato
    g.rectangle(z(0, 0, 520, H), fill=BG)
    g.text(z(56, 56), "Paraná en Barranqueras", font=fnt(sans, 28), fill=MUTED)
    g.text(z(56, 92), D["cuando"], font=fnt(sans, 28), fill=MUTED)
    g.text(z(50, 140), f2(D["h"]), font=fnt(serif, 150), fill=FG)
    g.text(z(58, 300), "metros", font=fnt(sans, 34), fill=MUTED)
    if D["cambio"] is not None:
        c = D["cambio"]; t = "Sin cambios desde ayer" if c == 0 else f"{'▲' if c > 0 else '▼'} {abs(c)} cm desde ayer"
        g.text(z(200, 306), t, font=fnt(sans, 26), fill=MUTED)
    # nivel, en una pastilla
    pf = fnt(bold, 28); tw = g.textlength(D["nivel"], font=pf) / S
    tint = {BAD: "#fbe3e1", WARN: "#fbeedd"}.get(D["col"], "#ecebe6")
    g.rounded_rectangle(z(56, 370, 56 + tw + 40, 420), radius=25 * S, fill=tint)
    g.text(z(76, 378), D["nivel"], font=pf, fill=D["col"])
    if D["comp"]:
        g.text(z(56, 446), "Compuertas: ", font=fnt(sans, 26), fill=FG)
        x = 56 + g.textlength("Compuertas: ", font=fnt(sans, 26)) / S
        g.text(z(x, 446), D["comp"], font=fnt(bold, 26), fill=WARN if D["comp"] == "cerradas" else FG)
    g.text(z(56, 548), "apuratejose.com.ar", font=fnt(bold, 26), fill=FG)
    # derecha: últimos 15 días con alerta y evacuación
    g.text(z(568, 56), "Últimos 15 días", font=fnt(sans, 26), fill=MUTED)
    se = D["serie"]
    if len(se) >= 2:
        x0, x1, y0, y1 = 568, 1150, 120, 566
        lo = min(min(v for _, v in se), D["alerta"]) - 0.4; hi = max(max(v for _, v in se), D["evac"]) + 0.4
        t0, t1 = se[0][0], se[-1][0]; span = max(1, (t1 - t0).days)
        X = lambda t: x0 + (x1 - x0 - 12) * (t - t0).days / span
        Y = lambda v: y1 - (y1 - y0) * (v - lo) / (hi - lo)
        pts = [(X(t), Y(v)) for t, v in se]
        # área
        area = Image.new("RGBA", im.size, (0, 0, 0, 0)); ga = ImageDraw.Draw(area)
        ga.polygon([(x * S, y * S) for x, y in pts] + [(pts[-1][0] * S, y1 * S), (pts[0][0] * S, y1 * S)], fill=(47, 111, 214, 46))
        im.paste(area, (0, 0), area); g = ImageDraw.Draw(im)
        ye, ya = Y(D["evac"]), Y(D["alerta"])
        g.line(z(x0, ye, x1 + 18, ye), fill=BAD, width=3 * S)
        g.text(z(x0 + 4, ye - 34), f"Evacuación {f2(D['evac']).rstrip('0').rstrip(',')} m", font=fnt(sans, 22), fill=BAD)
        for xx in range(x0, x1 + 18, 18):
            g.line(z(xx, ya, min(xx + 10, x1 + 18), ya), fill=WARN, width=3 * S)
        g.text(z(x0 + 4, ya + 8), f"Alerta {f2(D['alerta']).rstrip('0').rstrip(',')} m", font=fnt(sans, 22), fill=WARN)
        g.line([(x * S, y * S) for x, y in pts], fill=BLUE, width=5 * S, joint="curve")
        cx, cy = pts[-1]
        g.ellipse(z(cx - 12, cy - 12, cx + 12, cy + 12), fill=PANEL); g.ellipse(z(cx - 9, cy - 9, cx + 9, cy + 9), fill=BLUE)
    im.resize((W, H), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE, colors=96).save(out, "PNG", optimize=True)  # liviana: se guarda cada hora
    return out


if __name__ == "__main__":
    try:
        print("tarjeta:", generar())
    except Exception as e:  # la tarjeta nunca frena la publicación
        print("tarjeta: no se pudo armar", e)
