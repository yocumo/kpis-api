from ast import parse
from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status
import pandas as pd
from requests import Session
from config.db import get_db

from fastapi.responses import JSONResponse
from loguru import logger

from models.exception import (
    ExcepActivityCreate,
    ExcepCategoryCreate,
    ExcepCavidCreate,
    ExceptionActivity,
    ExceptionCategory,
    ExceptionCavid,
)
from datetime import datetime, time


exceptione = APIRouter(
    prefix="/api/exceptions",
    tags=["Excepciones"],
    responses={404: {"msg": "No encontrado"}},
)


# TODO: --------------------------------- Excepciones Actividades
@exceptione.get("/activities")
def find_all_activity(db: Session = Depends(get_db)):
    activities = db.query(ExceptionActivity).all()

    return activities


@exceptione.post("/activities")
def create_activity(form: ExcepActivityCreate, db: Session = Depends(get_db)):
    activity = ExceptionActivity(**form.dict())
    db.add(activity)
    db.commit()
    db.refresh(activity)

    return activity


@exceptione.patch("/activities/{id}")
def update_activity(id: str, form: ExcepActivityCreate, db: Session = Depends(get_db)):
    activity = db.query(ExceptionActivity).filter(ExceptionActivity.id == id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")

    for key, value in form.dict(exclude_unset=True).items():
        setattr(activity, key, value)

    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


# TODO: --------------------------------- FIN Excepciones Categorias
@exceptione.get("/categories")
def find_all_category(db: Session = Depends(get_db)):
    categories = db.query(ExceptionCategory).all()
    return categories


@exceptione.post("/categories")
def create_category(form: ExcepCategoryCreate, db: Session = Depends(get_db)):
    category = ExceptionCategory(**form.dict())
    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@exceptione.patch("/categories/{id}")
def update_category(id: str, form: ExcepCategoryCreate, db: Session = Depends(get_db)):
    category = db.query(ExceptionCategory).filter(ExceptionCategory.id == id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

    for key, value in form.dict(exclude_unset=True).items():
        setattr(category, key, value)

    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# TODO: --------------------------------- FIN Excepciones Tipo Cateorias


@exceptione.get("/cavid")
def find_all_cavid(db: Session = Depends(get_db)):
    cavids = db.query(ExceptionCavid).all()
    return cavids


@exceptione.post("/cavid")
def create_cavid(form: ExcepCavidCreate, db: Session = Depends(get_db)):
    cavid = ExceptionCavid(**form.dict())
    db.add(cavid)
    db.commit()
    db.refresh(cavid)

    return cavid


@exceptione.patch("/cavid/{id}")
def update_cavid(id: str, form: ExcepCavidCreate, db: Session = Depends(get_db)):
    cavid = db.query(ExceptionCavid).filter(ExceptionCavid.id == id).first()
    if not cavid:
        raise HTTPException(status_code=404, detail="CAV/ID no encontrada")

    for key, value in form.dict(exclude_unset=True).items():
        setattr(cavid, key, value)

    db.add(cavid)
    db.commit()
    db.refresh(cavid)
    return cavid
