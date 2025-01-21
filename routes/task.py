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

task = APIRouter(
    prefix="/api/tasks", tags=["Tareas"], responses={404: {"msg": "No encontrado"}}
)


@task.get("/")
def find_all(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()

    return tasks


@task.post("/")
def create_task(form: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**form.dict())
    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@task.post("/import-from-excel/")
def import_from_excel(form: TaskImport, db: Session = Depends(get_db)):

    task_data = form.tasks
    updated_tasks = []
    error_task_codes = []

    try:
        for item in task_data:
            try:

                normalized_arrival_dead_time = item.arrival_dead_time
                normalized_execution_dead_time = item.execution_dead_time
                normalized_customer_waiting = item.customer_waiting

                print("CW", normalized_customer_waiting, item.customer_waiting)

                task = db.query(Task).filter(Task.code == item.code).first()

                if task:
                    # Actualización de tarea existente
                    task.documenter = item.documenter
                    task.code = item.code
                    task.client = item.client
                    task.description = item.description
                    task.address = item.address
                    task.cav_id = str(item.cav_id)
                    task.operational_category = item.operational_category
                    task.request_activity = item.request_activity
                    task.assigned_staff = item.assigned_staff
                    task.status = item.status
                    task.date_delivery_time = item.date_delivery_time
                    task.assigned_time = item.assigned_time
                    task.scheduled_time = item.scheduled_time
                    task.way_time = item.way_time
                    task.arrival_time = item.arrival_time
                    task.final_time = item.final_time
                    task.confirmation_time = item.confirmation_time
                    task.arrival_dead_time = normalized_arrival_dead_time
                    task.execution_dead_time = normalized_execution_dead_time
                    task.observation_dead_time = item.observation_dead_time
                    task.root_cause = item.root_cause
                    task.attributable = item.attributable
                    task.resolutioncategory_2ps = item.resolutioncategory_2ps
                    task.customer_waiting = normalized_customer_waiting
                    task.service_type = item.service_type
                    task.staff_dni = item.staff_dni

                else:
                    # Creación de nueva tarea
                    task = Task(
                        documenter=item.documenter,
                        code=item.code,
                        client=item.client,
                        description=item.description,
                        address=item.address,
                        cav_id=str(item.cav_id),
                        operational_category=item.operational_category,
                        request_activity=item.request_activity,
                        assigned_staff=item.assigned_staff,
                        status=item.status,
                        date_delivery_time=item.date_delivery_time,
                        assigned_time=(item.assigned_time),
                        scheduled_time=(item.scheduled_time),
                        way_time=(item.way_time),
                        arrival_time=(item.arrival_time),
                        final_time=(item.final_time),
                        confirmation_time=(item.confirmation_time),
                        arrival_dead_time=normalized_arrival_dead_time,
                        execution_dead_time=normalized_execution_dead_time,
                        observation_dead_time=item.observation_dead_time,
                        root_cause=item.root_cause,
                        attributable=item.attributable,
                        resolutioncategory_2ps=item.resolutioncategory_2ps,
                        customer_waiting=normalized_customer_waiting,
                        service_type=item.service_type,
                        staff_dni=item.staff_dni,
                    )
                    db.add(task)

                db.flush()
                updated_tasks.append(task)

            except Exception as task_error:
                error_task_codes.append(item.code)
                print(f"Error con tarea {item.code}: {str(task_error)}")
                continue

        db.commit()

        if error_task_codes:
            error_file_path = "task_import_errors.txt"
            with open(error_file_path, "w") as f:
                f.write("\n".join(error_task_codes))
            print(f"Códigos de tareas con errores guardados en {error_file_path}")

        return JSONResponse(
            {
                "code": 200,
                "message": f"Datos importados. {len(updated_tasks)} tareas procesadas correctamente. {len(error_task_codes)} tareas con errores.",
                "successful_tasks": len(updated_tasks),
                "failed_tasks": len(error_task_codes),
            }
        )

    except Exception as global_error:
        db.rollback()
        logger.error(global_error)
        raise HTTPException(
            status_code=400,
            detail=f"Error global al importar los datos: {str(global_error)}",
        )
