# Vätternrundan – Väderprognos

En webapp som förutspår vädret längs [Vätternrundan](https://www.vatternrundan.se) (315 km) utifrån din **starttid**, **snittfart** och **stopptid per depå**.

Du fyller i startdatum, starttid och snittfart. Appen räknar ut din ankomsttid till varje depå och hämtar väderprognosen för just den timmen och platsen – från **två officiella källor sida vid sida**:

- 🇳🇴 **yr.no** (MET Norway, Locationforecast 2.0)
- 🇸🇪 **SMHI** (meteorologisk prognos, SNOW1g v1)

För varje depå visas temperatur, vind, nederbörd och om du får med-, mot- eller sidvind baserat på cykelriktningen i etappen.

## Funktioner

- Ankomsttid per depå utifrån avstånd och snittfart
- **Stopptid per depå** som du kan ställa in individuellt – tiderna räknas om direkt
- Temperatur, vindstyrka/-riktning och nederbörd per depå, från **både yr.no och SMHI**
- **Med-/mot-/sidvind** uträknat mot färdriktningen i varje etapp
- Inga API-nycklar

## Depåer

Motala (start) → Ödeshög (47 km) → Ölmstad (83) → Jönköping (104, vändpunkt) → Fagerhult (133) → Hjo (171) → Karlsborg (204) → Boviken (225) → Askersund (256) → Godegård (284) → Mål Motala (315).

Avstånd enligt [vatternrundan.se/sv/guide/depaer](https://www.vatternrundan.se/sv/guide/depaer).

## Arkitektur

En liten **FastAPI-backend** (`app.py`) som:

1. Serverar frontend (`index.html`).
2. Tillhandahåller `POST /api/weather` som hämtar och normaliserar prognoser från yr.no och SMHI.

Backend behövs eftersom MET Norway kräver en identifierande `User-Agent` och inte tillåter direkta anrop från webbläsaren (CORS). All tids- och vindlogik körs i frontend, så ändrade stopptider räknas om direkt utan att hämta om väderdata.

## Köra lokalt

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --reload --port 8123
# besök http://localhost:8123
```

## Deploy

Deployas som **Web Service** på [Render](https://render.com) via `render.yaml` (Blueprint). Push till `main` deployar automatiskt.

## Begränsningar

- Prognosens räckvidd är ~10 dygn framåt; längre fram saknas data.
- Vindprognos är osäker – betrakta med-/motvind som en indikation.
- klart.se har inget officiellt publikt API och används därför inte; SMHI är Sveriges officiella myndighetskälla.

---
Källor: [yr.no](https://www.yr.no) (MET Norway, [NLOD/CC BY 4.0](https://api.met.no/doc/License)) och [SMHI](https://www.smhi.se) (CC BY 4.0).
