from pydantic import BaseModel
from models.mixins import TimestampMixin
from config.db import Base
from fastapi_utils.guid_type import GUID, GUID_SERVER_DEFAULT_POSTGRESQL
from sqlalchemy import Column, ForeignKey, String


class userResponse(BaseModel):
    id: str
    name: str
    dni: str
    email: str
    phone: str
    role: str
    statu: str


class authUser(BaseModel):
    username: str
    password: str


class AuthReset(BaseModel):
    username: str
    password: str


class LoginRecord(TimestampMixin, Base):
    __tablename__ = "login_records"

    id = Column(GUID, primary_key=True, server_default=GUID_SERVER_DEFAULT_POSTGRESQL)
    user_id = Column(GUID, ForeignKey("users.id"))
    location = Column(String)
    ip_address = Column(String)
    browser_info = Column(String)

class LoginRecordCreate(BaseModel):
    user_id: str
    location: str
    ip_address: str
    browser_info: str
