from typing import List, Dict, Optional
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint, Column, JSON
from pydantic import BaseModel


# Studies

class PersonBase(SQLModel):
    name: str
    email: str
    email_public: bool = Field(default=False)
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
    study: Optional["Study"] = Relationship(back_populates="contributors")


class StudyBase(SQLModel):
    identifier: str
    name: str
    description: str
    website: Optional[str] = Field(default=None)
    start_year: Optional[int] = Field(default=None)
    end_year: Optional[int] = Field(default=None)
    duration: Optional[int] = Field(default=None)
    occupant_impact: Optional[str] = Field(default=None)
    other_indoor_param: Optional[str] = Field(default=None)
    citation: Optional[str] = Field(default=None)
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
    buildings: List["Building"] = Relationship(
        back_populates="study", cascade_delete=True)
    instruments: List["Instrument"] = Relationship(
        back_populates="study", cascade_delete=True)
    datasets: List["Dataset"] = Relationship(
        back_populates="study", cascade_delete=True)
    contributors: List["Person"] = Relationship(
        back_populates="study", cascade_delete=True)


class StudyRead(StudyBase):
    id: int
    contributors: List["Person"] = []
    buildings: List["Building"] = []
    instruments: List["Instrument"] = []


class StudyDraft(StudyRead):
    id: Optional[int] = Field(default=None)
    buildings: List["BuildingDraft"] = []
    instruments: List["InstrumentDraft"] = []
    datasets: List["DatasetDraft"] = []


# Buildings

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
    timezone: str
    altitude: int
    climate_zone: str
    long: float
    lat: float
    type: Optional[str] = Field(default=None)
    other_type: Optional[str] = Field(default=None)
    special_population: Optional[str] = Field(default=None)
    outdoor_env: Optional[str] = Field(default=None)
    other_outdoor_env: Optional[str] = Field(default=None)
    green_certified: Optional[str] = Field(default=None)
    construction_year: Optional[int] = Field(default=None)
    renovation: str
    renovation_year: Optional[int] = Field(default=None)
    mechanical_ventilation: str
    particle_filtration_rating: Optional[int] = Field(default=None)
    operable_windows: str
    special_population: Optional[str] = Field(default=None)
    other_special_population: Optional[str] = Field(default=None)
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


class BuildingDraft(BuildingRead):
    id: Optional[int] = Field(default=None)
    country: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None)
    timezone: Optional[str] = Field(default=None)
    altitude: Optional[int] = Field(default=None)
    climate_zone: Optional[str] = Field(default=None)
    long: Optional[float] = Field(default=None)
    lat: Optional[float] = Field(default=None)
    type: Optional[str] = Field(default=None)
    other_type: Optional[str] = Field(default=None)
    renovation: Optional[str] = Field(default=None)
    mechanical_ventilation: Optional[str] = Field(default=None)
    operable_windows: Optional[str] = Field(default=None)
    smoking: Optional[str] = Field(default=None)


# Spaces


class SpaceBase(SQLModel):
    identifier: str
    type: str
    occupancy: Optional[str] = Field(default=None)
    mechanical_ventilation_status: str
    mechanical_ventilation_type: Optional[str] = Field(default=None)
    windows_status: str
    ventilation_rate: Optional[float] = Field(default=None)
    air_change_rate: Optional[float] = Field(default=None)
    cooling_status: str
    cooling_type: Optional[str] = Field(default=None)
    other_cooling_type: Optional[str] = Field(default=None)
    heating_status: str
    heating_type: Optional[str] = Field(default=None)
    other_heating_type: Optional[str] = Field(default=None)
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

# Instruments


class InstrumentParameterBase(SQLModel):
    physical_parameter: str
    analysis_method: Optional[str] = Field(default=None)
    measurement_uncertainty: Optional[str] = Field(default=None)
    note: Optional[str] = Field(default=None)

    instrument_id: Optional[int] = Field(
        default=None, foreign_key="instrument.id", ondelete="CASCADE")


class InstrumentParameter(InstrumentParameterBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    id: int = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    # relationships
    instrument: Optional["Instrument"] = Relationship(
        back_populates="parameters")


class InstrumentBase(SQLModel):
    identifier: str
    manufacturer: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)
    equipment_grade_rating: Optional[str] = Field(default=None)
    placement: Optional[str] = Field(default=None)

    study_id: Optional[int] = Field(
        default=None, foreign_key="study.id", ondelete="CASCADE")


class Instrument(InstrumentBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    id: int = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    # relationships
    study: Optional["Study"] = Relationship(
        back_populates="instruments")
    parameters: List[InstrumentParameter] = Relationship(
        back_populates="instrument", cascade_delete=True)


class InstrumentRead(InstrumentBase):
    id: int
    parameters: List[InstrumentParameter] = []


class InstrumentDraft(InstrumentRead):
    id: Optional[int] = Field(default=None)

# Datasets


class DatasetBase(SQLModel):
    name: str
    description: str
    folder: Dict | None = Field(sa_column=Column(
        JSON), default=None)  # file store node object
    study_id: Optional[int] = Field(
        default=None, foreign_key="study.id", ondelete="CASCADE")


class Dataset(DatasetBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    id: int = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    # relationships
    study: Optional[Study] = Relationship(
        back_populates="datasets")
    variables: List["Variable"] = Relationship(
        back_populates="dataset", cascade_delete=True)


class VariableBase(SQLModel):
    name: str
    type: str
    unit: Optional[str] = Field(default=None)
    format: Optional[str] = Field(default=None)
    # ref in the taxonomy of variables
    reference: Optional[str] = Field(default=None)

    study_id: Optional[int] = Field(
        default=None, foreign_key="study.id", ondelete="CASCADE")
    dataset_id: Optional[int] = Field(
        default=None, foreign_key="dataset.id", ondelete="CASCADE")


class Variable(VariableBase, table=True):
    __table_args__ = (UniqueConstraint("id"),)
    id: int = Field(
        default=None,
        nullable=False,
        primary_key=True,
        index=True,
    )
    # relationships
    dataset: Optional[Dataset] = Relationship(back_populates="variables")


class DatasetRead(DatasetBase):
    id: int
    variables: List[Variable] = []


class DatasetDraft(DatasetRead):
    id: Optional[int] = Field(default=None)

#
# Results
#


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


class InstrumentsResult(ListResult):
    data: List[InstrumentRead]


class DatasetsResult(ListResult):
    data: List[DatasetRead]


class StudyDraftsResult(ListResult):
    data: List[StudyDraft]
