# Cómo actualizar apuratejose.com.ar

Sitio público "Crecida del Paraná · Resistencia" (GitHub Pages, dominio apuratejose.com.ar).
Lo leen familiares y amigos en Resistencia, Chaco: todo texto nuevo va en español simple, sin guiones largos.

Estructura:
- `index.html`: la página publicada. NO se edita a mano: se genera con `python3 fuente/armar_sitio.py`.
- `fuente/page.html`: el diseño de la página. No lo cambies en las actualizaciones automáticas.
- `fuente/data/*.json`: los datos. Es lo único que cambia en cada actualización.
- `fuente/build_public.py`, `fuente/armar_sitio.py`, `fuente/sat_update.py`: scripts.

## Qué hacer en cada corrida

Mirá la hora actual en Argentina (`TZ=America/Argentina/Buenos_Aires date`).
- Corrida de la mañana (antes de las 11): ACTUALIZACIÓN COMPLETA (pasos 1 a 7).
- Corridas de mediodía, tarde y noche: ACTUALIZACIÓN LIVIANA (pasos 1, 7 y, si encontrás algo nuevo de la APA sobre compuertas en una búsqueda rápida, el paso 3).

Si una fuente no responde, dejá ese archivo como está y seguí con el resto.

### 1. parana_barranqueras.json
Array `[{fecha:"YYYY-MM-DD", altura_m:number, hora?:"HH:MM"}]` ordenado por fecha.
- Fuente principal: Prefectura. `curl -sS -m 40 --http1.1 -A "Mozilla/5.0" https://contenidosweb.prefecturanaval.gob.ar/alturas/` y buscá las filas BARRANQUERAS y CORRIENTES (último registro, fecha y hora).
- Si no responde: https://fich.unl.edu.ar/cim/rios/historico/25 (tabla diaria) o https://fich.unl.edu.ar/cim/rios/parana/alturas.
- Si la lectura es más nueva que la última fila (fecha y hora), actualizá la fila de esa fecha o agregá una nueva, con `hora` en hora de Argentina. Mantené las filas existentes; corregí si la fuente cambió un valor.
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

Al final, resumí en una o dos líneas: altura y hora de la lectura, fuente usada, compuertas, y qué archivos cambiaron.
