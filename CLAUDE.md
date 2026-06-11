# CLAUDE.md – Vätternrundan väderprognos

Fristående webapp som förutspår vädret längs Vätternrundan (315 km) utifrån
starttid, snittfart och stopptid per depå. Två flikar: **Planera rundan**
(tabell depå för depå) och **Var jag är nu** (live-position + aktuell tid).

## Stack

- **Backend:** FastAPI (`app.py`) + httpx. Serverar `index.html` och
  `POST /api/weather` som hämtar och normaliserar prognoser från två källor.
- **Frontend:** en enda statisk `index.html` (vanilla JS, ingen build).
- **Väderkällor:** yr.no (MET Norway Locationforecast 2.0) och SMHI
  (SNOW1g v1 – pmp3g lades ner 2026-03-31).
- **Deploy:** Render Web Service via `render.yaml`.

## Köra lokalt

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --reload --port 8123
# http://localhost:8123
```

## Viktigt att veta

- MET Norway kräver en identifierande `User-Agent` och tillåter inte direkta
  webbläsaranrop (CORS) – därför går allt väder via backend-proxyn.
- All tids-/vindlogik körs i frontend, så ändrad stopptid räknar om
  ankomsttiderna direkt utan att hämta om väderdata.
- Geolocation (`Var jag är nu`) kräver HTTPS – fungerar på Render och
  localhost, men inte över osäker http.
- Depådata (avstånd, koordinater, färdriktning) ligger i `DEPOTS` i
  `index.html`. Avstånd enligt vatternrundan.se.

## Repo & deploy

- GitHub: https://github.com/Jakesnake71/vatternrundan-vader
- Push till `main` → Render auto-deployar (när tjänsten är kopplad).
