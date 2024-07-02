from typing import List
from fastapi import APIRouter, Query
from api.models.catalog import Study, Building, StudiesResult, BuildingStudy, BuildingsResult, Room, RoomsResult
from beanie import PydanticObjectId
from beanie.odm.operators.find.logical import And
from beanie.odm.operators.find.comparison import In

router = APIRouter()


@router.get("/studies")
async def getStudies(skip: int = Query(0), limit: int = Query(100), altmin: int = Query(None), altmax: int = Query(None), climates: List[str] = Query(None)) -> StudiesResult:
    studyIds = []
    buildingQuery = makeBuildingQuery(altmin, altmax, climates)
    if not buildingQuery is None:
        buildingDigests = await Building.find(buildingQuery).project(BuildingStudy).to_list()
        # unique study ids
        studyIds = set([digest.study.ref.id for digest in buildingDigests])
        # no building for the criteria then no study
        if len(studyIds) == 0:
            return StudiesResult(total=0, skip=skip, limit=limit, data=[])
    # use the list of study ids if any
    query = {"_id": {"$in": studyIds}} if len(studyIds) > 0 else {}
    count = await Study.find(query).count()
    data = await Study.find(query).skip(skip).limit(limit).to_list()
    return StudiesResult(total=count, skip=skip, limit=limit, data=data)


@router.get("/study/){id}")
async def getStudy(id: PydanticObjectId) -> Study:
    return await Study.get(id)


@router.get("/study/{id}/buildings")
async def getStudyBuildings(id: PydanticObjectId) -> List[Building]:
    return await Building.find(Building.study.id == id).to_list()


@router.get("/study/{id}/rooms")
async def getStudyBuildings(id: PydanticObjectId) -> List[Room]:
    return await Room.find(Room.study.id == id, fetch_links=True, nesting_depth=1).to_list()


@router.get("/buildings")
async def getBuildings(skip: int = Query(0), limit: int = Query(100), altmin: int = Query(None), altmax: int = Query(None), climates: List[str] = Query(None)) -> BuildingsResult:
    query = makeBuildingQuery(altmin, altmax, climates)
    if query is None:
        query = {}
    count = await Building.find(query).count()
    data = await Building.find(query, fetch_links=True, nesting_depth=1).skip(skip).limit(limit).to_list()
    # For back links resolution:
    # return await Building.find_all(fetch_links=True, nesting_depth=1).to_list()
    return BuildingsResult(total=count, skip=skip, limit=limit, data=data)


@router.get("/rooms")
async def getRooms(skip: int = Query(0), limit: int = Query(100)) -> RoomsResult:
    query = {}
    count = await Room.find(query).count()
    data = await Room.find(query, fetch_links=False, nesting_depth=1).skip(skip).limit(limit).to_list()
    return RoomsResult(total=count, skip=skip, limit=limit, data=data)


def makeBuildingQuery(altmin: int | None, altmax: int | None, climates: List[str] | None):
    criteria = []
    if not altmin is None:
        criteria.append(Building.altitude >= altmin)
    if not altmax is None:
        criteria.append(Building.altitude <= altmax)
    if climates:
        criteria.append(In(Building.climate_zone, climates))
    query = And(*criteria) if len(criteria) > 0 else None
    return query
