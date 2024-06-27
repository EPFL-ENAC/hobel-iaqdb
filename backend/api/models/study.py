from typing import List, Optional, Literal

import pymongo
from pydantic import Field, BaseModel

from beanie import Document, Indexed, Link, BackLink


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


class Building(Document):
    slug: str
    country: str
    city: str
    altitude: int
    climate_zone: str
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


class BuildingView(BaseModel):
    slug: str
    country: str
    city: str
    altitude: int
    climate_zone: str
    # rooms: Optional[List[Link["Room"]]]


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
