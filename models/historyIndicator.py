from typing import List, Optional, Dict, Union
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy import Column, Float, Integer, String
from config.db import Base
from enums.user_enum import ServiceTypeEnum

from models.mixins import TimestampMixin
from fastapi_utils.guid_type import GUID, GUID_SERVER_DEFAULT_POSTGRESQL



class HistoryIndicator(TimestampMixin, Base):
    __tablename__ = "history_indicators"

    id = Column(GUID, primary_key=True, server_default=GUID_SERVER_DEFAULT_POSTGRESQL)

    etl = Column(Float, nullable=True)
    etr = Column(Float, nullable=True)
    etci = Column(Float, nullable=True)
    ts = Column(Float, nullable=True)
    es = Column(Float, nullable=True)
    vr = Column(Float, nullable=True)
    esi = Column(Float, nullable=True)
    efo = Column(Float, nullable=True)
    cd = Column(Float, nullable=True)
    month = Column(Integer, nullable=True)
    year = Column(String, nullable=True)
    total = Column(Float, nullable=True)
    typei = Column(String, nullable=True)
    service_type_name = Column(String, nullable=True)


class KPICalculationRequest(BaseModel):
    service_type: str
    month: int
    data: Optional[List[Dict[str, Union[float, str]]]]

    class Config:
        extra = "ignore"
        from_attributes = True


class KPICalculationResult(BaseModel):
    service_type: ServiceTypeEnum
    month: int
    input_data: List[Dict[str, Union[float, str]]]
    calculated_rows: List[Dict[str, Union[float, str]]]
    total: float


class OperationalCategoryCreate(BaseModel):

    category_type: str


class RequestSearchHistory(BaseModel):
    month: int
    serviceType: str