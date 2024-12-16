
def userEntity(item) -> dict:
    return {
        "id": str(item["id"]),
        "name": item["name"],
        "dni": item["dni"],
        "email": item["email"],
        "phone": item["phone"],
        "role": item["role"],
        "statu": item["statu"],
        "password": item["password"],
        "created_at": item["created_at"],
        "updated_at": item["updated_at"],
    }
    
    
def usersEntity(entity) -> list:
    return [userEntity(item) for item in entity]