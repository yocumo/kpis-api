from datetime import time
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Enum,
    Time,
)
from config.db import Base
from models.mixins import TimestampMixin
from fastapi_utils.guid_type import GUID, GUID_SERVER_DEFAULT_POSTGRESQL
from sqlalchemy.orm import relationship


class ExceptionActivity(TimestampMixin, Base):
    __tablename__ = "exceptions_activity"

    id = Column(GUID, primary_key=True, server_default=GUID_SERVER_DEFAULT_POSTGRESQL)

    activity = Column(String)
    minut = Column(Time)


class ExcepActivityCreate(BaseModel):
    activity: str
    minut: time


# -----------------------------------------------------------------------------

class ExceptionCategory(TimestampMixin, Base):
    __tablename__ = "exceptions_category"

    id = Column(GUID, primary_key=True, server_default=GUID_SERVER_DEFAULT_POSTGRESQL)

    category_type = Column(String)
    hourr = Column(Time)


class ExcepCategoryCreate(BaseModel):
    category_type: str
    hourr: time
    
    
    
    
# -----------------------------------------------------------------------------
class ExceptionCavid(TimestampMixin, Base):
    __tablename__ = "exceptions_cavid"

    id = Column(GUID, primary_key=True, server_default=GUID_SERVER_DEFAULT_POSTGRESQL)

    cavid = Column(String)
    attributable_customer = Column(String)


class ExcepCavidCreate(BaseModel):
    cavid: str
    attributable_customer: str