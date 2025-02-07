from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request, requests
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from requests import Session
from config.db import engine, get_db
from models.auth import authUser, LoginRecord
from models.user import User
from enums.user_enum import StatuEnum as UserStatuEnum


auth = APIRouter(
    prefix="/api/auth",
    tags=["Autenticación"],
    responses={404: {"msg": "No encontrado"}},
)

load_dotenv()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(60)
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"

REFRESH_TOKEN_EXPIRE_DAYS = int(2)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user(user_dict: dict):
    if user_dict:
        return user_dict
    return None


# # TODO: Implementar la autenticación
@auth.post("/login")
async def login(form_data: authUser, request: Request, db: Session = Depends(get_db)):

    user_db = db.query(User).filter(User.dni == form_data.username).first()

    if not user_db:
        raise HTTPException(status_code=400, detail="Usuario incorrecto")

    user = get_user(user_db)

    save_login_record(request, user.id, db)

    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    if user.statu == UserStatuEnum.inactive:
        raise HTTPException(
            status_code=400, detail="Usuario inactivo, contacte al administrador."
        )

    if not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.dni}, expires_delta=access_token_expires
    )

    # Generar refresh token
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_DAYS)

    user_response = {
        "id": user.id,
        "name": user.name,
        "dni": user.dni,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "statu": user.statu,
    }

    return {
        "user": user_response,
        "token": access_token,
    }


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# #TODO:: Implementar el verification token
@auth.get("/verify-token")
async def verify_token(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        dni: str = payload.get("sub")
        if dni is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception

    user_db = db.query(User).filter(User.dni == dni).first()
    user = get_user(user_db)

    if user is None:
        raise credentials_exception

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.dni}, expires_delta=access_token_expires
    )

    user_response = {
        "id": user.id,
        "name": user.name,
        "dni": user.dni,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "statu": user.statu,
    }

    return {"user": user_response, "token": access_token}


## TODO: LOGIN RECORDS
def save_login_record(request: Request, user_id: str, db: Session):

    ip_address = request.client.host
    browser_info = request.headers.get("User-Agent", "Desconocido")
    location = get_location_from_ip(ip_address)

    login_record = LoginRecord(
        user_id=user_id,
        ip_address=ip_address,
        location=location,
        browser_info=browser_info,
    )

    db.add(login_record)
    db.commit()

    return {"message": "Login registrado"}


def get_location_from_ip(ip: str):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        return response.json().get("city", "Desconocido")
    except:
        return "Desconocido"


@auth.get("/login-records")
def get_all_login_records(db: Session = Depends(get_db)):
    try:
        login_records = db.query(LoginRecord).all()

        result = []
        for record in login_records:
            user = db.query(User).filter(User.id == record.user_id).first()
            result.append(
                {
                    "id": record.id,
                    "user_name": user.name if user else "Desconocido",
                    "ip_address": record.ip_address,
                    "location": record.location,
                    "browser_info": record.browser_info,
                    "created_at": record.created_at,
                }
            )
        return result
    except Exception as e:
        print(f"Error al obtener los registros de login: {str(e)}")


@auth.delete("/access-delete")
def delete_access(db: Session = Depends(get_db)):
    try:

        db.query(LoginRecord).delete()
        db.commit()

        return JSONResponse(
            {"code": 200, "message": "Historial de Accesos eliminado exitosamente!"}
        )
    except Exception as e:
        print(f"Error al eliminar el acceso: {str(e)}")
