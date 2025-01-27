from ast import parse
from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status
import pandas as pd
from requests import Session
from sqlalchemy import case, distinct, extract, func
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
        # Base query with filters
        base_query = db.query(Task)
        if month:
            base_query = base_query.filter(
                extract("month", Task.date_delivery_time) == month
            )
        if service_type:
            base_query = base_query.filter(Task.service_type == service_type)
        if request_activity:
            base_query = base_query.filter(Task.request_activity == request_activity)

        # Apply filters to status count
        results = (
            base_query.with_entities(Task.status, func.count(Task.id))
            .group_by(Task.status)
            .all()
        )
        taskCount = base_query.count()
        taskCustomer = base_query.with_entities(distinct(Task.client)).count()

        status_mapping = {
            "Completada": "completed",
            "Cancelada": "cancelled",
            "Asignada": "asigned",
            "En curso": "ongoing",
            "Final x Confirmar ETB": "byconfirmed",
            "en camino": "onway",
        }
        count_by_status = {
            "completed": 0,
            "cancelled": 0,
            "asigned": 0,
            "ongoing": 0,
            "byconfirmed": 0,
            "onway": 0,
        }

        for status, count in results:
            status_value = (
                status.value if isinstance(status, TaskStatusEnum) else status
            )
            if status_value in status_mapping:
                count_by_status[status_mapping[status_value]] = count

        # Daily tasks with filters
        daily_tasks = (
            base_query.with_entities(
                func.date(Task.date_delivery_time).label("date"),
                func.sum(
                    case((Task.request_activity == "INMEDIATA", 1), else_=0)
                ).label("immediate"),
                func.sum(
                    case((Task.request_activity == "PROGRAMADA", 1), else_=0)
                ).label("programmed"),
            )
            .group_by(func.date(Task.date_delivery_time))
            .order_by(func.date(Task.date_delivery_time))
            .all()
        )

        tasks_by_day = [
            {
                "date": str(day.date),
                "immediate": day.immediate,
                "programmed": day.programmed,
            }
            for day in daily_tasks
        ]

        # Activity percentages with filters
        filtered_activity_query = base_query.filter(
            Task.request_activity.in_(["INMEDIATA", "PROGRAMADA"])
        )
        total_activities = filtered_activity_query.count() or 1

        activity_counts = (
            filtered_activity_query.with_entities(
                Task.request_activity, func.count(Task.id)
            )
            .group_by(Task.request_activity)
            .all()
        )

        activity_percentages = {"immediate": 0, "programmed": 0}
        activity_counts_data = {"immediate": 0, "programmed": 0}

        for activity, count in activity_counts:
            if activity == "INMEDIATA":
                activity_counts_data["immediate"] = count
                activity_percentages["immediate"] = round(
                    (count / total_activities) * 100, 2
                )
            elif activity == "PROGRAMADA":
                activity_counts_data["programmed"] = count
                activity_percentages["programmed"] = round(
                    (count / total_activities) * 100, 2
                )

        return JSONResponse(
            {
                "task_count": taskCount,
                "customer_count": taskCustomer,
                "count_by_status": count_by_status,
                "activity_percentages": activity_percentages,
                "activity_counts": activity_counts_data,
                "tasks_by_day": tasks_by_day,
            }
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": "Error en la base de datos"}


## TODO:: Hora Llegada


def round_to_30_minutes(dt):
    if dt.minute >= 30:
        minutes = 30
    else:
        minutes = 0
    return dt.replace(minute=minutes, second=0, microsecond=0)


@dashboard.get("/tasks/arrival-time")
async def get_arrival_time(month: Optional[int], db: Session = Depends(get_db)):
    try:
        if month is None:
            raise HTTPException(status_code=400, detail="El mes es requerido")

        # Crear un CTE para redondear las fechas
        rounded_times = (
            db.query(
                func.date_trunc("day", Task.arrival_time).label("day"),
                func.date_trunc("hour", Task.arrival_time).label("hour"),
                extract("minute", Task.arrival_time).label("minute"),
            )
            .filter(extract("month", Task.arrival_time) == month)
            .cte()
        )

        # Consulta para obtener las horas únicas redondeadas a intervalos de 30 minutos
        time_expression = func.date_trunc("hour", rounded_times.c.hour) + case(
            (rounded_times.c.minute >= 30, timedelta(minutes=30)),
            else_=timedelta(minutes=0),
        ).label("time_slot")

        unique_slots = (
            db.query(time_expression).distinct().order_by(time_expression).all()
        )

        # Convertir a formato string
        time_slots = [
            slot[0].strftime("%Y-%m-%d %H:%M:%S.000") for slot in unique_slots
        ]

        return {"time_slots": time_slots, "total": len(time_slots)}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error al obtener franjas horarias: {e}")
        raise HTTPException(
            status_code=500, detail="Error al procesar la solicitud de franjas horarias"
        )
