from fastapi import FastAPI

from routes.user import user as users
from routes.auth import auth
from routes.task import task
from routes.exception import exceptione
from routes.estimateds import estimated
from routes.historyindicator import kpi

from loguru import logger
import sys
from fastapi.middleware.cors import CORSMiddleware
from config.db import engine

from models import user as user_model
from models import historyIndicator as history_indicator
from models import exception as exception

user_model.Base.metadata.create_all(bind=engine)
history_indicator.Base.metadata.create_all(bind=engine)
exception.Base.metadata.create_all(bind=engine) 


app = FastAPI(title="KPI - ETB")


# Configure loguru
logger.remove()  
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)
logger.add("app.log", rotation="500 MB", retention="7 days")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth)
app.include_router(users)
app.include_router(task)
app.include_router(estimated)
app.include_router(exceptione)
app.include_router(kpi)



# if __name__ == "__main__":
#     import uvicorn

#     uvicorn.run("app2:app", host="0.0.0.0", port=8002, reload=True)
