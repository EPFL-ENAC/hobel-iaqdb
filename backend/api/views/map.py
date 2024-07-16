from fastapi import APIRouter, Query
from api.models.catalog import Building, Room
from api.models.geo import Geometry, BuildingFeature, BuildingFeatures, BuildingProperties, ClimateZone, Elevation
from api.services.geo import GeoService

router = APIRouter()


@router.get("/buildings")
async def getBuildings() -> BuildingFeatures:
    buildings = await Building.find_all().to_list()

    # aggs = Room.aggregate({"$group": {"_id": {"building": "$building", "ventilation": "$ventilation"}, "count": {"$sum": 1}}})

    features = []
    for building in buildings:
        roomAggs = await Room.find(Room.building.id == building.id).aggregate([{"$group": {"_id": "$ventilation", "count": {"$sum": 1}}}]).to_list()
        ventilations = "|".join(
            map(lambda agg: agg["_id"], filter(lambda agg: agg["count"] > 0, roomAggs)))
        geometry = Geometry(coordinates=building.location, type="Point")
        properties = BuildingProperties(id=str(building.id),
                                        identifier=building.identifier,
                                        country=building.country, city=building.city,
                                        climate_zone=building.climate_zone,
                                        altitude=building.altitude,
                                        ventilations=ventilations,
                                        study_id=str(building.study.ref.id))
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
