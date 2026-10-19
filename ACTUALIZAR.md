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
- Corrida de la noche (20 h): ACTUALIZACIÓN LIVIANA (pasos 1, 3 solo para compuertas y alerta, y 7).

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
Una fila: `{fecha, actualizado, alerta_apa, compuertas_rio_negro, tendencia, corrientes_m, corrientes_fecha, resumen, pronostico_texto, fuentes, fuente_url, pronostico_url?, compuertas_revisado}`.
- COMPUERTAS, EN TODAS LAS CORRIDAS (también la liviana de la noche): buscá en las noticias de HOY y de ayer qué dijo la APA o el gobierno del Chaco sobre las compuertas del dique del Río Negro, actualizá `compuertas_rio_negro` si hay algo nuevo, y poné SIEMPRE `compuertas_revisado` = fecha de hoy (YYYY-MM-DD) aunque no haya novedades. La página muestra "Revisado hoy" o avisa en naranja si hoy no se revisó. Si la APA habla de las bombas funcionando o del cierre pero sin decirlo claro, no pongas "Cerradas": no cambies el estado (queda el del manual) y contalo en `resumen`.
- Buscá SIEMPRE las noticias del día sobre la APA y el Paraná ("APA Morán Paraná", "APA compuertas río Negro", "Comité de Emergencia Chaco Paraná"), en La Voz del Chaco, Diario Norte, Data Chaco, Chaco Día por Día y chaco.gob.ar. Si hay un informe de la APA más nuevo que el de `fuente_url`, actualizá compuertas, alerta, pronóstico y `fuente_url` con ese informe.
- `compuertas_rio_negro`: siempre "Abiertas" o "Cerradas". Si la APA (o el gobierno del Chaco) lo anunció EXPLÍCITAMENTE, poné ese estado, `compuertas_base` = "APA" y `compuertas_fecha_apa` = fecha del anuncio (YYYY-MM-DD). Si no hay anuncio explícito, no lo toques: el robot de cada hora aplica el manual de la APA (6 m o más: "Cerradas"; menos de 6 m: "Abiertas") y pone `compuertas_base` = "manual". Nunca pongas "Sin confirmar".
- `fuente_url`: URL https de la nota o comunicado MÁS RECIENTE de la APA (si no hay nueva, dejá la anterior). La página muestra "Último informe de la APA: <fecha de la URL>"; si la URL no tiene la fecha en la ruta, poné `fuente_fecha` (YYYY-MM-DD) y `fuente_medio`.
- `pronostico_url`: URL de donde sale el pronóstico de `pronostico_texto` si NO es la misma nota de `fuente_url` (por ejemplo, el reporte del INA). Si es la misma, no lo pongas.
- `corrientes_m` y `corrientes_fecha`: los actualiza solo el robot de cada hora (INA). No los toques.
- `resumen`: UNA línea corta con el estado del Río Negro hoy (ej. "Dentro de su cauce. Las compuertas están abiertas (dato de la APA)."). No repitas la regla de los 6 m.
- `pronostico_texto`: una o dos oraciones con el pronóstico oficial vigente, empezando por quién lo dijo y cuándo (ej. "APA (14 oct): ..."). Si hay una alerta oficial vigente (ej. alerta naranja del Comité de Emergencia), nombrala acá también. `alerta_apa`: el color de esa alerta ("Amarilla", "Naranja", "Roja" o "").

### 4. umbrales.json e historicos.json
No cambian, salvo que la APA, el INA o la UNNE publiquen niveles nuevos.

### 5. lluvia.json
`[{fecha, nivel (0 sin lluvia, 1 lluvia posible, 2 lluvias y tormentas), lluvia, descripcion, mm (opcional), mm_modelo, prob_modelo}]` desde hoy a 3 días.
- nivel, lluvia, descripcion: SMN (oficial): https://ws.smn.gob.ar/map_items/forecast/0, /1, /2 y /3 (0 = hoy), entrada "Resistencia" (Chaco). Usá mañana y tarde para el nivel; descripción corta en español (máximo ~8 palabras). Si hay alerta del SMN por tormentas o lluvias para Resistencia o el departamento San Fernando, mencionala y, si el SMN da milímetros acumulados, ponelos en "mm" como texto (ej. "30 a 50 mm"); si no, omití "mm".
- mm_modelo (número, mm del día; 0 si no muestra lluvia) y prob_modelo (0 a 100, o null): Meteored, https://www.meteored.com.ar/tiempo-en_Resistencia-America+Sur-Argentina-Chaco-SARE-1-16890.html (estimación no oficial). Si no responde, dejá los valores anteriores para las fechas que coincidan.

### 6. satelite.json
No lo toques: la imagen satelital la actualiza sola el robot de cada hora (Sentinel-2).

### 6b. Control de coherencia (SIEMPRE, antes de publicar)
La página tiene que coincidir con sus fuentes. Si algo de esto falla, corregilo antes de publicar:
- Cada número de la página tiene una fuente con un link que lleva a ese mismo número: altura (fila `fuente` de parana_barranqueras.json), compuertas y pronóstico (`fuente_url` / `pronostico_url`), Corrientes (INA), lluvia (SMN y Meteored).
- `pronostico.json`: ninguna fila "pronostico" con fecha pasada; la primera fila es la última medición.
- `lluvia.json`: empieza HOY y sigue 2 o 3 días. Nada de días pasados.
- `pronostico_texto` no contradice la altura actual (ej. no decir "podría llegar a 5,50 m" si ya está en 5,53).
- Ningún texto dice "hoy" con un dato de otro día.

### 7. Publicar
1. En `situacion.json` poné `actualizado` = hora actual en ISO con zona -03:00 (ej. 2026-10-13T12:15:00-03:00), siempre que al menos una fuente haya respondido. Es lo que la página muestra arriba como "Última actualización".
2. `python3 fuente/armar_sitio.py`
3. Commit y push directo a `main` (sin ramas ni pull requests), con mensaje tipo "Datos: Paraná 5,19 m (12:00)". GitHub Pages publica solo en un par de minutos.

Al final, resumí en una o dos líneas: altura y hora de la lectura, qué mostraba cada una de las cuatro fuentes y cuál usaste, compuertas, y qué archivos cambiaron.
