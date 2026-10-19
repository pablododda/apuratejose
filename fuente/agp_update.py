#!/usr/bin/env python3
"""Actualización horaria de la altura del Paraná en Barranqueras (la corre GitHub Actions cada hora, sin Claude).

1. Lee la estación automática del puerto de Barranqueras (cada hora).
2. Si esa estación está colgada (último dato de hace más de MAX_HORAS), usa Prefectura vía INA (Hidráulica de Entre Ríos).
3. Si la lectura elegida es más nueva que la última fila de parana_barranqueras.json, actualiza la fila de ese día
   (o agrega una), la primera fila de pronostico.json y "actualizado" en situacion.json.
Imprime CAMBIO=1 si cambió algo, para que el workflow arme index.html y haga commit.
Uso, desde la raíz del repo: python3 fuente/agp_update.py
"""
import datetime, json, os, re, ssl, urllib.request

F = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(F, "data")
AR = datetime.timezone(datetime.timedelta(hours=-3))
MAX_HORAS = 3
AGP_URL = "https://hidrografia2.agpse.gob.ar/histdat/Barranqueras.dat"
INA_URL = "https://www.hidraulica.gob.ar/ina/ajax.estaciones.json.php"
UA = {"User-Agent": "Mozilla/5.0 (apuratejose.com.ar; actualizacion horaria)"}


def bajar(url):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.URLError as e:
        # el servidor del puerto no manda el certificado intermedio completo; son datos públicos de solo lectura,
        # así que reintentamos sin verificar la cadena (y abajo se descarta cualquier salto raro de altura)
        if "CERTIFICATE_VERIFY_FAILED" not in str(e) or "agpse.gob.ar" not in url:
            raise
        ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            return r.read().decode("utf-8", "replace")


def agp():
    """Última lectura válida: (datetime con zona AR, altura). Columnas: TIMESTAMP, RECORD, NIvel_Avg, Altura_Avg, Offset."""
    ult = None
    for linea in bajar(AGP_URL).splitlines()[4:]:
        c = [x.strip().strip('"') for x in linea.split(",")]
        if len(c) < 4 or not re.match(r"\d{4}-\d\d-\d\d \d\d:\d\d", c[0]):
            continue
        try:
            h = float(c[3])
        except ValueError:
            continue  # NAN
        if not 0 < h < 15:
            continue
        ult = (datetime.datetime.strptime(c[0][:16], "%Y-%m-%d %H:%M").replace(tzinfo=AR), round(h, 2))
    return ult


def ina():
    """(Barranqueras, Corrientes) desde el JSON del INA: cada uno (datetime AR, altura) o None."""
    out = {}
    for e in json.loads(bajar(INA_URL)):
        n = str(e.get("nombre", "")).lower()
        if n in ("barranqueras", "corrientes") and e.get("valor_actual") is not None:
            t = datetime.datetime.strptime(e["fecha_actual"], "%d/%m/%Y %H:%M").replace(tzinfo=AR)
            out[n] = (t, round(float(e["valor_actual"]), 2))
    return out.get("barranqueras"), out.get("corrientes")


def main():
    ahora = datetime.datetime.now(AR)
    lecturas, corr, respondio = [], None, False
    try:
        a = agp()
        respondio = respondio or a is not None
        if a and ahora - a[0] <= datetime.timedelta(hours=MAX_HORAS):
            lecturas.append((a[0], a[1], "estación del puerto de Barranqueras"))
        print("puerto:", a)
    except Exception as e:
        print("puerto: error", e)
    try:
        b, corr = ina()
        respondio = respondio or b is not None
        if b and not lecturas:  # el puerto está colgado: Prefectura vía INA
            lecturas.append((b[0], b[1], "Prefectura vía INA"))
        print("INA:", b, "Corrientes:", corr)
    except Exception as e:
        print("INA: error", e)
    if not respondio:
        print("CAMBIO=0 (ninguna fuente respondió)")
        return

    cambio, msg = False, "revisado sin dato nuevo"
    pp = os.path.join(DATA, "parana_barranqueras.json")
    p = json.load(open(pp, encoding="utf-8"))
    if lecturas:
        t, h, fuente = max(lecturas)
        fecha, hora = t.strftime("%Y-%m-%d"), t.strftime("%H:%M")
        ult = p[-1]
        ult_t = datetime.datetime.strptime(ult["fecha"] + " " + (ult.get("hora") or "00:00"), "%Y-%m-%d %H:%M").replace(tzinfo=AR)
        if t <= ult_t:
            print("la última fila ya es igual o más nueva:", ult)
        elif t - ult_t < datetime.timedelta(days=2) and abs(h - float(ult["altura_m"])) > 0.6:
            print("salto sospechoso de", ult["altura_m"], "a", h, "; no se carga")
        else:
            fila = {"fecha": fecha, "altura_m": h, "hora": hora, "fuente": fuente}
            if ult["fecha"] == fecha:
                p[-1] = fila
            else:
                p.append(fila)
            json.dump(p, open(pp, "w", encoding="utf-8"), ensure_ascii=False)
            fp = os.path.join(DATA, "pronostico.json")
            pr = json.load(open(fp, encoding="utf-8"))
            if pr and pr[0].get("tipo") == "ultimo dato":
                pr[0].update({"fecha": fecha, "min_m": h, "max_m": h})
                json.dump(pr, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
            cambio, msg = True, f"Paraná {h:.2f} m ({fuente}, {fecha} {hora})".replace(".", ",", 1)

    sp = os.path.join(DATA, "situacion.json")
    st = json.load(open(sp, encoding="utf-8"))
    if st:
        if corr and (st[0].get("corrientes_m") != corr[1] or st[0].get("corrientes_fecha") != corr[0].strftime("%Y-%m-%d")):
            st[0]["corrientes_m"] = corr[1]
            st[0]["corrientes_fecha"] = corr[0].strftime("%Y-%m-%d")
            cambio = True
            if not msg.startswith("Paraná"):
                msg = f"Corrientes {corr[1]:.2f} m".replace(".", ",", 1)
        # compuertas: lo que anuncia la APA manda. Si la APA no dijo nada desde que el Paraná cruzó los 6 m
        # (para arriba o para abajo), se aplica su manual de operación: 6 m o más, cerradas; menos de 6 m, abiertas.
        try:
            cierre = 6.0
            arriba = float(p[-1]["altura_m"]) >= cierre
            desde = p[-1]["fecha"]
            for r in reversed(p):
                if (float(r["altura_m"]) >= cierre) == arriba: desde = r["fecha"]
                else: break
            m = re.search(r"/(20\d\d)/(\d\d)/(\d\d)/", str(st[0].get("fuente_url", "")))
            inf = st[0].get("compuertas_fecha_apa") or st[0].get("fuente_fecha") or (f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else "")
            base_apa = st[0].get("compuertas_base", "APA") == "APA" and re.search(r"abiert|cerrad", str(st[0].get("compuertas_rio_negro", "")), re.I)
            if not (base_apa and inf and inf >= desde):
                estado = "Cerradas" if arriba else "Abiertas"
                if st[0].get("compuertas_rio_negro") != estado or st[0].get("compuertas_base") != "manual":
                    st[0]["compuertas_rio_negro"] = estado
                    st[0]["compuertas_base"] = "manual"
                    st[0]["resumen"] = ("El Paraná está sobre 6 m: según el manual de la APA, las compuertas se cierran y el agua del Río Negro sale por bombeo."
                                        if arriba else "El Paraná está debajo de 6 m: según el manual de la APA, las compuertas están abiertas.")
                    cambio = True
                    msg = (msg + "; " if msg.startswith("Paraná") else "") + f"compuertas {estado.lower()} (manual de la APA)"
        except Exception as e:
            print("regla de compuertas: error", e)
        # imagen satelital (Sentinel-2): busca una pasada nueva con pocas nubes sobre el dique
        try:
            import sat_s2
            r = sat_s2.actualizar(os.path.join(DATA, "satelite.json"), pp)
            if r:
                cambio = True
                msg = (msg + "; " if msg.startswith("Paraná") else "") + r
        except Exception as e:
            print("satélite: error", e)
        if cambio:
            # "Revisado" = la última vez que entró un dato nuevo (el robot mira cada 10 minutos)
            st[0]["actualizado"] = ahora.replace(microsecond=0).isoformat()
            json.dump(st, open(sp, "w", encoding="utf-8"), ensure_ascii=False)

    print(f"CAMBIO={1 if cambio else 0} {msg}")


if __name__ == "__main__":
    main()
