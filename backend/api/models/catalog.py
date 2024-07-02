from typing import List, Literal
import pymongo
from pydantic import Field, BaseModel
from beanie import PydanticObjectId, Document, Indexed, Link, BackLink


class ListResult(BaseModel):
    total: int
    skip: int | None
    limit: int | None


class Study(Document):
    slug: str
    name: str
    description: str
    # buildings: Optional[List[Link["Building"]]]

    class Settings:
        name = "studies"
        indexes = [
            [
                ("slug", pymongo.TEXT),
                ("name", pymongo.TEXT),
            ],
        ]


class StudiesResult(ListResult):
    data: List[Study]


class Building(Document):
    slug: str
    country: str
    city: str
    altitude: int
    climate_zone: str
    location: List[float]
    study: Link[Study]
    # rooms: Optional[List[Link["Room"]]]
    # study: BackLink[Study] = Field(original_field="buildings")

    class Settings:
        name = "buildings"
        indexes = [
            [
                ("slug", pymongo.TEXT),
            ],
        ]


class BuildingStudy(BaseModel):
    slug: str
    study: Link[Study]


class BuildingsResult(ListResult):
    data: List[Building]


class Room(Document):
    slug: str
    space: str
    ventilation: Literal['natural', 'mechanical', 'NA']
    smoking: Literal['yes', 'no', 'dnk']
    study: Link[Study]
    building: Link[Building]

    class Settings:
        name = "rooms"
        indexes = [
            [
                ("slug", pymongo.TEXT),
            ],
        ]


class RoomsResult(ListResult):
    data: List[Room]
