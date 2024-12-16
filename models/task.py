from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from config.db import Base
from models.mixins import TimestampMixin
from fastapi_utils.guid_type import GUID, GUID_SERVER_DEFAULT_POSTGRESQL
from sqlalchemy.orm import relationship

from datetime import datetime, time


# ----------------------------- TODO:: TAREAS -----------------------------
class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    id = Column(GUID, primary_key=True, server_default=GUID_SERVER_DEFAULT_POSTGRESQL)

    documenter = Column(String, nullable=True)
    code = Column(String, unique=True)
    client = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    address = Column(String, nullable=True)
    cav_id = Column(String, nullable=True)
    operational_category = Column(String, nullable=True)
    request_activity = Column(String, nullable=True)
    assigned_staff = Column(String, nullable=True)
    status = Column(String, nullable=True)

    date_delivery_time = Column(DateTime, nullable=True)
    assigned_time = Column(DateTime, nullable=True)
    scheduled_time = Column(DateTime, nullable=True)
    way_time = Column(DateTime, nullable=True)
    arrival_time = Column(DateTime, nullable=True)
    final_time = Column(DateTime, nullable=True)
    confirmation_time = Column(DateTime, nullable=True)
    arrival_dead_time = Column(Time, nullable=True)

    execution_dead_time = Column(Time, nullable=True)
    observation_dead_time = Column(Text, nullable=True, default="")
    service_type = Column(String, nullable=True)
    staff_dni = Column(String, nullable=True)

    root_cause = Column(String, nullable=True, default="")
    attributable = Column(String, nullable=True, default="")
    resolutioncategory_2ps = Column(String, nullable=True, default="")
    customer_waiting = Column(Time, nullable=True)


class TaskCreate(BaseModel):
    documenter: Optional[str] = None
    code: Optional[str] = None
    client: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    cav_id: Optional[str] = None
    operational_category: Optional[str] = None
    request_activity: Optional[str] = None
    assigned_staff: Optional[str] = None
    status: Optional[str] = None
    date_delivery_time: Optional[datetime] = None
    assigned_time: Optional[datetime] = None
    scheduled_time: Optional[datetime] = None
    way_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    final_time: Optional[datetime] = None
    confirmation_time: Optional[datetime] = None
    arrival_dead_time: Optional[time] = None
    execution_dead_time: Optional[time] = None
    observation_dead_time: Optional[str] = None
    root_cause: Optional[str] = None
    attributable: Optional[str] = None
    resolutioncategory_2ps: Optional[str] = None
    customer_waiting: Optional[time] = None
    service_type: Optional[str] = None
    staff_dni: Optional[str] = None


class TaskListSchemaCreate(BaseModel):
    documenter: Optional[str] = None
    code: Optional[str] = None
    client: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    cav_id: Optional[str] = None
    operational_category: Optional[str] = None
    request_activity: Optional[str] = None
    assigned_staff: Optional[str] = None
    status: Optional[str] = None
    date_delivery_time: Optional[datetime] = None
    assigned_time: Optional[datetime] = None
    scheduled_time: Optional[datetime] = None
    way_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    final_time: Optional[datetime] = None
    confirmation_time: Optional[datetime] = None
    arrival_dead_time: Optional[time] = None
    execution_dead_time: Optional[time] = None
    observation_dead_time: Optional[str] = None
    root_cause: Optional[str] = None
    attributable: Optional[str] = None
    resolutioncategory_2ps: Optional[str] = None
    customer_waiting: Optional[time] = None
    service_type: Optional[str] = None
    staff_dni: Optional[str] = None
    

    class Config:
        from_attributes = True


class TaskImport(BaseModel):
    admin_id: str
    tasks: List[TaskListSchemaCreate]


class TaskUpdateSchema(TaskListSchemaCreate):
    pass


# ----------------------------- TODO: LOGISTICA TIME :-----------------------------


# ----------------------------- TODO:: COLUMNAS CALCULADAS -----------------------------
class Estimated(TimestampMixin, Base):
    __tablename__ = "estimateds"

    id = Column(
        GUID,
        primary_key=True,
        server_default=GUID_SERVER_DEFAULT_POSTGRESQL,
        unique=True,
    )

    task_id = Column(GUID, ForeignKey("tasks.id"), unique=True)
    expected_current_date_time = Column(String, nullable=True)
    compliance_etl_etr = Column(String, nullable=True)
    confirmation_waiting_time = Column(Time, nullable=True)
    total_time = Column(Time, nullable=True)
    ts = Column(String, nullable=True)
    vr_date = Column(DateTime)
    catv_test = Column(Integer)
    vr_staff = Column(String)
    esi_date = Column(DateTime)
    esi_catv_test = Column(String)
    esi_staff = Column(String)
    root_cause_ant = Column(String)
    vr = Column(String)
    esi = Column(String)
    days_recurrence = Column(Integer)
    monthh = Column(Integer)
    dayy = Column(Integer)
    day_week = Column(Integer)
    time_int = Column(Float)
    dead_time = Column(Float)
    one_fifty = Column(Float, nullable=True)

    task = relationship("Task", backref="estimated", foreign_keys=[task_id])
