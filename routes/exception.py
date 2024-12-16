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


# TODO: --------------------------------- FIN Excepciones Actividades
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
