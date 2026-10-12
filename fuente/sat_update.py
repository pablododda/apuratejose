#!/usr/bin/env python3
"""Actualiza la imagen satelital "reciente" del norte de Resistencia (NASA GIBS, capas HLS de 30 m).

Uso: python3 -I sat_update.py SATELITE_JSON PARANA_JSON OUT_JSON [DIAS_ATRAS]
  SATELITE_JSON: el satelite.json vigente (se conserva la fila tipo "antes")
  PARANA_JSON:   parana_barranqueras.json (para la altura del río el día de la imagen)
Busca, desde hoy hacia atrás, la pasada más reciente sin nubes que cubra la zona; si es más nueva
que la vigente, la descarga y reemplaza la fila "reciente". Requiere Pillow y acceso a gibs.earthdata.nasa.gov.
"""
import base64, datetime, io, json, sys, urllib.request
from PIL import Image

BBOX = "-27.475,-59.035,-27.390,-58.925"  # minLat,minLon,maxLat,maxLon (WMS 1.3.0, EPSG:4326)
LAYERS = ["HLS_S30_Nadir_BRDF_Adjusted_Reflectance", "HLS_L30_Nadir_BRDF_Adjusted_Reflectance"]


def get(layer, date, w, h, fmt):
    u = ("https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0"
         f"&LAYERS={layer}&STYLES=&CRS=EPSG:4326&BBOX={BBOX}&WIDTH={w}&HEIGHT={h}&FORMAT={fmt}&TRANSPARENT=TRUE&TIME={date}")
    return urllib.request.urlopen(u, timeout=60).read()


def quality(layer, date):
    im = Image.open(io.BytesIO(get(layer, date, 120, 93, "image/png"))).convert("RGBA")
    px = list(im.getdata())
    valid = [p for p in px if p[3] > 0 and sum(p[:3]) > 15]
    cov = len(valid) / len(px)
    cloud = sum(1 for p in valid if min(p[:3]) > 170) / max(1, len(valid))
    return cov, cloud


def main():
    sat_path, par_path, out_path = sys.argv[1:4]
    dias = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    sat = json.load(open(sat_path, encoding="utf-8"))
    par = {r["fecha"]: r["altura_m"] for r in json.load(open(par_path, encoding="utf-8"))}
    cur = next((r for r in sat if r.get("tipo") == "reciente"), None)
    cur_date = cur["fecha"] if cur else "0000-00-00"
    d = datetime.date.today()
    for _ in range(dias):
        ds = d.isoformat()
        if ds <= cur_date:
            break
        for L in LAYERS:
            try:
                cov, cloud = quality(L, ds)
            except Exception:
                continue
            if cov >= 0.97 and cloud <= 0.03:
                jpg = get(L, ds, 900, 696, "image/jpeg")
                row = {"tipo": "reciente", "fecha": ds, "altura_m": par.get(ds),
                       "img": "data:image/jpeg;base64," + base64.b64encode(jpg).decode()}
                sat = [r for r in sat if r.get("tipo") != "reciente"] + [row]
                json.dump(sat, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
                print("nueva imagen", ds, L)
                return
        d -= datetime.timedelta(days=1)
    json.dump(sat, open(out_path, "w", encoding="utf-8"), ensure_ascii=False)
    print("sin imagen nueva; se mantiene", cur_date)


if __name__ == "__main__":
    main()
