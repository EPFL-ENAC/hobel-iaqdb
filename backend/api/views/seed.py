import uuid
import random
from fastapi import APIRouter
from pydantic import BaseModel
from api.models.study import Study, Building, Room
from beanie import WriteRules

router = APIRouter()


class SeedStatus(BaseModel):
    """Response model to validate and return when performing a health check."""
    status: str = "OK"


@router.put("")
async def seed() -> SeedStatus:
    words = ["apple", "banana", "cherry", "date",
             "elderberry", "fig", "grape", "honeydew"]
    lorem = [
        "Blanditiis voluptatem nisi reprehenderit doloribus ullam accusantium. Debitis voluptates ut aliquid. Illum dignissimos fugiat culpa similique ipsum. Et et qui est sequi laudantium. Iste sapiente deserunt asperiores rerum. Eos ratione ratione ad quia et.",
        "Praesentium maiores modi ex fuga laborum vero. Earum expedita illo placeat alias cumque. Modi vitae praesentium qui velit et non sed.",
        "Fuga et ad corporis enim esse aliquid nihil facere. Eos voluptatibus nihil nihil. Incidunt consectetur quaerat quis voluptatem praesentium voluptas libero nulla. Vel est earum nisi ipsum. Molestiae omnis reiciendis voluptas perspiciatis dolor consectetur. Quod nostrum in adipisci.",
        "Quidem dolor dolor deserunt temporibus. Error est quis vitae modi magni. Sed quae quaerat accusamus inventore.",
        "Sed omnis sequi qui recusandae quod iusto aut. Nesciunt mollitia voluptatem rerum error qui temporibus ut. Enim tempore ratione est. Officiis maiores quis reprehenderit quae. In quidem non maiores."
    ]
    climate_zones = [
        "Af ",
        "Am ",
        "Aw ",
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
        "ET ",
        "EF ",
    ]

    bbox = [
        # swiss
        lambda: [random.uniform(5, 10), random.uniform(45, 48)],
        # europe
        lambda: [random.uniform(-10, 45), random.uniform(35, 60)],
        # north america
        lambda: [random.uniform(-120, -70), random.uniform(20, 50)],
        # china
        lambda: [random.uniform(100, 140), random.uniform(10, 40)],
        # india
        lambda: [random.uniform(70, 85), random.uniform(10, 30)],
        # australia
        lambda: [random.uniform(145, 155), random.uniform(-35, -25)],
    ]

    for i in range(1, 100):
        study = Study(slug=f"seed-{uuid.uuid4()}", name=random.choice(words),
                      description=lorem[random.randint(0, 4)])
        study = await Study.insert_one(study)

        for j in range(1, 10):
            building = Building(slug=f"seed-{uuid.uuid4()}", country="CH",
                                city="Lausanne", altitude=random.randint(0, 2500), climate_zone=climate_zones[random.randint(0, 29)],
                                location=bbox[random.randint(0, 5)](),
                                study=study)
            building = await Building.insert_one(building)

            for k in range(1, 10):
                room = Room(slug=f"seed-{uuid.uuid4()}",
                            space="outdoor", ventilation="NA", smoking="yes",
                            study=study,
                            building=building)
                room = await Room.insert_one(room)

    return SeedStatus(status="OK")
