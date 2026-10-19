#!/usr/bin/env python3
"""Imagen satelital "reciente" del dique, directo de Sentinel-2 (Earth Search, AWS, datos abiertos).

Busca pasadas de Sentinel-2 más nuevas que la imagen vigente, mira cuántas nubes hay SOLO en el recuadro
del dique (banda SCL de clasificación de escena) y, si hay pocas, guarda la imagen en color real.
Lo llama el robot de cada hora (agp_update.py). Devuelve un texto si cambió la imagen, o None.
"""
import base64, datetime, io, json, os, subprocess, sys, urllib.request

BBOX = (-59.015, -27.4915, -58.865, -27.3885)  # lon/lat: centrado en el dique regulador del Río Negro
MAX_NUBES = 0.45      # hasta 45% del recuadro con nubes o sombra de nubes
MAX_SIN_DATO = 0.03   # el recuadro tiene que estar cubierto por la pasada
STAC = "https://earth-search.aws.element84.com/v1/search"
VISTOS = "/tmp/sat_s2_descartadas.txt"  # pasadas ya revisadas y descartadas en esta corrida del robot


def _rasterio():
    try:
        import rasterio  # noqa
    except ImportError:
        import importlib, site
        r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--user", "--break-system-packages", "rasterio", "pillow", "numpy"], capture_output=True, text=True)
        print("pip:", r.returncode, r.stderr[-300:])
        site.addsitedir(site.getusersitepackages())
        importlib.invalidate_caches()
    import rasterio
    return rasterio


def buscar(desde):
    q = {"collections": ["sentinel-2-l2a"], "bbox": list(BBOX), "limit": 20,
         "datetime": f"{desde}T00:00:00Z/{datetime.datetime.utcnow():%Y-%m-%dT%H:%M:%SZ}",
         "sortby": [{"field": "properties.datetime", "direction": "desc"}]}
    r = urllib.request.Request(STAC, data=json.dumps(q).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=60) as x:
        feats = json.loads(x.read()).get("features", [])
    # solo las que cubren todo el recuadro
    return [f for f in feats if f["bbox"][0] <= BBOX[0] and f["bbox"][1] <= BBOX[1] and f["bbox"][2] >= BBOX[2] and f["bbox"][3] >= BBOX[3]]


def leer(rasterio, href, w, h):
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds
    from rasterio.enums import Resampling
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", AWS_NO_SIGN_REQUEST="YES"):
        with rasterio.open(href) as src:
            b = transform_bounds("EPSG:4326", src.crs, *BBOX)
            win = from_bounds(*b, transform=src.transform)
            return src.read(window=win, out_shape=(src.count, h, w), resampling=Resampling.nearest if src.count == 1 else Resampling.bilinear, boundless=True, fill_value=0)


def actualizar(sat_path, par_path):
    sat = json.load(open(sat_path, encoding="utf-8"))
    cur = next((r for r in sat if r.get("tipo") == "reciente"), None)
    cur_date = cur["fecha"] if cur else "2000-01-01"
    desde = (datetime.date.fromisoformat(cur_date) + datetime.timedelta(days=1)).isoformat()
    vistos = set(open(VISTOS).read().split()) if os.path.exists(VISTOS) else set()
    feats = [f for f in buscar(desde) if f["id"] not in vistos]
    if not feats:
        return None
    rasterio = _rasterio()
    import numpy as np
    from PIL import Image
    for f in feats:
        fecha = f["properties"]["datetime"][:10]
        try:
            scl = leer(rasterio, f["assets"]["scl"]["href"], 150, 116)[0]
            n = scl.size
            sin = np.isin(scl, [0, 1]).sum() / n            # sin dato / píxel saturado
            nub = np.isin(scl, [3, 8, 9, 10]).sum() / n     # sombra de nube, nubes medias/altas, cirros
            print(f"satélite {f['id']}: nubes {nub:.0%}, sin dato {sin:.0%}")
            if sin > MAX_SIN_DATO or nub > MAX_NUBES:
                open(VISTOS, "a").write(f["id"] + "\n")
                continue
            rgb = leer(rasterio, f["assets"]["visual"]["href"], 900, 696)
            img = Image.fromarray(np.moveaxis(rgb[:3], 0, -1).astype("uint8"))
            buf = io.BytesIO(); img.save(buf, "JPEG", quality=82)
            par = {r["fecha"]: r["altura_m"] for r in json.load(open(par_path, encoding="utf-8"))}
            row = {"tipo": "reciente", "fecha": fecha, "altura_m": par.get(fecha), "nubes_pct": round(nub * 100),
                   "satelite": "Sentinel-2", "img": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()}
            # la que era "reciente" pasa a ser la de "antes": así se comparan dos pasadas seguidas, no una vieja
            prev = next((r for r in sat if r.get("tipo") == "reciente"), None)
            if prev:
                sat = [dict(prev, tipo="antes")] + [row]
            else:
                sat = [r for r in sat if r.get("tipo") != "reciente"] + [row]
            json.dump(sat, open(sat_path, "w", encoding="utf-8"), ensure_ascii=False)
            return f"imagen satelital del {fecha} ({round(nub * 100)}% de nubes)"
        except Exception as e:
            print("satélite: error con", f["id"], e)
    return None


if __name__ == "__main__":
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    print(actualizar(os.path.join(d, "satelite.json"), os.path.join(d, "parana_barranqueras.json")))
