from typing import List, Literal, Optional
import pymongo
from pydantic import Field, BaseModel
from beanie import Document, Indexed, Link


class ListResult(BaseModel):
    total: int
    skip: int | None
    limit: int | None


class Person(BaseModel):
    name: str
    email: str
    institution: str


class GreenCertification(BaseModel):
    program: str
    level: str


class Study(Document):
    identifier: str
    name: str
    description: str
    contact: Optional[Person] = None
    building_count: Optional[int] = None
    room_count: Optional[int] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None

    class Settings:
        name = "studies"
        indexes = [
            [
                ("identifier", pymongo.TEXT),
                ("name", pymongo.TEXT),
                ("description", pymongo.TEXT),
            ],
        ]


class StudiesResult(ListResult):
    data: List[Study]


class Building(Document):
    identifier: str
    country: str
    city: str
    timezone: str
    altitude: int
    climate_zone: str
    location: List[float]  # [long, lat]
    type: Optional[str] = None                # ex: school
    special_population: Optional[str] = None  # ex: children
    outdoor_env: Optional[Literal["rural",
                                  "urban", "suburban", "other"]] = None
    construction_year: Optional[int] = None
    renovation_year: Optional[int] = None
    certifications: Optional[List[GreenCertification]] = None
    study: Link[Study]

    class Settings:
        name = "buildings"
        indexes = [
            [
                ("identifier", pymongo.TEXT),
            ],
        ]


class BuildingStudy(BaseModel):
    identifier: str
    study: Link[Study]


class BuildingsResult(ListResult):
    data: List[Building]


class Room(Document):
    identifier: str
    space: str
    ventilation: Literal["natural", "mechanical", "NA"]
    smoking: Literal["yes", "no", "NA"]
    study: Link[Study]
    building: Link[Building]

    class Settings:
        name = "rooms"
        indexes = [
            [
                ("identifier", pymongo.TEXT),
            ],
        ]


class RoomsResult(ListResult):
    data: List[Room]
