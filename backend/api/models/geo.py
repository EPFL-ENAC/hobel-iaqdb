from typing import List, Literal
from pydantic import Field, BaseModel


class Geometry(BaseModel):
    coordinates: List[float]
    type: Literal['Point']


class BuildingProperties(BaseModel):
    slug: str
    country: str
    city: str
    altitude: int
    climate_zone: str


class BuildingFeature(BaseModel):
    geometry: Geometry
    properties: BuildingProperties
    type: Literal['Feature']


class BuildingFeatures(BaseModel):
    features: List[BuildingFeature]
    type: Literal['FeatureCollection']
