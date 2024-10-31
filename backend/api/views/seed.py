import uuid
import random
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.db import get_session, AsyncSession
from api.models.catalog import Person, Study, Building, Space, Instrument, InstrumentParameter
from faker import Faker
from api.services.geo import GeoService

router = APIRouter()


class SeedStatus(BaseModel):
    """Response model to validate and return when performing a health check."""
    status: str = "OK"


@router.put("")
async def seed(session: AsyncSession = Depends(get_session)) -> SeedStatus:
    fake = Faker()
    outdoor_envs = ["rural", "urban", "suburban", "industrialized", "other"]
    occupant_impacts = ["health", "comfort",
                        "performance", "well-being", "other"]
    special_populations = ["low-income",
                           "middle-income", "elderly", "children", "other", "NA"]
    other_indoor_params = ["thermal", "acoustic",
                           "visual", "architectural design", "other"]
    building_types = ["multifamily residential", "dwelling", "office",
                      "school", "senior center", "hospital", "retail", "sport center", "other"]
    occupancy_status = ["occupied", "unoccupied", "combined", "unknown"]
    ventilation_types = ["dilution", "displacement",
                         "exhaust only", "other", "unknown"]
    windows = ["open", "closed", "unknown", "NA"]
    cooling_types = ["forced air", "fan coil units",
                     "ceiling radiant", "floor radiant", "other", "unknown"]
    heating_types = ["forced air", "fan coil units", "ceiling radiant",
                     "floor radiant", "radiator", "other", "unknown"]
    major_combustion_sources = ["unvented kerosene and gas space heaters",
                                "wood stoves", "fireplaces", "gas stoves", "other"]
    minor_combustion_sources = ["candles", "incense", "other"]
    licenses = ["CC0",
                "CC BY",
                "CC BY-SA",
                "CC BY-NC",
                "CC BY-NC-SA",
                "PDDL",
                "ODC-By",
                "ODbL",
                "GPL",
                "MIT",
                "Apache2",
                "BSD",
                "UK OGL",
                "Canada OGL",
                "Australia OGL",
                "EUPL"]
    yes_no = ["yes", "no", "unknown"]
    on_off = ["on", "off", "unknown", "NA"]
    space_types = ["living room", "kitchen", "bedroom", "basement", "garage", "enclosed shared office", "enclosed private office",
                   "open office", "focus room", "hallway", "restaurant", "supermarket", "waiting room", "patient room", "other"]
    physical_params = [
        "individual voc",
        "tvoc",
        "pm10",
        "pm2.5",
        "pm1",
        "particle number ≤10μm",
        "particle number ≤2.5μm",
        "particle number ≤1μm",
        "nanoparticles",
        "carbon dioxide",
        "carbon monoxide",
        "ozone",
        "radon",
        "sulphur dioxide",
        "nitrogen dioxide",
        "lead",
        "air temperature",
        "relative humidity",
        "occupancy",
        "mechanical ventilation rate",
        "biocontaminants"
    ]

    geoService = GeoService()

    for i in range(0, 3):
        study = Study(identifier=f"seed-{uuid.uuid4()}",
                      name=fake.word(),
                      description=fake.paragraph(nb_sentences=4),
                      website=fake.url(),
                      start_year=random.randint(2000, 2010),
                      end_year=random.randint(2010, 2020),
                      duration=random.randint(1, 24),
                      occupant_impact=fake.word(
                          ext_word_list=occupant_impacts),
                      other_indoor_param=fake.word(
                          ext_word_list=other_indoor_params),
                      funding=fake.company(),
                      ethics=fake.paragraph(),
                      license=fake.word(ext_word_list=licenses),
                      )

        session.add(study)
        await session.commit()
        await session.refresh(study)

        # study contact
        contact = Person(name=fake.name(),
                         email=fake.email(),
                         email_public=fake.boolean(),
                         institution=fake.company(),
                         study_id=study.id)

        session.add(contact)
        await session.commit()
        await session.refresh(contact)

        # study instruments
        for j in range(0, 3):
            instrument = Instrument(identifier=f"seed-{j}",
                                    manufacturer=fake.company(),
                                    model=fake.word(),
                                    equipment_grade_rating=fake.word(
                                        ext_word_list=["reference instrument", "low-cost sensor", "other", "unknown"]),
                                    placement=fake.word(ext_word_list=[
                                                        "ceiling", "lateral wall", "air return", "desk", "other", "mixed", "unknown"]),
                                    study_id=study.id)
            session.add(instrument)
            await session.commit()
            await session.refresh(instrument)

            for k in range(0, random.randint(1, 5)):
                parameter = InstrumentParameter(
                    physical_parameter=fake.word(
                        ext_word_list=physical_params),
                    analysis_method="unknown",
                    measurement_uncertainty=None,
                    study_id=study.id,
                    instrument_id=instrument.id)
                session.add(parameter)
                await session.commit()
                await session.refresh(parameter)

        # study buildings
        for j in range(0, 3):
            place = fake.location_on_land()
            zone = geoService.readClimateZone(place[1], place[0], False)
            elevation = geoService.queryElevation(place[1], place[0])

            renovation = fake.word(ext_word_list=yes_no)
            renovation_year = (study.start_year +
                               9) if renovation == "yes" else None

            special_population = fake.word(
                ext_word_list=special_populations)

            building = Building(identifier=f"seed-{j}",
                                city=place[2],
                                country=place[3],
                                timezone=place[4],
                                altitude=elevation.altitude,
                                climate_zone=zone.name,
                                long=float(place[1]),
                                lat=float(place[0]),
                                type=fake.word(ext_word_list=building_types),
                                special_population=special_population,
                                outdoor_env=fake.word(
                                    ext_word_list=outdoor_envs),
                                construction_year=(study.start_year - 1),
                                renovation=renovation,
                                renovation_year=renovation_year,
                                mechanical_ventilation=fake.word(
                                    ext_word_list=yes_no),
                                operable_windows=fake.word(
                                    ext_word_list=yes_no),
                                smoking=fake.word(ext_word_list=yes_no),
                                study_id=study.id)
            session.add(building)
            await session.commit()
            await session.refresh(building)

            # study building spaces
            for k in range(0, 10):
                combustion_sources = fake.word(ext_word_list=yes_no)
                major_combustion_sources = fake.word(
                    ext_word_list=major_combustion_sources) if combustion_sources == "yes" else None
                minor_combustion_sources = fake.word(
                    ext_word_list=minor_combustion_sources) if combustion_sources == "yes" else None

                space = Space(identifier=f"seed-{j}-{k}",
                              type=fake.word(ext_word_list=space_types),
                              occupancy=fake.word(
                                  ext_word_list=occupancy_status),
                              mechanical_ventilation_type=fake.word(
                                  ext_word_list=ventilation_types),
                              mechanical_ventilation_status=fake.word(
                                  ext_word_list=on_off),
                              windows_status=fake.word(ext_word_list=windows),
                              ventilation_rate=random.uniform(0.1, 1.0),
                              air_change_rate=random.uniform(0.1, 1.0),
                              particle_filtration_rating=random.randint(1, 5),
                              cooling_type=fake.word(
                                  ext_word_list=cooling_types),
                              cooling_status=fake.word(ext_word_list=on_off),
                              heating_type=fake.word(
                                  ext_word_list=heating_types),
                              heating_status=fake.word(ext_word_list=on_off),
                              air_filtration=fake.word(ext_word_list=yes_no),
                              printers=fake.word(ext_word_list=yes_no),
                              carpets=fake.word(ext_word_list=yes_no),
                              combustion_sources=combustion_sources,
                              major_combustion_sources=major_combustion_sources,
                              minor_combustion_sources=minor_combustion_sources,
                              pets=fake.word(ext_word_list=yes_no),
                              dampness=fake.word(ext_word_list=yes_no),
                              mold=fake.word(ext_word_list=yes_no),
                              detergents=fake.word(ext_word_list=yes_no),
                              study_id=study.id,
                              building_id=building.id)
                session.add(space)
                await session.commit()
                await session.refresh(space)

    return SeedStatus(status="OK")
