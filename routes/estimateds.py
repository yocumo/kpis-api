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
