"""
Vätternrundan väderprognos – backend.

Serverar den statiska frontend-sidan och en /api/weather-endpoint som hämtar
väderprognoser från två officiella källor och normaliserar dem till samma form:

  * yr.no   – MET Norway Locationforecast 2.0 (kräver egen User-Agent)
  * SMHI    – Meteorologisk prognos (pmp3g v2)

Frontend skickar depåernas koordinater, får hela tidsserien per källa tillbaka,
och väljer själv rätt timme utifrån användarens ankomsttid (som beror på
starttid, snittfart och stopptid per depå). Det gör att appen kan räkna om
direkt när användaren ändrar stopptider utan att hämta om data.
"""
from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Vätternrundan väderprognos")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# MET Norway kräver en identifierande User-Agent med kontaktuppgift.
USER_AGENT = (
    "VatternrundanVader/1.0 "
    "(+https://github.com/Jakesnake71/vatternrundan-vader; jacob.ekstrom@leanon.se)"
)
MET_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
# pmp3g lades ner 2026-03-31; SNOW1g v1 är efterföljaren.
SMHI_URL = (
    "https://opendata-download-metfcst.smhi.se/api/category/snow1g/version/1"
    "/geotype/point/lon/{lon}/lat/{lat}/data.json"
)

# Enkel process-cache så vi inte hamrar källorna (nyckel: avrundad koordinat).
_CACHE: dict[str, tuple[float, list[dict]]] = {}
_CACHE_TTL = 600  # sekunder


class Point(BaseModel):
    lat: float
    lon: float


class WeatherRequest(BaseModel):
    points: list[Point]


def _epoch(iso: str) -> int:
    """ISO-8601 (UTC) -> epoch-sekunder."""
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


# --- Normalisering av vädersymboler till gemensamma kategorier ---------------

def _met_category(symbol_code: str | None) -> str:
    if not symbol_code:
        return "unknown"
    s = symbol_code.split("_")[0]  # ta bort _day/_night/_polartwilight
    if "thunder" in s:
        return "thunder"
    if "sleet" in s:
        return "sleet"
    if "snow" in s:
        return "snow"
    if "showers" in s or "rainshowers" in s:
        return "showers"
    if "rain" in s:
        return "rain"
    if s == "fog":
        return "fog"
    if s == "cloudy":
        return "cloudy"
    if s == "partlycloudy":
        return "partlycloudy"
    if s == "fair":
        return "fair"
    if s == "clearsky":
        return "clear"
    return "unknown"


def _smhi_category(wsymb: int | None) -> str:
    if wsymb is None:
        return "unknown"
    table = {
        1: "clear", 2: "fair", 3: "partlycloudy", 4: "partlycloudy",
        5: "cloudy", 6: "cloudy", 7: "fog",
        8: "showers", 9: "showers", 10: "showers", 11: "thunder",
        12: "sleet", 13: "sleet", 14: "sleet",
        15: "snow", 16: "snow", 17: "snow",
        18: "rain", 19: "rain", 20: "rain", 21: "thunder",
        22: "sleet", 23: "sleet", 24: "sleet",
        25: "snow", 26: "snow", 27: "snow",
    }
    return table.get(wsymb, "unknown")


# --- Hämtning per källa ------------------------------------------------------

async def fetch_met(client: httpx.AsyncClient, lat: float, lon: float) -> list[dict]:
    r = await client.get(
        MET_URL,
        params={"lat": round(lat, 4), "lon": round(lon, 4)},
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    r.raise_for_status()
    series = r.json()["properties"]["timeseries"]
    out: list[dict] = []
    for entry in series:
        det = entry["data"]["instant"]["details"]
        nxt = entry["data"].get("next_1_hours") or entry["data"].get("next_6_hours") or {}
        nxt_det = nxt.get("details", {})
        symbol = (nxt.get("summary") or {}).get("symbol_code")
        out.append({
            "t": _epoch(entry["time"]),
            "temp": det.get("air_temperature"),
            "ws": det.get("wind_speed"),
            "wg": det.get("wind_speed_of_gust"),
            "wd": det.get("wind_from_direction"),
            "mm": nxt_det.get("precipitation_amount"),
            "cat": _met_category(symbol),
        })
    return out


async def fetch_smhi(client: httpx.AsyncClient, lat: float, lon: float) -> list[dict]:
    url = SMHI_URL.format(lon=round(lon, 4), lat=round(lat, 4))
    r = await client.get(url, timeout=15)
    r.raise_for_status()
    series = r.json()["timeSeries"]
    out: list[dict] = []
    for entry in series:
        d = entry["data"]
        sym = d.get("symbol_code")
        out.append({
            "t": _epoch(entry["time"]),
            "temp": d.get("air_temperature"),
            "ws": d.get("wind_speed"),
            "wg": d.get("wind_speed_of_gust"),
            "wd": d.get("wind_from_direction"),
            "mm": d.get("precipitation_amount_mean"),
            "cat": _smhi_category(int(sym) if sym is not None else None),
        })
    return out


async def fetch_point(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    key = f"{round(lat, 3)},{round(lon, 3)}"
    cached = _CACHE.get(key)
    if cached and (time.time() - cached[0]) < _CACHE_TTL:
        return cached[1]  # type: ignore[return-value]

    met, smhi = await asyncio.gather(
        fetch_met(client, lat, lon),
        fetch_smhi(client, lat, lon),
        return_exceptions=True,
    )
    result = {
        "met": met if not isinstance(met, Exception) else None,
        "smhi": smhi if not isinstance(smhi, Exception) else None,
        "met_error": str(met) if isinstance(met, Exception) else None,
        "smhi_error": str(smhi) if isinstance(smhi, Exception) else None,
    }
    _CACHE[key] = (time.time(), result)  # type: ignore[assignment]
    return result


@app.post("/api/weather")
async def weather(req: WeatherRequest):
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *(fetch_point(client, p.lat, p.lon) for p in req.points)
        )
    return JSONResponse({"points": results})


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def index():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))
