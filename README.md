#RUN SERVER
uvicorn main:app --reload


# SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:snow123@localhost/api_etbkpi"
# SQLALCHEMY_DATABASE_URL = "postgresql://api_etbkpi_owner:IzVKRov2qn6c@ep-lively-resonance-a52ts2qe.us-east-2.aws.neon.tech/api_etbkpi?sslmode=require"


# Servidor LINUX
SQLALCHEMY_DATABASE_URL = "postgresql://admeiasa:eiasa.adm2024@db:5432/etbkpi_manager"

# SQLALCHEMY_DATABASE_URL = "postgresql://kpis_api_user:Yl95krRVDEoh45s93uxEfWAydOObVrk8@dpg-cth51t9opnds73auvsi0-a.oregon-postgres.render.com/kpis_api"

# Quitar de futuros cambios en git
git update-index --assume-unchanged app.log
# (Opcional) Si en el futuro quieres que Git vuelva a rastrear cambios en
git update-index --no-assume-unchanged app.log
