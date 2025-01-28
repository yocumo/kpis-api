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


def convert_string_to_time(time_str):
    """
    Convierte un string de tiempo a objeto time.
    Acepta formatos como: "HH:MM:SS", "HH:MM"
    """
    if pd.isna(time_str):
        return None

    try:
        # Intentar diferentes formatos comunes
        formats_to_try = ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"]

        for fmt in formats_to_try:
            try:
                parsed_time = datetime.strptime(str(time_str).strip(), fmt).time()
                return parsed_time
            except ValueError:
                continue

        raise ValueError(f"No se pudo convertir el tiempo: {time_str}")
    except Exception as e:
        logger.error(f"Error convirtiendo tiempo {time_str}: {str(e)}")
        return None


def convert_date_format(date_value):
    """
    Convierte la fecha al formato esperado por PostgreSQL (YYYY-MM-DD HH:MM:SS)
    """
    if pd.isna(date_value):
        return None

    try:
        # Si ya es datetime, solo formatear
        if isinstance(date_value, datetime):
            return date_value.strftime("%Y-%m-%d %H:%M:%S")

        # Si es string, intentar diferentes formatos
        formats_to_try = [
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M",
            "%d/%m/%y %H:%M:%S",
            "%d/%m/%y %H:%M",
        ]

        date_str = str(date_value).strip()

        for fmt in formats_to_try:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

        raise ValueError(f"No se pudo convertir la fecha: {date_value}")
    except Exception as e:
        logger.error(f"Error convirtiendo fecha {date_value}: {str(e)}")
        return None


@task.post("/upload-task/")
async def upload_task_excel(
    file: UploadFile = File(...), db: Session = Depends(get_db)
):
    error_task_codes = []
    updated_tasks = []

    try:
        try:
            contents = await file.read()
            excel_data = BytesIO(contents)
            df = pd.read_excel(excel_data)
        except Exception as e:
            logger.error(f"Error al leer el archivo Excel: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Error al leer el archivo Excel. Verifique el formato."
                },
            )

        # Define column groups for validation and processing
        time_string_columns = ["arrival_dead_time", "execution_dead_time"]

        datetime_columns = [
            "date_delivery_time",
            "assigned_time",
            "scheduled_time",
            "way_time",
            "arrival_time",
            "final_time",
            "confirmation_time",
        ]

        required_columns = [
            "documenter",
            "code",
            "client",
            "description",
            "address",
            "cav_id",
            "operational_category",
            "request_activity",
            "assigned_staff",
            "status",
            *datetime_columns,
            *time_string_columns,
            "observation_dead_time",
            "staff_dni",
        ]

        # Validate required columns
        if not all(col in df.columns for col in required_columns):
            missing_columns = [col for col in required_columns if col not in df.columns]
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"Columnas requeridas faltantes en el Excel: {', '.join(missing_columns)}"
                },
            )

        # Process each row independently
        for index, row in df.iterrows():
            current_session = db  # Create savepoint
            try:
                # Validar que el código no esté vacío
                if pd.isna(row["code"]):
                    error_task_codes.append(f"Fila {index + 1}: Código vacío")
                    current_session.rollback()
                    continue

                # Process time and datetime values for current row
                processed_data = {}

                # Process string time columns (arrival_dead_time, execution_dead_time)
                for col in time_string_columns:
                    try:
                        processed_data[col] = (
                            convert_string_to_time(row[col])
                            if pd.notna(row[col])
                            else None
                        )
                    except Exception as e:
                        logger.error(
                            f"Error procesando columna {col} en fila {index + 1}: {str(e)}"
                        )
                        processed_data[col] = None

                # Process datetime columns
                for col in datetime_columns:
                    try:
                        processed_data[col] = convert_date_format(row[col])
                    except Exception as e:
                        logger.error(
                            f"Error procesando columna {col} en fila {index + 1}: {str(e)}"
                        )
                        processed_data[col] = None

                # Prepare task data
                task_data = {
                    "documenter": (
                        row["documenter"] if pd.notna(row["documenter"]) else None
                    ),
                    "code": str(row["code"]),
                    "client": row["client"] if pd.notna(row["client"]) else None,
                    "description": (
                        row["description"] if pd.notna(row["description"]) else None
                    ),
                    "address": row["address"] if pd.notna(row["address"]) else None,
                    "cav_id": str(row["cav_id"]) if pd.notna(row["cav_id"]) else None,
                    "operational_category": (
                        row["operational_category"]
                        if pd.notna(row["operational_category"])
                        else None
                    ),
                    "request_activity": (
                        row["request_activity"]
                        if pd.notna(row["request_activity"])
                        else None
                    ),
                    "assigned_staff": (
                        row["assigned_staff"]
                        if pd.notna(row["assigned_staff"])
                        else None
                    ),
                    "status": row["status"] if pd.notna(row["status"]) else None,
                    "staff_dni": (
                        row["staff_dni"] if pd.notna(row["staff_dni"]) else None
                    ),
                    "observation_dead_time": (
                        row["observation_dead_time"]
                        if pd.notna(row["observation_dead_time"])
                        else None
                    ),
                    **processed_data,  # Add processed time and datetime values
                }

                try:
                    # Intentar obtener la tarea existente
                    task = db.query(Task).filter(Task.code == task_data["code"]).first()

                    if task:
                        # Update existing task
                        for key, value in task_data.items():
                            setattr(task, key, value)
                    else:
                        # Create new task
                        task = Task(**task_data)
                        db.add(task)

                    db.flush()  # Try to flush changes
                    updated_tasks.append(task_data["code"])
                    current_session.commit()  # Commit this row's changes

                except Exception as task_error:
                    # Log specific error for this task
                    error_message = f"Fila {index + 1}, Código {task_data['code']}: {str(task_error)}"
                    logger.error(error_message)
                    error_task_codes.append(task_data["code"])
                    current_session.rollback()  # Rollback changes for this row only
                    continue

            except Exception as row_error:
                # Handle any other errors in row processing
                error_message = f"Error procesando fila {index + 1}: {str(row_error)}"
                logger.error(error_message)
                error_task_codes.append(f"Fila {index + 1}")
                current_session.rollback()
                continue

        # Save error codes to file
        if error_task_codes:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file_path = f"task_import_errors_{timestamp}.txt"
            with open(error_file_path, "w") as f:
                f.write(
                    "\n".join(
                        [f"{code}: Error al procesar" for code in error_task_codes]
                    )
                )
            logger.info(f"Códigos de tareas con errores guardados en {error_file_path}")

        return JSONResponse(
            content={
                "code": 200,
                "message": f"Importación completada. {len(updated_tasks)} tareas procesadas correctamente. {len(error_task_codes)} tareas con errores.",
                "successful_tasks": len(updated_tasks),
                "failed_tasks": len(error_task_codes),
                "total_rows_processed": len(df),
                "error_file": error_file_path if error_task_codes else None,
            }
        )

    except Exception as global_error:
        logger.error(f"Error general en el proceso de importación: {str(global_error)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Error general en el proceso de importación",
                "detail": str(global_error),
                "successful_tasks": len(updated_tasks),
                "failed_tasks": len(error_task_codes),
                "total_rows_processed": len(updated_tasks) + len(error_task_codes),
            },
        )


# TODO:: IMPORTAR CRUDO


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


@task.post("/upload-crudo/")
async def upload_crudo(file: UploadFile = File(...), db: Session = Depends(get_db)):
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
