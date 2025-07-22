from fastapi import APIRouter, Depends, Query
from api.db import get_session, AsyncSession
from api.models.geo import Geometry, BuildingFeature, BuildingFeatures, BuildingProperties, ClimateZone, Elevation, TimeZone
from api.services.geo import GeoService
from api.services.study import StudyService
from api.services.building import BuildingService
from timezonefinder import TimezoneFinder
from api.utils.colors import string_to_color


router = APIRouter()
tf = TimezoneFinder()


@router.get("/buildings")
async def getBuildings(session: AsyncSession = Depends(get_session)) -> BuildingFeatures:
    studyResults = await StudyService(session).find({}, [], [])
    buildingsResult = await BuildingService(session).find({}, [], [])

    # map study id to study identifier
    studyColorsDict = {
        study.id: {"study": study, "color": string_to_color(study.identifier)} for study in studyResults.data}
    # aggs = Room.aggregate({"$group": {"_id": {"building": "$building", "ventilation": "$ventilation"}, "count": {"$sum": 1}}})

    features = []
    for building in buildingsResult.data:
        # roomAggs = await Room.find(Room.building.id == building.id).aggregate([{"$group": {"_id": "$ventilation", "count": {"$sum": 1}}}]).to_list()
        # "|".join(map(lambda agg: agg["_id"], filter(lambda agg: agg["count"] > 0, roomAggs)))
        mechanical_ventilation_types = "|".join(
            set([space.mechanical_ventilation_type for space in building.spaces if space.mechanical_ventilation_type is not None]))
        geometry = Geometry(
            coordinates=[building.long, building.lat], type="Point")
        properties = BuildingProperties(id=str(building.id),
                                        identifier=str(building.identifier),
                                        country=building.country, city=building.city,
                                        climate_zone=building.climate_zone,
                                        altitude=building.altitude,
                                        age_group=building.age_group,
                                        socioeconomic_status=building.socioeconomic_status,
                                        building_type=building.type,
                                        construction_year=building.construction_year,
                                        outdoor_env=building.outdoor_env,
                                        mechanical_ventilation=building.mechanical_ventilation,
                                        mechanical_ventilation_types=mechanical_ventilation_types,
                                        spaces_count=len(building.spaces),
                                        study_id=studyColorsDict[building.study_id]["study"].identifier,
                                        study_name=studyColorsDict[building.study_id]["study"].name,
                                        color=studyColorsDict[building.study_id]["color"],)
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


@router.get("/timezone")
async def getTimezone(lon: float = Query(0), lat: float = Query(0)) -> TimeZone:
    return TimeZone(name=tf.timezone_at(lng=lon, lat=lat), lon=lon, lat=lat)
