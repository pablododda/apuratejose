# Cómo actualizar apuratejose.com.ar

Sitio público "Crecida del Paraná · Resistencia" (GitHub Pages, dominio apuratejose.com.ar).
Lo leen familiares y amigos en Resistencia, Chaco: todo texto nuevo va en español simple, sin guiones largos.

Estructura:
- `index.html`: la página publicada. NO se edita a mano: se genera con `python3 fuente/armar_sitio.py`.
- `fuente/page.html`: el diseño de la página. No lo cambies en las actualizaciones automáticas.
- `fuente/data/*.json`: los datos. Es lo único que cambia en cada actualización.
- `fuente/build_public.py`, `fuente/armar_sitio.py`, `fuente/sat_update.py`: scripts.

## Qué hacer en cada corrida

Además de esta rutina, un robot de GitHub Actions (`.github/workflows/altura_horaria.yml` con `fuente/agp_update.py`) actualiza la altura del Paraná CADA HORA desde la estación del puerto de Barranqueras (o Prefectura vía INA si la estación se cuelga). No lo toques. Vos igual revisá el paso 1: si encontrás una lectura más nueva que la última fila, cargala; si no, dejá el archivo como está.

Mirá la hora actual en Argentina (`TZ=America/Argentina/Buenos_Aires date`).
- Corrida de la mañana (antes de las 12): ACTUALIZACIÓN COMPLETA (pasos 1 a 7).
- Corrida de la noche (20 h): ACTUALIZACIÓN LIVIANA (pasos 1, 7 y, si encontrás algo nuevo de la APA sobre compuertas en una búsqueda rápida, el paso 3).

Si una fuente no responde, dejá ese archivo como está y seguí con el resto.

### 1. parana_barranqueras.json
Array `[{fecha:"YYYY-MM-DD", altura_m:number, hora?:"HH:MM", fuente?:string}]` ordenado por fecha.

Revisá SIEMPRE las cuatro fuentes (si una no responde, seguí con las otras) y anotá de cada una la última lectura de Barranqueras con su fecha y hora:

0) AGP (Administración General de Puertos), estación automática del puerto de Barranqueras, se actualiza CADA HORA. Es la más nueva casi siempre. Archivo de datos: `curl -sS -m 40 -A "Mozilla/5.0" https://hidrografia2.agpse.gob.ar/histdat/Barranqueras.dat` (CSV; la última línea es la más reciente: `"2026-10-14 10:00:00",5708,4.875006,5.522,0.647`). La altura es la CUARTA columna (`Altura_Avg`, ej. 5.522 → 5.52), NO la tercera (`NIvel_Avg`). Ignorá filas con "NAN". La hora ya está en hora argentina. Página para mirarla a mano: https://hidrografia2.agpse.gob.ar/Barranqueras/marea.html . `fuente`: "estación del puerto de Barranqueras". Ojo: esta estación marca unos 3 a 5 cm más que Prefectura a la misma hora.
a) Prefectura: `curl -sS -m 40 --http1.1 -A "Mozilla/5.0" https://contenidosweb.prefecturanaval.gob.ar/alturas/` y buscá la fila BARRANQUERAS (y CORRIENTES para situacion.json). Si corta la conexión, probá una vez más con `curl -sS -m 60 --http1.1 --retry 2 -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15" -H "Accept-Language: es-AR,es" https://contenidosweb.prefecturanaval.gob.ar/alturas/`. Muestra, por ejemplo, `13/OCT/26 - 0000`: eso es fecha 2026-10-13 y hora "00:00". `fuente`: "Prefectura".
b) INA, publicado por Hidráulica de Entre Ríos (datos de la red de Prefectura, en JSON): `curl -sS -m 40 -A "Mozilla/5.0" https://www.hidraulica.gob.ar/ina/ajax.estaciones.json.php` y buscá el objeto con `"nombre": "Barranqueras"`: `valor_actual` es la altura y `fecha_actual` ("13/10/2026 00:00") la fecha y hora. El historial diario está en `https://www.hidraulica.gob.ar/ina/ajax.historico.json.php?series_id=20&dias=10` (`[{ts:"2026-10-13T00:00:00", valor:5.27}]`). `fuente`: "Prefectura vía INA". La página para mirarla a mano es https://www.hidraulica.gob.ar/nivhidr.php
c) FICH (UNL): la tabla https://fich.unl.edu.ar/cim/rios/historico/25 (la primera fila es la más reciente, con su fecha y hora reales). NO uses https://fich.unl.edu.ar/cim/rios/parana/alturas para la fecha: esa página muestra la fecha de hoy aunque el dato sea de ayer. Si la fila más reciente repite la altura de la anterior con la variación vacía ("—"), es un dato repetido: no la uses. `fuente`: "FICH, UNL".

Cómo elegir:
- Usá la lectura con la fecha y hora MÁS NUEVAS de las cuatro (no la altura más alta: cuando el río baje, la más alta va a ser la más vieja).
- Si dos fuentes tienen lectura de la misma hora, preferí Prefectura (a o b). Si la estación del puerto no responde o su último dato tiene más de 3 horas, usá la más nueva de las otras. Entre FICH y Prefectura del mismo día, preferí Prefectura salvo que la de FICH sea de una hora claramente posterior y no sea un dato repetido.
- Guardá en la fila la fecha, la hora y la `fuente` EXACTAS de esa lectura. Nunca inventes ni copies una hora de otra fuente. La página muestra la fuente debajo de la altura.
- REGLA IMPORTANTE: solo podés agregar o cambiar la fila de un día si alguna fuente muestra una lectura de Barranqueras de ESE día. Si todas muestran todavía la de ayer, NO agregues una fila para hoy ni repitas el valor de ayer con fecha de hoy: dejá el archivo como está. La página avisa sola que la medición es de ayer.
- Si la lectura elegida es más nueva que la última fila (fecha y hora), actualizá la fila de esa fecha o agregá una nueva. Mantené las filas existentes; no cambies días pasados (cada día queda con la última lectura que se tomó ese día), salvo para corregir un error evidente (por ejemplo, una fila con fecha equivocada).
- Actualizá también la primera fila de `pronostico.json` (tipo "ultimo dato": fecha, min_m y max_m = esa altura).

### 2. pronostico.json
`[{fecha, min_m, max_m, tipo}]`. Primera fila: último dato medido (tipo "ultimo dato"). Las siguientes: pronóstico oficial vigente para Barranqueras (tipo "pronostico").
Fuentes: INA (https://www.ina.gov.ar/alerta/, reporte diario https://alerta.ina.gob.ar/a5/diario/reporte_diario, informe semanal) y comunicados de la APA Chaco en la prensa (buscá "APA Paraná Barranqueras pronóstico" de los últimos días). Solo números atribuidos a INA o APA. Si no hay número oficial nuevo, mantené el vigente y quitá fechas que ya pasaron.

### 3. situacion.json
Una fila: `{fecha, actualizado, alerta_apa, compuertas_rio_negro, tendencia, corrientes_m, resumen, pronostico_texto, fuentes, fuente_url}`.
- `compuertas_rio_negro`: "Abiertas" o "Cerradas" SOLO si la APA (o el gobierno del Chaco) lo informó en los últimos días (buscá "APA compuertas río Negro" en la prensa y en chaco.gov.ar). Si el Paraná superó 6 m en Barranqueras y no hay confirmación de la APA, poné "Sin confirmar".
- `fuente_url`: URL https de la nota o comunicado más reciente de la APA que usaste (si no hay nueva, dejá la anterior).
- `corrientes_m`: lectura de Corrientes (Prefectura o INA).
- `resumen`: UNA línea corta con el estado del Río Negro hoy (ej. "Dentro de su cauce. Las compuertas están abiertas (dato de la APA)."). No repitas la regla de los 6 m.
- `pronostico_texto`: una o dos oraciones con el pronóstico oficial vigente (INA/APA).

### 4. umbrales.json e historicos.json
No cambian, salvo que la APA, el INA o la UNNE publiquen niveles nuevos.

### 5. lluvia.json
`[{fecha, nivel (0 sin lluvia, 1 lluvia posible, 2 lluvias y tormentas), lluvia, descripcion, mm (opcional), mm_modelo, prob_modelo}]` desde hoy a 3 días.
- nivel, lluvia, descripcion: SMN (oficial): https://ws.smn.gob.ar/map_items/forecast/0, /1, /2 y /3 (0 = hoy), entrada "Resistencia" (Chaco). Usá mañana y tarde para el nivel; descripción corta en español (máximo ~8 palabras). Si hay alerta del SMN por tormentas o lluvias para Resistencia o el departamento San Fernando, mencionala y, si el SMN da milímetros acumulados, ponelos en "mm" como texto (ej. "30 a 50 mm"); si no, omití "mm".
- mm_modelo (número, mm del día; 0 si no muestra lluvia) y prob_modelo (0 a 100, o null): Meteored, https://www.meteored.com.ar/tiempo-en_Resistencia-America+Sur-Argentina-Chaco-SARE-1-16890.html (estimación no oficial). Si no responde, dejá los valores anteriores para las fechas que coincidan.

### 6. satelite.json (solo en la corrida de la mañana)
`pip install pillow` si falta, y desde la raíz del repo:
`python3 -I fuente/sat_update.py fuente/data/satelite.json fuente/data/parana_barranqueras.json fuente/data/satelite.json 30`
Si no hay acceso a gibs.earthdata.nasa.gov, dejalo como está.

### 7. Publicar
1. En `situacion.json` poné `actualizado` = hora actual en ISO con zona -03:00 (ej. 2026-10-13T12:15:00-03:00), siempre que al menos una fuente haya respondido. Es lo que la página muestra arriba como "Última actualización".
2. `python3 fuente/armar_sitio.py`
3. Commit y push directo a `main` (sin ramas ni pull requests), con mensaje tipo "Datos: Paraná 5,19 m (12:00)". GitHub Pages publica solo en un par de minutos.

Al final, resumí en una o dos líneas: altura y hora de la lectura, qué mostraba cada una de las cuatro fuentes y cuál usaste, compuertas, y qué archivos cambiaron.
