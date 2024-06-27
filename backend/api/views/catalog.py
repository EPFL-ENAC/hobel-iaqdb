from typing import List
from fastapi import APIRouter
from api.models.study import Study, Building, Room
from beanie import PydanticObjectId

router = APIRouter()


@router.get("/studies")
async def getStudies() -> List[Study]:
    return await Study.find_all().to_list()
    # return await Study.find_all(fetch_links=True, nesting_depth=2).to_list()


@router.get("/study/{id}")
async def getStudy(id: PydanticObjectId) -> Study:
    return await Study.get(id)


@router.get("/study/{id}/buildings")
async def getStudyBuildings(id: PydanticObjectId) -> List[Building]:
    return await Building.find(Building.study.id == id).to_list()


@router.get("/study/{id}/rooms")
async def getStudyBuildings(id: PydanticObjectId) -> List[Room]:
    return await Room.find(Room.study.id == id, fetch_links=True, nesting_depth=1).to_list()


@router.get("/buildings")
async def getBuildings() -> List[Building]:
    return await Building.find_all(fetch_links=True, nesting_depth=1).to_list()
    # For back links resolution:
    # return await Building.find_all(fetch_links=True, nesting_depth=1).to_list()


@router.get("/rooms")
async def getRooms() -> List[Room]:
    return await Room.find_all(fetch_links=False, nesting_depth=1).to_list()
