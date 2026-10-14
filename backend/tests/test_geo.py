from unittest.mock import MagicMock, patch

from api.models.catalog import Building
from api.services import geo
from api.services.geo import GeoService
from api.services.study_parser import StudyParser


def fake_get(url, params=None, **kwargs):
    resp = MagicMock()
    if "locations" in params:
        resp.json.return_value = {"results": [{"elevation": 495.4}]}
    elif params["q"] == "nowhere":
        resp.json.return_value = []
    else:
        resp.json.return_value = [{"lon": "6.6323", "lat": "46.5197"}]
    return resp


def test_locate_buildings_cached():
    geo._geocode.cache_clear()
    geo._elevation.cache_clear()
    buildings = [
        Building(id=0, identifier="a", city="Lausanne", country="CH"),
        Building(id=1, identifier="b", city=" lausanne ", country="ch"),
        Building(id=2, identifier="c", city="Lausanne", country="CH", altitude=1),
        Building(id=3, identifier="d", city="nowhere", country="CH"),
    ]
    parser = StudyParser()
    with patch.object(geo.requests, "get", side_effect=fake_get) as get:
        parser.locate_buildings(buildings)
    # one geocoding for Lausanne, one for nowhere, one elevation
    assert get.call_count == 3
    a = buildings[0]
    assert (a.long, a.lat, a.altitude) == (6.6323, 46.5197, 495)
    assert a.climate_zone == "Cfb"
    assert a.timezone == "Europe/Zurich"
    assert buildings[1].lat == a.lat
    assert buildings[2].altitude == 1  # existing value kept
    assert buildings[3].lat is None
    assert [e.loc for e in parser.errors] == ["building[3].city"]


def test_locate_failure_not_cached():
    geo._geocode.cache_clear()
    with patch.object(geo.requests, "get", side_effect=OSError("down")):
        assert GeoService().locate("Geneva", "CH") is None
    with patch.object(geo.requests, "get", side_effect=fake_get):
        assert GeoService().locate("Geneva", "CH") is not None
