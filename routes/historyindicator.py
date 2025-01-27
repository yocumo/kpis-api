import math
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case
from sqlalchemy.orm import Session

# from config.db import get_db

from fastapi.responses import JSONResponse
from loguru import logger

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db import get_db
from enums.user_enum import ServiceTypeEnum, TypeIHistoryEnum

from models.historyIndicator import (
    HistoryIndicator,
    KPICalculationRequest,
    RequestSearchHistory,
)
from models.task import Estimated, Task


kpi = APIRouter(
    prefix="/api/indicators",
    tags=["Historial Indicadores"],
    responses={404: {"msg": "No encontrado"}},
)


# TODO:: Calcula los KPIs utilizando consultas a los modelos Estimated y Task
def calcular_kpis_calculados(db: Session, month: str, service_type: str):

    task_summary = (
        db.query(
            Task.service_type,
            Task.request_activity,
            Task.status,
            Estimated.monthh,
            Estimated.compliance_etl_etr,
            Estimated.vr,
            Estimated.esi,
            Estimated.catv_test,
            Estimated.esi_catv_test,
            Estimated.ts,
        )
        .join(Estimated, Task.id == Estimated.task_id)
        .filter(Estimated.monthh == month, Task.service_type == service_type)
        .all()
    )

    # TODO:: Cálculo de ETL (Tiempo de Liquidación)
    etl_total = sum(
        1
        for task in task_summary
        if task.status == "Completada" and task.request_activity == "PROGRAMADA"
    )
    etl_cumple = sum(
        1
        for task in task_summary
        if task.status == "Completada"
        and task.request_activity == "PROGRAMADA"
        and task.compliance_etl_etr == "CUMPLE"
    )

    etl_rate = round((etl_cumple / etl_total * 100) if etl_total > 0 else 0, 2)

    # print("etl_rate", etl_total, etl_cumple, etl_rate)

    # TODO:: Cálculo de ETR (Tiempo de Respuesta)
    etr_total = sum(
        1
        for task in task_summary
        if task.status == "Completada" and task.request_activity == "INMEDIATA"
    )
    etr_cumple = sum(
        1
        for task in task_summary
        if task.status == "Completada"
        and task.request_activity == "INMEDIATA"
        and task.compliance_etl_etr == "CUMPLE"
    )
    etr_rate = round((etr_cumple / etr_total * 100) if etr_total > 0 else 0)

    # TODO::Cálculo de VR (Visitas Recurrentes)
    vr_total = sum(1 for task in task_summary if task.catv_test is not None)
    vr_recurrente = sum(
        1
        for task in task_summary
        if task.vr == "RECURRENTE" and task.catv_test is not None
    )
    vr_rate = 1 - (vr_recurrente / vr_total if vr_total > 0 else 0)

    # TODO:: Cálculo de ESI (Eventos sin Incidencia)
    esi_total = sum(
        1
        for task in task_summary
        if task.esi_catv_test and task.esi_catv_test.replace("-", "").isdigit()
    )
    esi_reincidente = sum(
        1
        for task in task_summary
        if task.esi == "REINCIDENTE"
        and task.esi_catv_test
        and task.esi_catv_test.replace("-", "").isdigit()
    )
    esi_rate = 1 - (esi_reincidente / esi_total if esi_total > 0 else 0)

    # TODO:: ES
    cumple_count = sum(1 for task in task_summary if task.ts == "CUMPLE")
    no_cumple_count = sum(1 for task in task_summary if task.ts == "NO CUMPLE")
    total_count = len(task_summary)

    es_rate = (
        round(cumple_count / (cumple_count + no_cumple_count) * 100, 2)
        if total_count > 0
        else 0
    )

    # TODO: TOTAL
    if service_type == "ASG_CUM_01":

        total_calculado = (
            etl_rate
            + etr_rate
            + 0  # TS inicialmente es NULL
            + vr_rate
            + esi_rate
            + 100
            + 96
            + 100
            + es_rate
        )

    elif service_type == "ASG_CUM_03":
        total_calculado = vr_rate + esi_rate + 100 + 96

    else:
        total_calculado = (
            etl_rate
            + etr_rate
            + 0  # TS inicialmente es NULL
            + vr_rate
            + esi_rate
            + 100
            + 96
            + es_rate
        )

    return {
        "month": month,
        "service_type_name": service_type,
        "etl": etl_rate,
        "etr": etr_rate,
        "ts": None,
        "vr": vr_rate,
        "esi": esi_rate,
        "efo": 100,
        "cd": 96,
        "etci": 100,
        "es": es_rate,
        "total": total_calculado,
    }


def calculate_percentage(value, multiplier):
    if value is None or multiplier is None:
        return 0
    return (value * multiplier) / 100


@kpi.post("/calculate-kpis")
def calculate_kpis(request: KPICalculationRequest, db: Session = Depends(get_db)):

    try:
        merged_data = {}
        for item in request.data:
            merged_data.update(item)

        if request.service_type not in [type.value for type in ServiceTypeEnum]:
            raise HTTPException(status_code=400, detail="Tipo de servicio inválido")

        # TODO::1. Fila de DATOS INGRESADOS
        datos_ingresados = HistoryIndicator(
            month=request.month,
            service_type_name=request.service_type,
            typei=TypeIHistoryEnum.registered.value,
            **{k.lower(): v for k, v in merged_data.items()},
        )
        db.add(datos_ingresados)

        # TODO::2. Fila de DATOS CALCULADOS
        kpis_calculados = calcular_kpis_calculados(
            db, request.month, request.service_type
        )
        datos_calculados = HistoryIndicator(
            **kpis_calculados, typei=TypeIHistoryEnum.indicator.value
        )
        db.add(datos_calculados)

        # TODO::3. Fila de RESULTADO (multiplicación)
        datos_resultado = HistoryIndicator(
            month=request.month,
            service_type_name=request.service_type,
            etl=calculate_percentage(merged_data.get("ETL", 0), kpis_calculados["etl"]),
            etr=calculate_percentage(merged_data.get("ETR", 0), kpis_calculados["etr"]),
            ts=calculate_percentage(
                merged_data.get("TS", 0), kpis_calculados.get("ts", 0)
            ),
            vr=calculate_percentage(merged_data.get("VR", 0), kpis_calculados["vr"]),
            esi=calculate_percentage(merged_data.get("ESI", 0), kpis_calculados["esi"]),
            efo=calculate_percentage(merged_data.get("EFO", 0), 100),
            cd=calculate_percentage(merged_data.get("CD", 0), 95),
            etci=calculate_percentage(merged_data.get("ETCI", 0), 100),
            es=calculate_percentage(merged_data.get("ES", 0), kpis_calculados["es"]),
            total=math.ceil(kpis_calculados["total"] * 100),
            typei=TypeIHistoryEnum.calculated.value,
        )

        db.add(datos_resultado)
        db.commit()

        return JSONResponse(
            {
                "code": 200,
                "message": "KPIs calculados correctamente",
            }
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@kpi.get("/")
def find_all_kpis(db: Session = Depends(get_db)):
    kpis = db.query(HistoryIndicator).all()
    return kpis


@kpi.get("/december_asg")
def find_all_kpis_indicator(db: Session = Depends(get_db)):
    kpis = (
        db.query(HistoryIndicator)
        .filter(HistoryIndicator.typei == TypeIHistoryEnum.indicator.value)
        .all()
    )
    return kpis


@kpi.post("/search/history")
def search_history(request: RequestSearchHistory, db: Session = Depends(get_db)):

    try:
        kpis = (
            db.query(HistoryIndicator)
            .filter(HistoryIndicator.typei == TypeIHistoryEnum.indicator.value)
            .filter(HistoryIndicator.month == request.month)
            .filter(HistoryIndicator.service_type_name == request.serviceType)
            .all()
        )

        if not kpis:
            raise HTTPException(status_code=404, detail="Indicadores no encontrados")
        return kpis

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@kpi.post("/search/allhistory")
def search_all_history(request: RequestSearchHistory, db: Session = Depends(get_db)):

    try:
        kpis = (
            db.query(HistoryIndicator)
            .filter(HistoryIndicator.month == request.month)
            .filter(HistoryIndicator.service_type_name == request.serviceType)
            .all()
        )

        if not kpis:
            raise HTTPException(status_code=404, detail="Indicadores no encontrados")
        return kpis

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@kpi.post("/delete/allhistory")
def delete_all_history(request: RequestSearchHistory, db: Session = Depends(get_db)):
    try:
        deleted_rows = (
            db.query(HistoryIndicator)
            .filter(HistoryIndicator.month == request.month)
            .filter(HistoryIndicator.service_type_name == request.serviceType)
            .delete(synchronize_session=False)
        )

        db.commit()

        if deleted_rows == 0:
            raise HTTPException(
                status_code=404, detail="No se encontraron indicadores para eliminar"
            )

        return JSONResponse(
            {
                "code": 200,
                "message": "Cáculo del KPI eliminado correctamente",
            }
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
