from ast import parse
from datetime import datetime, timedelta, timezone
from io import BytesIO
import os
import sys
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
import pandas as pd

# from requests import Session
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db import get_db
from sqlalchemy.orm import Session

from fastapi.responses import JSONResponse
from loguru import logger

from models.task import Task, TaskCreate, TaskCrudoImport, TaskImport
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


# TODO:: IMPORTAR CRUDO
@task.post("/import-crudo/")
async def import_crudo_data(form: TaskCrudoImport, db: Session = Depends(get_db)):
    try:
        crudo_data = form.tasks
        updated_tasks = []
        tasknot_found = []

        for crudo in crudo_data:
            task = db.query(Task).filter(Task.code == crudo.code).first()

            if not task:
                print(f"Tarea {crudo.code} no encontrada.")
                tasknot_found.append(crudo.code)
                logger.error(f"Crudo no encontrado {tasknot_found}")
                continue

            # Only update fields that are not None or empty
            if crudo.root_cause is not None and crudo.root_cause.strip():
                task.root_cause = crudo.root_cause

            if crudo.attributable is not None and crudo.attributable.strip():
                task.attributable = crudo.attributable

            if (
                crudo.resolutioncategory_2ps is not None
                and crudo.resolutioncategory_2ps.strip()
            ):
                task.resolutioncategory_2ps = crudo.resolutioncategory_2ps

            if crudo.customer_waiting is not None and crudo.customer_waiting.strip():
                task.customer_waiting = crudo.customer_waiting

            if crudo.service_type is not None and crudo.service_type.strip():
                task.service_type = crudo.service_type

            db.add(task)
            db.commit()
            db.refresh(task)
            updated_tasks.append(task)

        return JSONResponse(
            {
                "code": 200,
                "message": f"Datos importados. {len(updated_tasks)} tareas procesadas correctamente.",
                "successful_tasks": len(updated_tasks),
            }
        )

    except Exception as global_error:
        db.rollback()
        logger.error(global_error)
        raise HTTPException(
            status_code=400,
            detail=f"Error global al importar los datos del CRUDO: {str(global_error)}",
        )


def parse_time_value(value):
    """
    Convierte diferentes formatos de tiempo a time without timezone
    """
    if pd.isna(value):
        return None

    try:
        # Si es un string, intentar diferentes formatos
        if isinstance(value, str):
            # Intentar formato "dd/mm/yyyy hh:mm:ss p. m."
            try:
                dt = datetime.strptime(value, "%d/%m/%Y %I:%M:%S %p. m.")
                return dt.time()
            except ValueError:
                pass

            # Intentar formato "dd/mm/yyyy hh:mm:ss"
            try:
                dt = datetime.strptime(value, "%d/%m/%Y %H:%M:%S")
                return dt.time()
            except ValueError:
                pass

            # Intentar formato "hh:mm:ss"
            try:
                t = datetime.strptime(value, "%H:%M:%S").time()
                return t
            except ValueError:
                pass

        # Si es datetime
        elif isinstance(value, datetime):
            return value.time()

        # Si es time
        elif isinstance(value, time):
            return value

    except Exception as e:
        logger.error(f"Error parseando tiempo: {value}, error: {str(e)}")
        return None

    return None


@task.post("/upload-excel")
async def upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        excel_data = BytesIO(contents)
        df = pd.read_excel(excel_data)

        required_columns = [
            "code",
            "root_cause",
            "attributable",
            "resolutioncategory_2ps",
            "customer_waiting",
            "service_type",
        ]

        if not all(col in df.columns for col in required_columns):
            return {"error": "Columnas requeridas faltantes en el Excel"}

        successful_updates = 0
        failed_updates = 0

        for index, row in df.iterrows():
            try:
                task = db.query(Task).filter(Task.code == row["code"]).first()

                if task:
                    customer_waiting_time = parse_time_value(row["customer_waiting"])

                    task.root_cause = (
                        row["root_cause"] if not pd.isna(row["root_cause"]) else None
                    )
                    task.attributable = (
                        row["attributable"]
                        if not pd.isna(row["attributable"])
                        else None
                    )
                    task.resolutioncategory_2ps = (
                        row["resolutioncategory_2ps"]
                        if not pd.isna(row["resolutioncategory_2ps"])
                        else None
                    )
                    task.customer_waiting = customer_waiting_time
                    task.service_type = (
                        row["service_type"]
                        if not pd.isna(row["service_type"])
                        else None
                    )

                    try:
                        db.commit()
                        successful_updates += 1
                    except Exception as commit_error:
                        db.rollback()
                        raise commit_error
                else:
                    failed_updates += 1
                    print(
                        f"No se encontró la tarea con código: {row['code']} (fila {index + 1})"
                    )
                    # logger.error(
                    #     f"No se encontró la tarea con código: {row['code']} (fila {index + 1})"
                    # )

            except Exception as e:
                failed_updates += 1
                db.rollback()
                logger.error(
                    f"Error actualizando fila {index + 1}, code: {row['code']}: {str(e)}"
                )
                continue

        return JSONResponse(
            {
                "code": 200,
                "successful_tasks": successful_updates,
                "failed_updates": failed_updates,
                "total_rows_processed": len(df),
            }
        )

    except Exception as e:
        logger.error(f"Error general procesando archivo: {str(e)}")
        return {"error": str(e), "status": "error"}
