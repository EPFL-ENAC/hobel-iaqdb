from typing import List, Literal, Optional
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from pydantic import BaseModel


class StudyPerson(SQLModel, table=True):
    person_id: Optional[int] = Field(
        default=None, foreign_key="person.id", primary_key=True)
    study_id: Optional[int] = Field(
        default=None, foreign_key="study.id", primary_key=True)


class Person(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    id: Optional[int] = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    name: str
    email: str
    institution: str
    # relationships
    studies: List["Study"] = Relationship(
        back_populates="contacts", link_model=StudyPerson)


class StudyBase(SQLModel):
    identifier: str
    name: str
    description: str
    building_count: Optional[int] = Field(default=None)
    space_count: Optional[int] = Field(default=None)
    start_year: Optional[int] = Field(default=None)
    end_year: Optional[int] = Field(default=None)


class Study(StudyBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    id: Optional[int] = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    # relationships
    contacts: List[Person] = Relationship(
        back_populates="studies", link_model=StudyPerson)
    buildings: List["Building"] = Relationship(back_populates="study")


class StudyRead(StudyBase):
    id: int
    contacts: List[Person] = []
    buildings: List["Building"] = []


class Certification(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    id: int = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    program: str
    level: str
    building_id: Optional[int] = Field(default=None, foreign_key="building.id")
    # relationships
    building: Optional["Building"] = Relationship(
        back_populates="certifications")


class BuildingBase(SQLModel):
    country: str
    city: str
    timezone: str
    altitude: int
    climate_zone: str
    long: float
    lat: float
    type: Optional[str] = Field(default=None)                # ex: school
    special_population: Optional[str] = Field(default=None)  # ex: children
    outdoor_env: Optional[str] = Field(default=None)
    construction_year: Optional[int] = Field(default=None)
    renovation_year: Optional[int] = Field(default=None)
    study_id: Optional[int] = Field(default=None, foreign_key="study.id")


class Building(BuildingBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    id: int = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    # relationships
    certifications: List[Certification] = Relationship(
        back_populates="building")
    study: Optional["Study"] = Relationship(back_populates="buildings")
    spaces: List["Space"] = Relationship(back_populates="building")


class BuildingRead(BuildingBase):
    id: int
    certifications: List[Certification] = []
    spaces: List["Space"] = []


class SpaceBase(SQLModel):
    space: str
    ventilation: str
    smoking: str
    study_id: Optional[int] = Field(default=None, foreign_key="study.id")
    building_id: Optional[int] = Field(default=None, foreign_key="building.id")


class Space(SpaceBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    id: int = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    # relationships
    building: Optional[Building] = Relationship(back_populates="spaces")


class ListResult(BaseModel):
    total: int
    skip: int | None
    limit: int | None


class StudiesResult(ListResult):
    data: List[StudyRead]


class BuildingsResult(ListResult):
    data: List[BuildingRead]


class SpacesResult(ListResult):
    data: List[Space]
