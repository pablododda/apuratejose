#!/usr/bin/env python3
"""Arma index.html (la página de apuratejose.com.ar) con fuente/page.html y los JSON de fuente/data.
Uso, desde la raíz del repo: python3 fuente/armar_sitio.py"""
import os, re, subprocess, sys, tempfile
F = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(F)
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
<meta name="description" content="Altura del Paraná en Barranqueras, compuertas del Río Negro y pronóstico de lluvia para Resistencia, con datos oficiales.">
<meta property="og:title" content="Crecida del Paraná · Resistencia">
<meta property="og:description" content="Altura del Paraná, compuertas del Río Negro y pronóstico de lluvia, con datos oficiales. Se actualiza cuatro veces por día.">
<meta property="og:url" content="https://apuratejose.com.ar">
<meta property="og:type" content="website">
'''
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(meta + s[:i] + "\n</head>\n<body>\n" + s[i:] + "\n</body>\n</html>\n")
print("index.html listo")
