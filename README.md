# Apurate José · River flood dashboard

**[apuratejose.com.ar](https://apuratejose.com.ar)** · A one-page public dashboard that follows the Paraná River flood in Resistencia (Chaco, Argentina) and what it means for the city's Río Negro dam. It puts river height, flood gates and rain in one place, keeps itself up to date and uses official sources only.

*[Español más abajo](#español)*

---

## What the page shows

- **River height now**: the latest reading, the change since yesterday, the trend over the last 7 days and the distance to the alert and evacuation levels.
- **Chart**: the last 15 days or 3 months, plus the official forecast. A slider lets visitors pick a day or simulate a higher river.
- **Dam diagram**: the Río Negro dam with gates open or closed, the pumps and the rain forecast for the next days, all animated from the data.
- **Rain forecast**: the next 4 days.
- **History**: the 1983 flood compared with today.
- **Satellite**: the latest two cloud-free Sentinel‑2 images of the dam, with a slider to compare them.
- **Share button**: shares a text built from the current data. Each update also redraws the link preview card (`og.png`), so WhatsApp, X and Facebook show the latest height.

Every sentence on the page is written from the data. For example, if no rain is forecast, the page never says "the marked days".

## How it works

```
fuente/
  page.html          the page: HTML, CSS and JavaScript (uses d3)
  data/*.json        all the data the page shows
  armar_sitio.py     builds index.html from page.html + data
  build_public.py    embeds the data into the page
  agp_update.py      the hourly robot: fetches the river height and updates the data
  sat_s2.py          looks for a new cloud-free Sentinel-2 image of the dam
  og.py              draws the share card (fuente/data/og.png)
  fonts/             fonts for the share card (Liberation, SIL OFL)
.github/workflows/altura_horaria.yml   runs the robot every 10 minutes
index.html           the built site (served by GitHub Pages)
ACTUALIZAR.md        checklist for the twice-daily manual/AI review (forecast, gates, rain)
```

The site is static: no server and no database. The robot runs on GitHub Actions. When a reading is newer, it updates `fuente/data`, rebuilds `index.html` and commits.

### Data files

| File | What it holds |
|---|---|
| `parana_barranqueras.json` | one row per day: `fecha`, `altura_m`, `hora`, `fuente` |
| `umbrales.json` | the levels that matter (warning, alert, evacuation) and what happens at each |
| `pronostico.json` | official forecast ranges by date |
| `lluvia.json` | rain forecast by day (`nivel` 0, 1 or 2, mm, probability) |
| `situacion.json` | gate status, forecast text, upstream station, links to sources |
| `historicos.json` | historic floods for the comparison |
| `satelite.json` | the two satellite images (embedded) |

## Using it for another river

1. **Copy it.** Click **Use this template** (or **Fork**). You get your own copy and your own site. Nothing you do there touches apuratejose.com.ar.
2. **Remove what is ours:**
   - `CNAME` (our domain). Put yours or delete it.
   - Analytics: `fuente/page.html` loads Cloudflare Web Analytics and Microsoft Clarity only on our domains, so your copy sends nothing to our accounts. To measure your own site, put your domain and your own IDs in that block (search for `DOMINIOS`).
3. **Pick a height source** for your river and rewrite the fetch in `fuente/agp_update.py`, which today reads a port gauge and a backup source. Most countries publish gauges in real time. In England, for example, the Environment Agency has a public flood monitoring API. In Spain, each river basin publishes its own SAIH network.
4. **Set your levels** in `umbrales.json`, then reset `parana_barranqueras.json` with a few days of your river.
5. **Satellite:** change `BBOX` in `fuente/sat_s2.py` to the area you want to show.
6. **Rain:** fill `lluvia.json` from your weather service.
7. **Texts:** the page is in Spanish and written for Resistencia. The dam, gates, pumps and 1983 sections are specific to this place. Rewrite them for your river, or remove them.
8. **Turn it on:** in your copy, enable GitHub Actions (forks start with them off) and GitHub Pages (branch `main`, folder `/`).

To build the page locally: `python3 fuente/armar_sitio.py`, then open `index.html`.

## Sources used here

Height: Puerto de Barranqueras gauge (AGP) and Prefectura Naval via INA. Forecast: INA and APA Chaco. Rain: SMN and Meteored. Satellite: Copernicus Sentinel‑2 (Earth Search, AWS open data). Thresholds: APA Chaco operations manual (Res. 049/02), INA, Prefectura.

## License

Code: [MIT](LICENSE). Please keep the credit. The data belongs to the agencies that publish it, and each one has its own terms.

---

## Español

**[apuratejose.com.ar](https://apuratejose.com.ar)** es una página pública que sigue la crecida del Paraná en Resistencia (Chaco) y cómo afecta al dique del Río Negro. Junta en un solo lugar la altura del río, las compuertas y la lluvia, se actualiza sola y usa solo fuentes oficiales.

**Para usarla en otro río:** tocá **Use this template** (o **Fork**). Te queda una copia propia, con tu propio sitio, y nada de lo que hagas ahí toca apuratejose.com.ar. Después seguí los pasos de arriba ("Using it for another river"). Los más importantes son estos:

- sacar nuestro `CNAME` (la analítica solo funciona en nuestros dominios, así que tu copia no nos manda nada; para medir la tuya, poné tu dominio y tus códigos donde dice `DOMINIOS`);
- cambiar de dónde sale la altura en `fuente/agp_update.py`;
- poner tus niveles en `umbrales.json`;
- reescribir los textos que son de Resistencia (dique, compuertas, bombas, 1983).

Hecho por Pablo Dodda. Código con licencia MIT.
