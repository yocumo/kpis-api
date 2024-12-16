from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Enum
from config.db import Base
from enums.user_enum import RoleEnum, StatuEnum
from models.mixins import TimestampMixin
from fastapi_utils.guid_type import GUID, GUID_SERVER_DEFAULT_POSTGRESQL


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, server_default=GUID_SERVER_DEFAULT_POSTGRESQL)
    name = Column(String)
    dni = Column(String, unique=True)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String(15), nullable=True)
    role = Column(Enum(RoleEnum), default=RoleEnum.guest, nullable=False)
    statu = Column(Enum(StatuEnum), default=StatuEnum.inactive, nullable=False)
    password = Column(String)


class UserCreate(BaseModel):
    dni: str = Field(None, description="Unique identifier")
    name: str
    email: str
    phone: str
    role: RoleEnum = Field(default=RoleEnum.admin)
    statu: StatuEnum = Field(default=StatuEnum.active)
    password: str


class UserUpdate(BaseModel):
    dni: str
    name: str
    email: str
    phone: str
    role: RoleEnum
    statu: StatuEnum


class UserResponse(BaseModel):
    id: UUID
    name: str
    dni: str
    email: Optional[str] = None
    phone: Optional[str] = None 
    role: RoleEnum
    statu: StatuEnum

    class Config:
        from_attributes = True


class UsersApiResponse(BaseModel):
    code: int
    data: List[UserResponse]


class UserlistSchema(BaseModel):
    name: str
    dni: str
    project: Optional[str] = None

    class Config:
        from_attributes = True


class UserImport(BaseModel):
    supervisors: List[UserlistSchema]
