from enum import Enum


class TaskStatusEnum(Enum):
    completada = "Completada"
    cancelada = "Cancelada"
    asignada = "Asignada"
    encurso = "En curso"
    porconfirmar = "Final x Confirmar ETB"
    encamino = "en camino"
