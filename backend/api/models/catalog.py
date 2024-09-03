from typing import List, Literal, Optional
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from pydantic import BaseModel


class PersonBase(SQLModel):
    name: str
    email: str
    institution: str
    study_id: Optional[int] = Field(
        default=None, foreign_key="study.id", ondelete="CASCADE")


class Person(PersonBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    id: Optional[int] = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    # relationships
    study: Optional["Study"] = Relationship(back_populates="contact")


class StudyBase(SQLModel):
    identifier: str
    name: str
    description: str
    website: Optional[str] = Field(default=None)
    building_count: Optional[int] = Field(default=None)
    space_count: Optional[int] = Field(default=None)
    start_year: Optional[int] = Field(default=None)
    end_year: Optional[int] = Field(default=None)
    duration: Optional[int] = Field(default=None)
    occupant_impact: Optional[str] = Field(default=None)
    other_indoor_param: Optional[str] = Field(default=None)
    cite: Optional[str] = Field(default=None)
    doi: Optional[str] = Field(default=None)
    funding: Optional[str] = Field(default=None)
    ethics: Optional[str] = Field(default=None)
    license: Optional[str] = Field(default=None)


class Study(StudyBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    id: Optional[int] = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    # relationships
    contact: Person = Relationship(
        back_populates="study", cascade_delete=True)
    buildings: List["Building"] = Relationship(
        back_populates="study", cascade_delete=True)


class StudyRead(StudyBase):
    id: int
    contact: Person
    buildings: List["Building"] = []


class CertificationBase(SQLModel):
    program: str
    level: str
    building_id: Optional[int] = Field(
        default=None, foreign_key="building.id", ondelete="CASCADE")


class Certification(CertificationBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    id: int = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    # relationships
    building: Optional["Building"] = Relationship(
        back_populates="certifications")


class BuildingBase(SQLModel):
    identifier: str
    country: str
    city: str
    postcode: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    timezone: str
    altitude: int
    climate_zone: str
    long: float
    lat: float
    type: Optional[str] = Field(default=None)
    special_population: Optional[str] = Field(default=None)
    outdoor_env: Optional[str] = Field(default=None)
    construction_year: Optional[int] = Field(default=None)
    renovation: str
    renovation_year: Optional[int] = Field(default=None)
    special_population_designation: str
    special_population: Optional[str] = Field(default=None)
    smoking: str
    study_id: Optional[int] = Field(
        default=None, foreign_key="study.id", ondelete="CASCADE")


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
        back_populates="building", cascade_delete=True)
    study: Optional["Study"] = Relationship(
        back_populates="buildings")
    spaces: List["Space"] = Relationship(
        back_populates="building", cascade_delete=True)


class BuildingRead(BuildingBase):
    id: int
    certifications: List[Certification] = []
    spaces: List["Space"] = []


class SpaceBase(SQLModel):
    identifier: str
    type: str
    occupancy: Optional[str] = Field(default=None)
    ventilation: Optional[str] = Field(default=None)
    ventilation_rate: Optional[float] = Field(default=None)
    air_change_rate: Optional[float] = Field(default=None)
    particle_filtration_rating: Optional[int] = Field(default=None)
    cooling: Optional[str] = Field(default=None)
    heating: Optional[str] = Field(default=None)
    air_filtration: Optional[str] = Field(default=None)
    printers: Optional[str] = Field(default=None)
    carpets: Optional[str] = Field(default=None)
    combustion_sources: Optional[str] = Field(default=None)
    major_combustion_sources: Optional[str] = Field(default=None)
    minor_combustion_sources: Optional[str] = Field(default=None)
    pets: Optional[str] = Field(default=None)
    dampness: Optional[str] = Field(default=None)
    mold: Optional[str] = Field(default=None)
    detergents: Optional[str] = Field(default=None)

    study_id: Optional[int] = Field(
        default=None, foreign_key="study.id", ondelete="CASCADE")
    building_id: Optional[int] = Field(
        default=None, foreign_key="building.id", ondelete="CASCADE")


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
