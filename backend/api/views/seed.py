import uuid
import random
from fastapi import APIRouter
from pydantic import BaseModel
from api.models.catalog import Person, Study, Building, Room
from faker import Faker
from api.services.geo import GeoService

router = APIRouter()


class SeedStatus(BaseModel):
    """Response model to validate and return when performing a health check."""
    status: str = "OK"


@router.put("")
async def seed() -> SeedStatus:
    fake = Faker()
    climate_zones = [
        "Af",
        "Am",
        "Aw",
        "BWh",
        "BWk",
        "BSh",
        "BSk",
        "Csa",
        "Csb",
        "Csc",
        "Cwa",
        "Cwb",
        "Cwc",
        "Cfa",
        "Cfb",
        "Cfc",
        "Dsa",
        "Dsb",
        "Dsc",
        "Dsd",
        "Dwa",
        "Dwb",
        "Dwc",
        "Dwd",
        "Dfa",
        "Dfb",
        "Dfc",
        "Dfd",
        "ET",
        "EF",
    ]
    spaces = ["outdoor", "classroom", "NA"]
    ventilation = ["natural", "mechanical", "NA"]
    smoking = ["yes", "no", "NA"]

    geoService = GeoService()

    for i in range(0, 10):
        contact = Person(name=fake.name(), email=fake.email(),
                         institution=fake.company())
        study = Study(identifier=f"seed-{uuid.uuid4()}",
                      name=fake.word(),
                      description=fake.paragraph(nb_sentences=2),
                      contact=contact,
                      building_count=10,
                      room_count=100,
                      start_year=random.randint(2000, 2010),
                      end_year=random.randint(2010, 2020))
        study = await Study.insert_one(study)

        for j in range(0, 10):
            place = fake.location_on_land()
            zone = geoService.readClimateZone(place[1], place[0], False)
            elevation = geoService.queryElevation(place[1], place[0])

            building = Building(identifier=f"seed-{uuid.uuid4()}",
                                city=place[2],
                                country=place[3],
                                timezone=place[4],
                                altitude=elevation.altitude,
                                climate_zone=zone.name,
                                location=[place[1], place[0]],
                                study=study)
            building = await Building.insert_one(building)

            for k in range(0, 10):
                room = Room(identifier=f"seed-{uuid.uuid4()}",
                            space=fake.word(ext_word_list=spaces),
                            ventilation=fake.word(ext_word_list=ventilation),
                            smoking=fake.word(ext_word_list=smoking),
                            study=study,
                            building=building)
                room = await Room.insert_one(room)

    return SeedStatus(status="OK")
