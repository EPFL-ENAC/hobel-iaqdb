from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient


async def init_models(client: AsyncIOMotorClient):
    await init_beanie(
        database=client.get_default_database(),
        document_models=[
            "api.models.study.Study",
            "api.models.study.Building",
            "api.models.study.Room",
        ],
    )
