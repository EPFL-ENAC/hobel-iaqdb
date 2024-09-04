from fastapi import APIRouter, Depends, Query
from api.db import get_session, AsyncSession
from api.models.catalog import Building
from api.models.geo import Geometry, BuildingFeature, BuildingFeatures, BuildingProperties, ClimateZone, Elevation
from api.services.geo import GeoService
from api.services.building import BuildingService

router = APIRouter()


@router.get("/buildings")
async def getBuildings(session: AsyncSession = Depends(get_session)) -> BuildingFeatures:
    buildingsResult = await BuildingService(session).find({}, [], [])

    # aggs = Room.aggregate({"$group": {"_id": {"building": "$building", "ventilation": "$ventilation"}, "count": {"$sum": 1}}})

    features = []
    for building in buildingsResult.data:
        # roomAggs = await Room.find(Room.building.id == building.id).aggregate([{"$group": {"_id": "$ventilation", "count": {"$sum": 1}}}]).to_list()
        # "|".join(map(lambda agg: agg["_id"], filter(lambda agg: agg["count"] > 0, roomAggs)))
        ventilations = "|".join(
            set([space.mechanical_ventilation_type for space in building.spaces]))
        geometry = Geometry(
            coordinates=[building.long, building.lat], type="Point")
        properties = BuildingProperties(id=str(building.id),
                                        # building.identifier,
                                        identifier=str(building.id),
                                        country=building.country, city=building.city,
                                        climate_zone=building.climate_zone,
                                        altitude=building.altitude,
                                        ventilations=ventilations,
                                        study_id=str(building.study_id))
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
