# Vätternrundan – Väderprognos

En liten webapp som förutspår vädret längs [Vätternrundan](https://www.vatternrundan.se) (315 km) utifrån din **starttid** och **snittfart**.

Du fyller i startdatum, starttid och snittfart – appen räknar ut din ankomsttid till varje depå och hämtar väderprognosen för just den timmen och platsen. Den visar temperatur, vind, och om du får med- eller motvind baserat på cykelriktningen i varje etapp.

## Funktioner

- Ankomsttid per depå utifrån avstånd och snittfart (med valfritt depåstopp)
- Temperatur, vindstyrka och vindriktning per depå
- **Med-/mot-/sidvind** uträknat mot färdriktningen i varje etapp
- Nederbörd (torrt / risk för skur / regn) med sannolikhet
- Inga API-nycklar – väderdata från det öppna [Open-Meteo](https://open-meteo.com)

## Depåer

Motala (start) → Ödeshög (47 km) → Ölmstad (83) → Jönköping (104, vändpunkt) → Fagerhult (133) → Hjo (171) → Karlsborg (204) → Boviken (225) → Askersund (256) → Godegård (284) → Mål Motala (315).

Avstånd enligt [vatternrundan.se/sv/guide/depaer](https://www.vatternrundan.se/sv/guide/depaer).

## Köra lokalt

Det är en helt statisk sida – öppna `index.html` i en webbläsare, eller:

```bash
python3 -m http.server 8000
# besök http://localhost:8000
```

## Deploy

Deployas som **Static Site** på [Render](https://render.com) via `render.yaml` (Blueprint). Pushar du till `main` deployar Render automatiskt.

## Begränsningar

- Prognosens räckvidd är ~16 dygn framåt; längre fram visas "utanför prognosfönstret".
- Vindprognos är osäker – betrakta med-/motvind som en indikation.

---
Väderdata: [Open-Meteo](https://open-meteo.com) (CC BY 4.0).
