#!/usr/bin/env python3
"""Arma index.html (la página de apuratejose.com.ar) con fuente/page.html y los JSON de fuente/data.
Uso, desde la raíz del repo: python3 fuente/armar_sitio.py"""
import os, re, subprocess, sys, tempfile
F = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(F)
# tarjeta para compartir (fuente/data/og.png) con la última altura; si falla, el sitio se arma igual
subprocess.run([sys.executable, os.path.join(F, "og.py")])
og = ""
if os.path.exists(os.path.join(F, "data", "og.png")):
    import json
    try:
        u = json.load(open(os.path.join(F, "data", "parana_barranqueras.json"), encoding="utf-8"))[-1]
        v = re.sub(r"\D", "", u["fecha"] + str(u.get("hora") or ""))
    except Exception:
        v = "1"
    og = f'''<meta property="og:image" content="https://apuratejose.com.ar/fuente/data/og.png?v={v}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Altura del Paraná en Barranqueras y estado de las compuertas del Río Negro">
<meta name="twitter:card" content="summary_large_image">
'''
tmp = os.path.join(tempfile.mkdtemp(), "public.html")
subprocess.run([sys.executable, "-I", os.path.join(F, "build_public.py"), os.path.join(F, "page.html"),
                os.path.join(F, "data"), tmp, "https://apuratejose.com.ar"], check=True)
s = open(tmp, encoding="utf-8").read()
tag = '<script src="d3.min.js"></script>'
i = s.index(tag) + len(tag)
meta = '''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#f7f6f2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#191917" media="(prefers-color-scheme: dark)">
<meta name="description" content="Altura del Paraná en Barranqueras, compuertas del Río Negro y pronóstico de lluvia para Resistencia, con datos oficiales.">
<meta property="og:title" content="Crecida del Paraná y cómo afecta al Río Negro">
<meta property="og:description" content="Altura del Paraná, compuertas del Río Negro y pronóstico de lluvia, con datos oficiales. La altura se actualiza cada hora.">
<meta property="og:url" content="https://apuratejose.com.ar">
<meta property="og:type" content="website">
''' + og
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(meta + s[:i] + "\n</head>\n<body>\n" + s[i:] + "\n</body>\n</html>\n")
print("index.html listo")
