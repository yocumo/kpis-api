from fastapi import APIRouter, Depends, HTTPException, status
from requests import Session
from enums.user_enum import RoleEnum, StatuEnum
from models.auth import AuthReset
from passlib.context import CryptContext
from config.db import get_db
from models.user import (
    User,
    UserCreate,
    UserResponse,
    UserUpdate,
    UsersApiResponse,
)
from fastapi.responses import JSONResponse
from loguru import logger


user = APIRouter(
    prefix="/api/users", tags=["Usuarios"], responses={404: {"msg": "No encontrado"}}
)

# Configurar el contexto de hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@user.get("/", response_model=UsersApiResponse, status_code=status.HTTP_200_OK)
async def find_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    users_response = [UserResponse.from_orm(user) for user in users]
    return UsersApiResponse(code=200, data=users_response)


@user.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):

    try:
        user_exist = search_user_by_dni(user.dni, db)

        if user_exist is not None:
            raise HTTPException(status_code=400, detail="El usuario ya existe")

        if user.email:
            email_exist = db.query(User).filter(User.email == user.email).first()
            if email_exist:
                raise HTTPException(status_code=400, detail="El email ya existe")

        # Convertir en string el dni
        user.name = user.name.title()
        user_dict = dict(user)

        # Hashear la contraseña
        user_dict["password"] = pwd_context.hash(user_dict["password"])
        new_user = User(**user_dict)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"Usuario creado: {new_user}")
        return JSONResponse({"code": 201, "message": "Usuario creado exitosamente"})

    except Exception as e:
        logger.error(f"Usuario creado Error: {str(e)}")
        raise HTTPException(
            status_code=400, detail="Error al crear el usuario" + str(e)
        )


@user.post("/password-recovery")
async def password_recovery(form_data: AuthReset, db: Session = Depends(get_db)):

    try:
        user_exist = search_user_by_dni(form_data.username, db)
        if user_exist:
            user = db.query(User).filter(User.dni == form_data.username).first()
            user.password = pwd_context.hash(form_data.password)
            db.commit()

            logger.info(f"Contraseña recuperada: {user}")
            return JSONResponse(
                {"code": 200, "message": "La cuenta ha sido recuperada exitosamente"}
            )
        else:
            logger.error(f"Usuario no encontrado: {form_data.username}")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

    except Exception as e:
        logger.error(f"Contraseña recuperada Error: {str(e)}")
        raise HTTPException(
            status_code=400, detail="Error al recuperar la contraseña" + str(e)
        )


@user.get("/{id}", response_model=UsersApiResponse, status_code=status.HTTP_200_OK)
def find_user(id: str, db: Session = Depends(get_db)):
    return search_user_by_id(db, id)


@user.delete("/{id}")
def delete_user(id: str, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == id).first()
        db.delete(user)
        db.commit()
        return JSONResponse({"code": 200, "message": "Usuario eliminado exitosamente"})
    except Exception as e:
        logger.error(f"Usuario eliminado Error: {str(e)}")
        raise HTTPException(status_code=400, detail="Error al eliminar el usuario")


@user.patch("/{id}")
async def update_user(id: str, user: UserUpdate, db: Session = Depends(get_db)):
    try:
        user_db = db.query(User).filter(User.id == id).first()
        if not user_db:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        user_dict = dict(user)

        for key, value in user_dict.items():
            setattr(user_db, key, value)

        db.commit()
        db.refresh(user_db)
        logger.info(f"Usuario actualizado: {user_db}")
        return JSONResponse(
            {"code": 200, "message": "Usuario actualizado exitosamente"}
        )
    except Exception as e:
        logger.error(f"Usuario actualizado Error: {str(e)}")
        raise HTTPException(status_code=400, detail="Error al actualizar el usuario")


def search_user_by_dni(dni: str, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.dni == dni).first()
        return user
    except:
        return {"error": "Usuario no encontrado"}


def search_user_by_id(db: Session, id: str):
    try:
        user = db.query(User).filter(User.id == id).first()
        users_response = [UserResponse.from_orm(user)]
        return UsersApiResponse(code=200, data=users_response)
    except:
        return {"error": "Usuario no encontrado"}



# @user.get("/profile/{id}")
# def get_profile(id: str, db: Session = Depends(get_db)):

#     try:
#         user = db.query(User).filter(User.id == id).first()

#         if user is None:
#             return {"error": "Usuario no encontrado"}

#         return JSONResponse(
#             {
#                 "name": user.name,
#                 "dni": user.dni,
#                 "email": user.email,
#                 "role": getRole(user.role.value),
#                 "statu": "Activo" if user.statu.value == "active" else "Inactivo",
#                 "phone": user.phone,
#             }
#         )

#     except:
#         return {"error": "Error al obtener el perfil"}


def getRole(name: str):

    role = ""

    if name == "admin":
        role = "Administrador"


    if name == "superadmin":
        role = "Super Administrador"

    else:
        role = "Invitado"

    return role
