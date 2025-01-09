from ast import parse
from datetime import datetime, timedelta, timezone
import os
import sys
from fastapi import APIRouter, Depends, HTTPException

# from requests import Session
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db import get_db
from sqlalchemy.orm import Session

from fastapi.responses import JSONResponse
from loguru import logger

from models.task import Task, TaskCreate, TaskImport
from datetime import datetime, time

task_home = APIRouter(
    prefix="/api/tasks-home",
    tags=["Tareas - Home"],
    responses={404: {"msg": "No encontrado"}},
)


@task_home.get("/")
def find_all(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return tasks


@task_home.get("/code")
def find_by_code(code: str, db: Session = Depends(get_db)):
    task = find_task_by_code(code, db)
    return task


def find_task_by_code(code: str, db: Session = Depends(get_db)):

    task = db.query(Task).filter(Task.code == code).first()

    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    try:
        return task
    except Exception as e:
        logger.error(f"Error al encontrar la tarea: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# def get_order_by_id(order_id: str, db: Session = Depends(get_db)):
#     order = (
#         db.query(Order)
#         .options(joinedload(Order.order_details))
#         .filter(Order.id == order_id)
#         .first()
#     )
#     if not order:
#         raise HTTPException(status_code=404, detail="Orden no encontrada")
#     return order
