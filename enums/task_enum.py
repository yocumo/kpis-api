from enum import Enum


class TaskStatusEnum(Enum):
    completada = "active"
    cancelada = "inactive"
    asignada = "inactive"
    encurso = "En curso"
    porconfirmar = "Final x Confirmar ETB"
    encamino = "En camino"
