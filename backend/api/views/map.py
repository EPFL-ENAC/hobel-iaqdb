from typing import List
from fastapi import APIRouter
from api.models.study import Building
from api.models.geo import Geometry, BuildingFeature, BuildingFeatures, BuildingProperties
from beanie import PydanticObjectId

router = APIRouter()


@router.get("/buildings")
async def getBuildings() -> BuildingFeatures:
    buildings = await Building.find_all().to_list()

    features = []
    for building in buildings:
        geometry = Geometry(coordinates=building.location, type="Point")
        properties = BuildingProperties(slug=building.slug,
                                        country=building.country, city=building.city,
                                        climate_zone=building.climate_zone,
                                        altitude=building.altitude)
        feature = BuildingFeature(
            geometry=geometry, properties=properties, type="Feature")
        features.append(feature)
    return BuildingFeatures(features=features, type="FeatureCollection")
