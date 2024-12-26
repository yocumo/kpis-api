from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:snow123@localhost/api_etbkpi"
# SQLALCHEMY_DATABASE_URL = "postgresql://api_etbkpi_owner:IzVKRov2qn6c@ep-lively-resonance-a52ts2qe.us-east-2.aws.neon.tech/api_etbkpi?sslmode=require"


# Servidor LINUX
# SQLALCHEMY_DATABASE_URL = "postgresql://admeiasa:eiasa.adm2024@db:5432/etbkpi_manager"

# SQLALCHEMY_DATABASE_URL = "postgresql://kpis_api_user:Yl95krRVDEoh45s93uxEfWAydOObVrk8@dpg-cth51t9opnds73auvsi0-a.oregon-postgres.render.com/kpis_api"


engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={}, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
