import re
import pandas as pd
from datetime import datetime, timedelta
import concurrent.futures

# import Sytex
import tkinter as tk
from tkcalendar import DateEntry

import sys
import os

# Añadir el directorio A al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Importar el módulo completo
import Sytex

direccion_pattern = r"Direccion:(.*?)\n"
cav_id_pattern = r"CAV/ID:(.*?)\n"
categoria_pattern = r"Categorizacion Operacional:(.*?)\n"


def FindTask_status(id):
    Taskurl = f"https://app.sytex.io/api/statushistory/?content_type__model=task&object_id={id}&status_field__in=status,status_step"
    return Sytex.RunApi(Taskurl)


def FindTask(id):
    Taskurl = "https://app.sytex.io/api/task/?id=" + id
    return Sytex.RunApi(Taskurl)


def converhora(fecha_hora_original):
    # Convertir la cadena de fecha y hora original a un objeto datetime
    fecha_hora_objeto = datetime.fromisoformat(fecha_hora_original)

    # Restar 2 horas al objeto datetime
    fecha_hora_objeto -= timedelta(hours=2)

    # Formatear la fecha y hora en formato "Año/Mes/Día Hora:Minuto:Segundo"
    fecha_hora_militar = fecha_hora_objeto.strftime("%d/%m/%Y %H:%M:%S")

    return fecha_hora_militar


def FindTask_desde_hasta(fecha_desde, fecha_hasta):
    fecha_desde = fecha_desde.strftime("%Y-%m-%d")
    fecha_hasta = fecha_hasta.strftime("%Y-%m-%d")

    if fecha_desde == fecha_hasta:
        Taskurl = f"https://app.sytex.io/api/task/?plan_date_duration={fecha_desde}&project=1909&task_template=467&limit=4000"
    else:
        Taskurl = f"https://app.sytex.io/api/task/?task_template=467&project=1909&plan_date_duration=_{fecha_desde}_{fecha_hasta}_&limit=4000"

    # Taskurl = "https://app.sytex.io/api/task/reduced/?code=" + str('TAS000000589769')
    return Sytex.RunApi(Taskurl)


def seg_Descrip(texto):

    direccion_match = re.search(direccion_pattern, texto)
    cav_id_match = re.search(cav_id_pattern, texto)
    categoria_match = re.search(categoria_pattern, texto)

    # Extraer la información de las coincidencias
    direccion = direccion_match.group(1).strip() if direccion_match else None
    cav_id = cav_id_match.group(1).strip() if cav_id_match else None
    categoria_operacional = (
        categoria_match.group(1).strip() if categoria_match else None
    )

    return direccion, cav_id, categoria_operacional


def FindTaskDoc(id):
    id = str(id)
    Taskurl = " https://app.sytex.io/api/taskdocument/?task=" + id
    return Sytex.RunApi(Taskurl)


def find_fom_(id):
    id = str(id)
    Taskurl = f"https://app.sytex.io/api/urformdata/{id}/?exclude_deleted=true"
    return Sytex.RunApi(Taskurl)


def find_Form_question(id, valor_a_buscar):
    Form = FindTaskDoc(id)
    id = Form["results"][0]["document"]["id"]
    j = find_fom_(str(id))
    id_encontrado = None

    # Bucle para buscar el valor en la lista de diccionarios
    for diccionario in j["entry_set"]:
        if diccionario.get("index") == valor_a_buscar:
            # Si encontramos el valor, guardamos el 'id' y salimos del bucle
            id_encontrado = diccionario.get("id")
            break

    if id_encontrado is not None:
        # print(id_encontrado)

        for diccionario in j["entryanswer_set"]:
            if diccionario.get("entry") == id_encontrado:
                # Si encontramos el valor, guardamos el 'id' y salimos del bucle
                id_encontrado = diccionario.get("answer")
                break

    if id_encontrado is not None:
        # print(id_encontrado)
        return id_encontrado
    else:
        return None


def convertir_a_hora(cadena_tiempo):
    # Formato con fracciones de segundo
    formato_con_fracciones = "%H:%M:%S.%f"

    # Intentar parsear la cadena con fracciones de segundo
    try:
        hora_datetime = datetime.strptime(cadena_tiempo, formato_con_fracciones)
    except ValueError:
        print("Error al parsear la cadena de tiempo.")

    # Extraer solo hora, minutos y segundos
    hora_sin_fracciones = hora_datetime.strftime("%H:%M:%S")

    return hora_sin_fracciones


# Define una función que ejecuta find_Form_question(id, valor_a_buscar) para un solo id y valor_a_buscar
def find_Form_question_threaded(id, valor_a_buscar):
    result = find_Form_question(id, valor_a_buscar)
    return result


def convert_date_format(date_str, input_formats=None, output_format="%d/%m/%Y"):

    if not input_formats:
        input_formats = [
            "%Y-%m-%d",  # YYYY-MM-DD (most recent error case)
            "%d-%m-%Y",  # DD-MM-YYYY
            "%m-%d-%Y",  # MM-DD-YYYY
            "%Y/%m/%d",  # YYYY/MM/DD
            "%d/%m/%Y",  # DD/MM/YYYY
        ]

    for fmt in input_formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime(output_format)
        except ValueError:
            continue

    print(f"Could not convert date: {date_str}")
    return date_str


def safe_date_conversion(date_lists):
    return [
        [convert_date_format(date) if date else None for date in date_list]
        for date_list in date_lists
    ]


def format_datetime(request_time, request_date):
    time_without_fractions = request_time.split(".")[0]

    hora_datetime = datetime.strptime(time_without_fractions, "%H:%M:%S")
    hora_formateada = hora_datetime.strftime("%H:%M:%S")

    fecha_datetime = datetime.strptime(request_date, "%Y-%m-%d")
    fecha_formateada = fecha_datetime.strftime("%d/%m/%Y")

    return f"{fecha_formateada} {hora_formateada}"


def limpiar_tiempo(tiempo):
    if (
        tiempo is None
        or tiempo == "0"
        or tiempo == "0:0"
        or tiempo == "0:00"
        or tiempo == ".0"
        or tiempo == "N/A"
    ):
        return None

    # Normalizar el formato de tiempo
    tiempo = str(tiempo).strip()

    # Eliminar texto después del tiempo si existe
    tiempo = tiempo.split()[0]

    # Corregir formatos como '01.00' a '01:00'
    tiempo = tiempo.replace(".", ":")

    # Asegurar el formato HH:MM
    try:
        # Si solo tiene un dígito en horas o minutos, agregar un cero
        partes = tiempo.split(":")
        if len(partes[0]) == 1:
            partes[0] = partes[0].zfill(2)
        if len(partes[1]) == 1:
            partes[1] = partes[1].zfill(2)

        tiempo_formateado = ":".join(partes)

        datetime.strptime(tiempo_formateado, "%H:%M")

        return tiempo_formateado

    except (ValueError, IndexError):
        return None


def work1(fecha_desde, fecha_hasta):
    a = FindTask_desde_hasta(fecha_desde, fecha_hasta)
    # print(a["count"])

    lista_en_camino = []
    lista_En_curso = []
    lista_Final_x_Confirmar_ETB = []
    lista_Completada = []
    lista_asignado = []
    lista_tarea = []
    lista_DOC = []
    lista_Client = []
    lista_Descript = []
    lista_dir = []
    lista_CAV = []
    lista_Cap_opera = []
    lista_atributo = []
    lista_tecnico = []
    lista_status = []
    lista_entrega_etb = []
    lista_plan_inicio = []
    lista_tiempo_muerto_llegada = []
    lista_tiempo_muerto_ejecucion = []
    lista_descripo_time_muert = []
    lista_staff_dni = []

    if a["count"] == 0:
        print("No hay tareas en el rango de fechas proporcionado.")
        return
    lista_tareas = [str(Form["id"]) for Form in a["results"]]

    # Lista para almacenar los resultados
    time_death_time_arrive = []
    time_death_time_execution = []
    obs_time_death = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        status = executor.map(FindTask_status, lista_tareas)
        Tasks = executor.map(FindTask, lista_tareas)

        time_death_time_arrive = list(
            executor.map(
                find_Form_question_threaded, lista_tareas, ["1.12"] * len(lista_tareas)
            )
        )
        time_death_time_execution = list(
            executor.map(
                find_Form_question_threaded, lista_tareas, ["1.13"] * len(lista_tareas)
            )
        )
        obs_time_death = list(
            executor.map(
                find_Form_question_threaded, lista_tareas, ["1.14"] * len(lista_tareas)
            )
        )

    for task, stat, llegada, ejecucion, obs in zip(
        Tasks, status, time_death_time_arrive, time_death_time_execution, obs_time_death
    ):
        # print(task['results'][0]['code'])

        try:
            Time_death_llegada = llegada
            Time_death_ejecucion = ejecucion
            obs_death = obs

            lista_DOC.append(task["results"][0]["_who_created"])
            lista_tarea.append(task["results"][0]["code"])
            lista_Client.append(task["results"][0]["client"]["name"])

            if task["results"][0]["description"]:
                lista_Descript.append(task["results"][0]["description"])

            if task["results"][0]["description"] != None:
                Dir, cav, cat_ope = seg_Descrip(task["results"][0]["description"])

                lista_dir.append(str(Dir))
                lista_CAV.append(str(cav))
                lista_Cap_opera.append(str(cat_ope))

            if Time_death_llegada:
                lista_tiempo_muerto_llegada.append(Time_death_llegada)

            if Time_death_ejecucion:
                lista_tiempo_muerto_ejecucion.append(Time_death_ejecucion)

            if obs_death:
                lista_descripo_time_muert.append(obs_death)

            if task["results"][0]["attributes"]:
                lista_atributo.append(str(task["results"][0]["attributes"][0]["name"]))

            if task["results"][0]["assigned_staff"]:
                lista_tecnico.append(task["results"][0]["assigned_staff"]["name"])

            if task["results"][0]["assigned_staff"]:
                lista_staff_dni.append(task["results"][0]["assigned_staff"]["code"])

            lista_status.append(
                task["results"][0]["status_step_display"]["name"]["name"]
            )

            # Procesar los tiempos
            tiempo_muerto_llegada = [
                limpiar_tiempo(tiempo) for tiempo in lista_tiempo_muerto_llegada
            ]

            hora_datetime = datetime.strptime(
                task["results"][0]["_when_created"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            hora_menos_5_horas = hora_datetime - timedelta(hours=5)
            hora_menos_5_horas_formateada = hora_menos_5_horas.strftime(
                "%d/%m/%Y %H:%M:%S"
            )

            lista_asignado.append(hora_menos_5_horas_formateada)

            if (
                task["results"][0]["start_plan_time"] != None
                and task["results"][0]["start_plan_date"] != None
            ):
                hora_time = datetime.strptime(
                    task["results"][0]["start_plan_time"], "%H:%M:%S"
                )
                hora_date = datetime.strptime(
                    task["results"][0]["start_plan_date"], "%Y-%m-%d"
                )
                fecha_hora = datetime(
                    year=hora_date.year,
                    month=hora_date.month,
                    day=hora_date.day,
                    hour=hora_time.hour,
                    minute=hora_time.minute,
                    second=hora_time.second,
                )

                lista_plan_inicio.append(fecha_hora.strftime("%d/%m/%Y %H:%M:%S"))

            fecha_hora_combinada_str = format_datetime(
                task["results"][0]["request_time"], task["results"][0]["request_date"]
            )

            lista_entrega_etb.append(str(fecha_hora_combinada_str))

            for f in stat["results"]:
                if f["to_status_step"]:
                    status_step_new_value = f["to_status_step"]["name"]["name"]
                    if status_step_new_value == "en camino":
                        when_edited = f["when_created"]
                        when_edited = converhora(when_edited)
                        lista_en_camino.append(when_edited)
                    elif status_step_new_value == "En curso":
                        when_edited = f["when_created"]
                        when_edited = converhora(when_edited)
                        lista_En_curso.append(when_edited)
                    elif status_step_new_value == "Final x Confirmar ETB":
                        when_edited = f["when_created"]
                        when_edited = converhora(when_edited)
                        lista_Final_x_Confirmar_ETB.append(when_edited)
                    elif status_step_new_value == "Completada":
                        when_edited = f["when_created"]
                        when_edited = converhora(when_edited)
                        lista_Completada.append(when_edited)

            todas_listas = [
                lista_DOC,
                lista_tarea,
                lista_Client,
                lista_Descript,
                lista_dir,
                lista_CAV,
                lista_Cap_opera,
                lista_atributo,
                lista_tecnico,
                lista_status,
                lista_entrega_etb,
                lista_asignado,
                lista_plan_inicio,
                lista_en_camino,
                lista_En_curso,
                lista_Final_x_Confirmar_ETB,
                lista_Completada,
                tiempo_muerto_llegada,
                lista_tiempo_muerto_ejecucion,
                lista_descripo_time_muert,
                lista_staff_dni,
            ]

            longitud_maxima = max(map(len, todas_listas))

            listas_rellenadas = [
                lista + [None] * (longitud_maxima - len(lista))
                for lista in todas_listas
            ]

            lista_DOC = listas_rellenadas[0]
            lista_tarea = listas_rellenadas[1]
            lista_Client = listas_rellenadas[2]
            lista_Descript = listas_rellenadas[3]
            lista_dir = listas_rellenadas[4]
            lista_CAV = listas_rellenadas[5]
            lista_Cap_opera = listas_rellenadas[6]
            lista_atributo = listas_rellenadas[7]
            lista_tecnico = listas_rellenadas[8]
            lista_status = listas_rellenadas[9]
            lista_entrega_etb = listas_rellenadas[10]
            lista_asignado = listas_rellenadas[11]
            lista_plan_inicio = listas_rellenadas[12]
            lista_en_camino = listas_rellenadas[13]
            lista_En_curso = listas_rellenadas[14]
            lista_Final_x_Confirmar_ETB = listas_rellenadas[15]
            lista_Completada = listas_rellenadas[16]
            tiempo_muerto_llegada = listas_rellenadas[17]
            lista_tiempo_muerto_ejecucion = listas_rellenadas[18]
            lista_descripo_time_muert = listas_rellenadas[19]
            lista_staff_dni = listas_rellenadas[20]

        except Exception as e:
            print(f"Error processing task {task['results'][0]['code']}: {e}")
            continue

    data = {
        "documenter": listas_rellenadas[0],
        "code": listas_rellenadas[1],
        "client": listas_rellenadas[2],
        "description": listas_rellenadas[3],
        "address": listas_rellenadas[4],
        "cav_id": listas_rellenadas[5],
        "operational_category": listas_rellenadas[6],
        "request_activity": listas_rellenadas[7],
        "assigned_staff": listas_rellenadas[8],
        "status": listas_rellenadas[9],
        "date_delivery_time": listas_rellenadas[10],
        "assigned_time": listas_rellenadas[11],
        "scheduled_time": listas_rellenadas[12],
        "way_time": listas_rellenadas[13],
        "arrival_time": listas_rellenadas[14],
        "final_time": listas_rellenadas[15],
        "confirmation_time": listas_rellenadas[16],
        "arrival_dead_time": listas_rellenadas[17],
        "execution_dead_time": listas_rellenadas[18],
        "observation_dead_time": listas_rellenadas[19],
        "root_cause": "",
        "attributable": "",
        "resolutioncategory_2ps": "",
        "customer_waiting": "",
        "service_type": "",
        "staff_dni": listas_rellenadas[20],
    }

    df = pd.DataFrame(data)
    nombre_archivo = f"archivo_excel_{fecha_desde}-{fecha_hasta}.xlsx"
    # Guardar el DataFrame en un archivo Excel
    df.to_excel(nombre_archivo, index=False)

    print("finaliza proceso")


def obtener_rango_fechas():
    fecha_inicial = calendario_inicial.get_date()
    fecha_final = calendario_final.get_date()
    resultado_label.config(text=f"Rango seleccionado: {fecha_inicial} - {fecha_final}")
    work1(fecha_inicial, fecha_final)


# Crear la ventana principal
ventana = tk.Tk()
ventana.title("Seleccionar Rango de Fechas")

# Crear cuadros de fechas
calendario_inicial = DateEntry(
    ventana, date_pattern="yyyy-mm-dd", label="Fecha Inicial"
)
calendario_inicial.grid(row=0, column=0, padx=10, pady=10)

calendario_final = DateEntry(ventana, date_pattern="yyyy-mm-dd", label="Fecha Final")
calendario_final.grid(row=1, column=0, padx=10, pady=10)

# Botón para obtener el rango de fechas seleccionado
boton_obtener_rango = tk.Button(
    ventana, text="Obtener Rango", command=obtener_rango_fechas
)
boton_obtener_rango.grid(row=2, column=0, pady=10)

# Etiqueta para mostrar el resultado
resultado_label = tk.Label(ventana, text="")
resultado_label.grid(row=3, column=0, pady=10)

# Iniciar el bucle de eventos
ventana.mainloop()
