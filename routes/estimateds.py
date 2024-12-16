from ast import parse
from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status
import pandas as pd
from requests import Session
from config.db import get_db

from fastapi.responses import JSONResponse
from loguru import logger

from models.task import Estimated, Task

estimated = APIRouter(
    prefix="/api/estimateds",
    tags=["Indicadores"],
    responses={404: {"msg": "No encontrado"}},
)


@estimated.get("/")
def find_all(db: Session = Depends(get_db)):
    alle = db.query(Estimated).all()

    return alle


# Si quieres incluir la tarea relacionada
@estimated.get("/with-tasks")
def find_all_with_tasks(db: Session = Depends(get_db)):
    estimated_items = (
        db.query(Estimated, Task).join(Task, Estimated.task_id == Task.id).all()
    )

    result = []
    for estimated, task in estimated_items:
        estimated_dict = estimated.__dict__
        task_dict = task.__dict__

        # Eliminar claves internas de SQLAlchemy
        estimated_dict.pop("_sa_instance_state", None)
        task_dict.pop("_sa_instance_state", None)

        # Combinar los diccionarios
        combined_item = {
            **estimated_dict,
            "task_code": task_dict.get("code"),
            "task_status": task_dict.get("status"),
            "toperational_category": task_dict.get("operational_category"),
            "trequest_activity": task_dict.get("request_activity"),
            "tassigned_staff": task_dict.get("assigned_staff"),
            "tstaff_dni": task_dict.get("staff_dni"),
        }
        result.append(combined_item)

    return result


@estimated.get("/filters/compliance")
def find_by_compliance(filterOp: str, db: Session = Depends(get_db)):

    try:
        alle = (
            db.query(Estimated).filter(Estimated.compliance_etl_etr == filterOp).count()
        )
        return JSONResponse({"code": 200, "qty": alle})
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": "Error en la base de datos"}
