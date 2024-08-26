import uuid
import random
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.db import get_session, AsyncSession
from api.models.catalog import Person, Study, Building, Space
from faker import Faker
from api.services.geo import GeoService

router = APIRouter()


class SeedStatus(BaseModel):
    """Response model to validate and return when performing a health check."""
    status: str = "OK"


@router.put("")
async def seed(session: AsyncSession = Depends(get_session)) -> SeedStatus:
    fake = Faker()
    outdoor_envs = ["rural", "urban", "suburban", "other"]
    spaces = ["outdoor", "classroom", "NA"]
    ventilation = ["natural", "mechanical", "NA"]
    smoking = ["yes", "no", "NA"]

    geoService = GeoService()

    for i in range(0, 3):
        study = Study(identifier=f"seed-{uuid.uuid4()}",
                      name=fake.word(),
                      description=fake.paragraph(nb_sentences=2),
                      building_count=random.randint(1, 10),
                      space_count=random.randint(1, 100),
                      start_year=random.randint(2000, 2010),
                      end_year=random.randint(2010, 2020))

        session.add(study)
        await session.commit()
        await session.refresh(study)

        # study contact
        contact = Person(name=fake.name(), email=fake.email(),
                         institution=fake.company(), study_id=study.id)

        session.add(contact)
        await session.commit()
        await session.refresh(contact)

        # study buildings
        for j in range(0, 3):
            place = fake.location_on_land()
            zone = geoService.readClimateZone(place[1], place[0], False)
            elevation = geoService.queryElevation(place[1], place[0])

            building = Building(identifier=f"seed-{j}",
                                city=place[2],
                                country=place[3],
                                timezone=place[4],
                                altitude=elevation.altitude,
                                climate_zone=zone.name,
                                long=float(place[1]),
                                lat=float(place[0]),
                                outdoor_env=fake.word(
                                    ext_word_list=outdoor_envs),
                                construction_year=(study.start_year - 1),
                                renovation_year=(study.start_year + 9),
                                study_id=study.id)
            session.add(building)
            await session.commit()
            await session.refresh(building)

            # study building spaces
            for k in range(0, 10):
                space = Space(identifier=f"seed-{j}-{k}",
                              space=fake.word(ext_word_list=spaces),
                              ventilation=fake.word(ext_word_list=ventilation),
                              smoking=fake.word(ext_word_list=smoking),
                              study_id=study.id,
                              building_id=building.id)
                session.add(space)
                await session.commit()
                await session.refresh(space)

    return SeedStatus(status="OK")
