"""Download of the raw measurements matching an Explore selection: a
request row per job, built in the background, delivered by email."""

import re
from datetime import date, datetime
from typing import Dict, Optional

from enacit4r_sql.models.query import ListResult
from pydantic import BaseModel, ConfigDict
from pydantic import Field as PydanticField
from pydantic import field_validator
from sqlalchemy import TIMESTAMP, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel

# control characters (newlines included) would break the email headers
CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class DownloadRequest(SQLModel, table=True):
    __tablename__ = "download_request"

    id: Optional[int] = Field(default=None, primary_key=True)
    # sha256 of the emailed token, set when the link is sent
    token_hash: Optional[str] = Field(default=None, index=True, unique=True)
    email: str = Field(index=True)
    title: str
    description: str
    # {filter, parameters, from, to}, see DownloadSelection
    query: Dict = Field(sa_column=Column(JSONB, nullable=False))
    # pending | running | ready | failed | expired
    status: str = Field(default="pending", index=True)
    error: Optional[str] = Field(default=None)
    attempts: int = Field(default=0)
    # estimate at request time, then the exported row count
    n_records: int = Field(sa_column=Column(BigInteger, nullable=False))
    size: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    s3_key: Optional[str] = Field(default=None)
    client_ip: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(sa_column=Column(TIMESTAMP(timezone=True)))
    ready_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP(timezone=True))
    )
    notified_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP(timezone=True))
    )
    expires_at: Optional[datetime] = Field(
        default=None, sa_column=Column(TIMESTAMP(timezone=True))
    )


class DownloadSelection(BaseModel):
    """The Explore selection: same filter dialect as `/stats/*`."""

    model_config = ConfigDict(populate_by_name=True)

    filter: Optional[str] = None
    parameters: list[str] = []
    # sqlmodel's Field drops the alias on a plain pydantic model
    from_: Optional[date] = PydanticField(default=None, alias="from")
    to: Optional[date] = None


class DownloadForm(DownloadSelection):
    email: str = PydanticField(max_length=320)
    title: str = PydanticField(min_length=1, max_length=200)
    description: str = PydanticField(min_length=1, max_length=2000)

    @field_validator("email")
    @classmethod
    def check_email(cls, value: str) -> str:
        value = value.strip()
        local, _, domain = value.rpartition("@")
        if not local or "." not in domain or " " in value or CONTROL.search(value):
            raise ValueError("not an email address")
        return value

    @field_validator("title", "description")
    @classmethod
    def strip(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()

    @field_validator("title")
    @classmethod
    def single_line(cls, value: str) -> str:
        if CONTROL.search(value):
            raise ValueError("must be a single line")
        return value


class DownloadEstimate(BaseModel):
    # upper bound: building and space criteria are not counted
    n_records: int
    n_datasets: int
    # studies matching the selection left out because of their data embargo
    n_embargoed_studies: int
    max_records: int


class DownloadAccepted(BaseModel):
    id: int
    status: str
    n_records: int


class DownloadRequestRead(BaseModel):
    """A request as admins see it: everything but the token hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    title: str
    description: str
    query: Dict
    status: str
    error: Optional[str]
    attempts: int
    n_records: int
    size: Optional[int]
    client_ip: Optional[str]
    created_at: datetime
    ready_at: Optional[datetime]
    notified_at: Optional[datetime]
    expires_at: Optional[datetime]


class DownloadRequestsResult(ListResult):
    data: list[DownloadRequestRead]
