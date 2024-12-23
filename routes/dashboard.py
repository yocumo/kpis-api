from ast import parse
from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status
import pandas as pd
from requests import Session
from sqlalchemy import distinct
from config.db import get_db

from fastapi.responses import JSONResponse
from loguru import logger

from enums.task_enum import TaskStatusEnum
from models.exception import (
    ExcepActivityCreate,
    ExcepCategoryCreate,
    ExcepCavidCreate,
    ExceptionActivity,
    ExceptionCategory,
    ExceptionCavid,
)

from datetime import datetime, time

from models.task import Task


dashboard = APIRouter(
    prefix="/api/dashboards",
    tags=["Dashboard"],
    responses={404: {"msg": "No encontrado"}},
)


KNOWN_STATUSES = [status.value for status in TaskStatusEnum]


@dashboard.get("/")
def get_dashboard(
    month: Optional[int] = None,
    service_type: Optional[str] = None,
    request_activity: Optional[str] = None,
    db: Session = Depends(get_db),
):

    try:

        taskCount = 0
        taskCustomer = 0

        taskCount = db.query(Task).count()

        taskCustomer = db.query(distinct(Task.client)).count()

        # print("Dashboard")
        return JSONResponse({"taskCount": taskCount, "taskCustomer": taskCustomer})

    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": "Error en la base de datos"}
