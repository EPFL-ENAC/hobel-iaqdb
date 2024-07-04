from fastapi import APIRouter, Query
from api.models.catalog import Building
from api.models.geo import Geometry, BuildingFeature, BuildingFeatures, BuildingProperties, ClimateZone, Elevation
from api.services.geo import GeoService

router = APIRouter()


@router.get("/buildings")
async def getBuildings() -> BuildingFeatures:
    buildings = await Building.find_all().to_list()

    features = []
    for building in buildings:
        geometry = Geometry(coordinates=building.location, type="Point")
        properties = BuildingProperties(identifier=building.identifier,
                                        country=building.country, city=building.city,
                                        climate_zone=building.climate_zone,
                                        altitude=building.altitude)
        feature = BuildingFeature(
            geometry=geometry, properties=properties, type="Feature")
        features.append(feature)
    return BuildingFeatures(features=features, type="FeatureCollection")


@router.get("/climate-zone")
async def getClimateZone(lon: float = Query(0), lat: float = Query(0), precise: bool = Query(False)) -> ClimateZone:
    service = GeoService()
    return service.readClimateZone(lon, lat, precise)


@router.get("/elevation")
async def getElevation(lon: float = Query(0), lat: float = Query(0)) -> Elevation:
    service = GeoService()
    return service.queryElevation(lon, lat)
