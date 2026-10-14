import logging
import threading
import time
from functools import lru_cache
from importlib.resources import files

import rasterio
import requests
from api.config import config
from api.models.geo import ClimateZone, Elevation, Location
from timezonefinder import TimezoneFinder

logger = logging.getLogger(__name__)

CLIMATE_ZONES = [
    "Af",
    "Am",
    "Aw",
    "BWh",
    "BWk",
    "BSh",
    "BSk",
    "Csa",
    "Csb",
    "Csc",
    "Cwa",
    "Cwb",
    "Cwc",
    "Cfa",
    "Cfb",
    "Cfc",
    "Dsa",
    "Dsb",
    "Dsc",
    "Dsd",
    "Dwa",
    "Dwb",
    "Dwc",
    "Dwd",
    "Dfa",
    "Dfb",
    "Dfc",
    "Dfd",
    "ET",
    "EF",
]


@lru_cache(maxsize=2)
def _climate_raster(precise: bool):
    name = (
        "koppen_geiger_1991_2020_0p00833333.tif"
        if precise
        else "koppen_geiger_1991_2020_0p1.tif"
    )
    # opened once, only the requested cell is read (raster is EPSG:4326)
    return rasterio.open(str(files("api") / "data" / name))


# GDAL datasets are not thread-safe
_raster_lock = threading.Lock()

_tf = TimezoneFinder()

# Nominatim usage policy: max 1 request/s, identifying User-Agent, cache results
# ponytail: per-process throttle and cache, a shared store if several backend pods
_nominatim_lock = threading.Lock()
_nominatim_last = 0.0


def _nominatim_search(city: str, country: str) -> tuple[float, float] | None:
    global _nominatim_last
    with _nominatim_lock:
        wait = 1 - (time.monotonic() - _nominatim_last)
        if wait > 0:
            time.sleep(wait)
        try:
            resp = requests.get(
                config.GEOCODER_URL,
                params={
                    "q": city,
                    "countrycodes": country,
                    "format": "jsonv2",
                    "limit": 1,
                },
                headers={"User-Agent": f"iaqdb ({config.APP_URL})"},
                timeout=10,
            )
        finally:
            _nominatim_last = time.monotonic()
    resp.raise_for_status()
    results = resp.json()
    if not results:
        return None
    return float(results[0]["lon"]), float(results[0]["lat"])


class GeoService:
    def readClimateZone(
        self, lon: float = 0, lat: float = 0, precise: bool = True
    ) -> ClimateZone:
        with _raster_lock:
            value = int(next(_climate_raster(precise).sample([(lon, lat)]))[0])
        name = "NA"
        if value > 0 and value <= 30:
            name = CLIMATE_ZONES[value - 1]
        return ClimateZone(id=value, name=name, lon=lon, lat=lat)

    def queryElevation(self, lon: float = 0, lat: float = 0) -> Elevation:
        resp = requests.get(
            f"{config.ELEVATION_URL}",
            params={"locations": f"{lat},{lon}"},
            timeout=10,
        )
        content = resp.json()
        place = content["results"][0]
        return Elevation(altitude=place["elevation"], lon=lon, lat=lat)

    def locate(self, city: str | None, country: str | None) -> Location | None:
        """Geolocate a city in a country (ISO2), None when not found or when
        the geocoder fails. Buildings often share the same location, so
        external lookups are cached (failures are not, to be retried)."""
        if not city or not country:
            return None
        try:
            coords = _geocode(city.strip().lower(), country.strip().lower())
        except Exception as e:
            logger.warning(f"Geocoding '{city}, {country}' failed: {e}")
            return None
        if coords is None:
            return None
        lon, lat = coords
        altitude = None
        try:
            altitude = _elevation(lon, lat)
        except Exception as e:
            logger.warning(f"Elevation of '{city}, {country}' failed: {e}")
        zone = self.readClimateZone(lon, lat)
        return Location(
            long=lon,
            lat=lat,
            altitude=altitude,
            climate_zone=zone.name if zone.name != "NA" else None,
            timezone=_tf.timezone_at(lng=lon, lat=lat),
        )


@lru_cache(maxsize=4096)
def _geocode(city: str, country: str) -> tuple[float, float] | None:
    return _nominatim_search(city, country)


@lru_cache(maxsize=4096)
def _elevation(lon: float, lat: float) -> int:
    return round(GeoService().queryElevation(lon, lat).altitude)
