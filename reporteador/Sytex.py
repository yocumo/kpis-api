import requests
import json
import traceback

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Token 092c72cfaf87410971e74c640fbe9d53f8c1eda6",
    "Organization": "164"
    }

mensajes_errores = []

#instalador de paquetes "pip install -r paquetes.txt"

def RunApi(URL):

    api_url = URL
    try:
    # Realiza una solicitud GET a la API
        response = requests.get(api_url,headers=headers)

        if response.status_code in [200,201]:
            return response.json()
        else:
            data = response.json()
            print("Datos de la API:", data)
            mensajes_errores.append("Datos de la API: ", data)
            return ("Datos de la API: ", data)
               
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud a la API: {str(e)}")
        mensajes_errores.append(f"Error al realizar la solicitud a la API: {str(e)}")
        return (f"Error al realizar la solicitud a la API: {str(e)}")
        
    except Exception as e:
        mensajes_errores.append(f"Ocurrió un error: {str(e)}")
        print(f"Ocurrió un error: {str(e)}")
        return (f"Ocurrió un error: {str(e)}")

def FindUser(User):
    User = str(User)
    Userurl = "https://app.sytex.io/api/staff/?q="+User
    User = RunApi(Userurl)
    try :
        if User['results'][0]['id']:
            return User['results'][0]['id']
        else:
            print("Usuario no existe "+User)
            mensajes_errores.append("Usuario no existe "+User)
            
            with open("Logs_excel\\log.txt", "a") as errores_file:
                for mensaje_error in mensajes_errores:
                    errores_file.write(mensaje_error + "\n")
                    
    except Exception as e:
        print(f"error : {str(e)}"+ " al encontrar al usuario "+ str(User))
        mensajes_errores.append(f"error : {str(e)}"+ " al encontrar al usuario "+ str(User))
        
        with open("Logs_excel\\log.txt", "a") as errores_file:
            for mensaje_error in mensajes_errores:
                errores_file.write(mensaje_error + "\n")

def Change_asignement(task_id,id_user):
    ChangeStatusurl = "https://app.sytex.io/api/import/TaskImport/go/"
    
    TaskStatus={
    "code": task_id,
    "assigned_staff":id_user,
    "break_assignment":"force",
    }
    payload = json.dumps(TaskStatus)
    
    try:
        response = requests.post(ChangeStatusurl, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print(f"reasignacion exitosa de la tarea : {str(task_id)} ")
            #return(f"reasignacion exitosa de la tarea : {str(task_id)} ")
        else:
            data = response.json()
            print(f"cambios de asignación de la tarea: {str(task_id)} con el usuario {id_user} y con data: {data}")
            mensajes_errores.append(f"cambios de asignación de la tarea: {str(task_id)} con el usuario {id_user} y con data: {data}")
            
            with open("Logs_excel\\log.txt", "a") as errores_file:
                for mensaje_error in mensajes_errores:
                    errores_file.write(mensaje_error + "\n")
            
    except Exception as e:
        print(f"Error en la solicitud: Change_asignement {str(e)}")
        #return(f"Error en la solicitud: {str(e)}")
        mensajes_errores.append(f"Error en la solicitud: Change_asignement {str(e)}, al cambiar la asignacion de la tareas {str(task_id)}")
        
        with open("Logs_excel\\log.txt", "a") as errores_file:
            for mensaje_error in mensajes_errores:
                errores_file.write(mensaje_error + "\n")
              
def FindClient(Cliente):
    try:
        Cliente = str(Cliente)
        Clienturl = "https://app.sytex.io/api/client/?q="+Cliente
        Cliente = RunApi(Clienturl)
        return Cliente['results'][0]['id']
    except Exception as e:
        print(f"error : {str(e)}"+ " al encontrar al cliente "+ str(Cliente))
        mensajes_errores.append(f"error : {str(e)}"+ " al encontrar al cliente "+ str(Cliente))
        #return(f"error : {str(e)}"+ " al encontrar al cliente "+ str(Cliente))
    
        with open("Logs_excel\\log.txt", "a") as errores_file:
            for mensaje_error in mensajes_errores:
                errores_file.write(mensaje_error + "\n")

def ClientExists(clientname):
    clientname = clientname[:50]
    Clienturl = "https://app.sytex.io/api/client/?q=" + clientname
    return RunApi(Clienturl)

def FindTask(tramite_id):
    Taskurl = "https://app.sytex.io/api/task/reduced/?code=" + str(tramite_id)
    return RunApi(Taskurl)

def CreateTask(task):
    url = "https://app.sytex.io/api/wizard_trigger/Task_Clic_Hogares/trigger/"
    mensajes_errores = []
    payload = json.dumps(task)

    try:
        response = requests.post(url, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print("tarea creada exitosamente "+task['taskcode'])
        else:
            Tass = FindTask(task['taskcode'])
            if Tass['results'][0]['code'] == task['taskcode'] :
                print("tarea ya existe")
            else:
                data = response.json()
                print("Datos de la API:", data)
                print("tarea no existe "+task['taskcode'])
                mensajes_errores.append(f"Error al crear la tarea para el ID: {task['taskcode']}")
                mensajes_errores.append("Datos de la API:", data)
                
                with open("Logs_excel\\log.txt", "a") as errores_file:
                    for mensaje_error in mensajes_errores:
                        errores_file.write(mensaje_error + "\n")
                
            print(f"Error en la solicitud en la tarea {task['taskcode']}. Código de estado: {response.status_code}")
            mensajes_errores.append(f"Error en la solicitud en la tarea {task['taskcode']}. Código de estado: {response.status_code}")
            
            with open("Logs_excel\\log.txt", "a") as errores_file:
                for mensaje_error in mensajes_errores:
                    errores_file.write(mensaje_error + "\n")

    except Exception as e:
        print(f"Error en la solicitud: CreateTask {str(e)}")
        mensajes_errores.append(f"Error en la solicitud: CreateTask {str(e)}")
        tb = traceback.format_exc()
        print("Ocurrió un error en la siguiente línea:",tb)
        #print(tb)
        
        #mensajes_errores.append("Error en la línea:", relevant_line)
        with open("Logs_excel\\log.txt", "a") as errores_file:
            for mensaje_error in mensajes_errores:
                errores_file.write(mensaje_error + "\n")

def CreateTaskB2B(task):
    url = "https://app.sytex.io/api/wizard_trigger/Task_SIGC_B2B/trigger/"
    mensajes_errores = []
    payload = json.dumps(task)
    
    try:
        response = requests.post(url, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print("tarea creada exitosamente "+task['taskcode'])
        else:
            Tass = FindTask(task['taskcode'])
            if Tass['results'][0]['code'] == task['taskcode'] :
                print("tarea ya existe")
            else:
                data = response.json()
                print("Datos de la API:", data)
                print("tarea no existe "+task['taskcode'])
                mensajes_errores.append(f"Error al crear la tarea para el ID: {task['taskcode']}")
                mensajes_errores.append("Datos de la API:", data)
                
                with open("Logs_excel\\log.txt", "a") as errores_file:
                    for mensaje_error in mensajes_errores:
                        errores_file.write(mensaje_error + "\n")
                
            print(f"Error en la solicitud en la tarea {task['taskcode']}. Código de estado: {response.status_code}")
            mensajes_errores.append(f"Error en la solicitud en la tarea {task['taskcode']}. Código de estado: {response.status_code}")
            
            with open("Logs_excel\\log.txt", "a") as errores_file:
                for mensaje_error in mensajes_errores:
                    errores_file.write(mensaje_error + "\n")

    except Exception as e:
        print(f"Error en la solicitud: CreateTask {str(e)}")
        mensajes_errores.append(f"Error en la solicitud: CreateTask {str(e)}")
        tb = traceback.format_exc()
        print("Ocurrió un error en la siguiente línea:",tb)
        #print(tb)
        
        #mensajes_errores.append("Error en la línea:", relevant_line)
        with open("Logs_excel\\log.txt", "a") as errores_file:
            for mensaje_error in mensajes_errores:
                errores_file.write(mensaje_error + "\n")

def CreateClient(Cliente):

    CreateTaskurl = "https://app.sytex.io/api/client/"
    ClienteCorto = Cliente[:50]
    client={
        "code": ClienteCorto,
        "name": ClienteCorto,
        "organization": "164",
        }
    payload = json.dumps(client)

    try:
        response = requests.post(CreateTaskurl, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print(f"creacion exito del cliente : {Cliente}")
        else:
            if ClientExists(Cliente)['count'] == 1 :
                print("cliente ya existe")
            else:
                data = response.json()

                mensaje = 'Error en la solicitud al crear el cliente: '
                mensaje += (Cliente)
                mensaje += ', Datos de la API: '
                mensaje += (data)
                mensajes_errores.append(mensaje + '\n')
                print(mensaje)
                #print(f"Error en la solicitud al crear el cliente {client} . Código de estado: {response.status_code}")
                #mensajes_errores.append(f"Error en la solicitud al crear el cliente {client} . Código de estado: {response.status_code}")

                with open("Logs_excel\\log.txt", "a") as errores_file:
                        for mensaje_error in mensajes_errores:
                            errores_file.write(mensaje_error + "\n")
                        
    except Exception as e:
        print(f"Error en la solicitud: CreateClient {str(e)}")
        mensajes_errores.append(f"Error en la solicitud: CreateClient{str(e)}, al crear el cliente {str(Cliente)}")
        
        with open("Logs_excel\\log.txt", "a") as errores_file:
                    for mensaje_error in mensajes_errores:
                        errores_file.write(mensaje_error + "\n")

def Change_state(task_id):
    ChangeStatusurl = "https://app.sytex.io/api/import/TaskImport/go/"
    
    TaskStatus={
    "code": task_id,
    "status_step":"cancelada",
    "cancel_pending_documents":1,
    "status_history_comments":"Cancelar por cambio en sistema de informacion tigo"
    }
    payload = json.dumps(TaskStatus)

    try:
        response = requests.post(ChangeStatusurl, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print(f"cancelacion exitosa de la tarea : {str(task_id)} ")
            #mensajes.append(f"creacion exito del cliente : {str(task_id)}")
        else:
            data = response.json()
            print("Datos de la API cambio de estado :", data)
            mensajes_errores.append(f"Datos de la API cambio de estado :{str(data)}, en la tarea {str(task_id)}")
            
            with open("Logs_excel\\log.txt", "a") as errores_file:
                for mensaje_error in mensajes_errores:
                    errores_file.write(mensaje_error + "\n")
                    
    except Exception as e:
        print(f"Error en la solicitud: Change_state {str(e)}")
        mensajes_errores.append(f"Error en la solicitud: Change_state {str(e)}")
        with open("Logs_excel\\log.txt", "a") as errores_file:
            for mensaje_error in mensajes_errores:
                errores_file.write(mensaje_error + "\n")

def Change_asignement_hide(task_id):
    ChangeStatusurl = "https://app.sytex.io/api/import/TaskImport/go/"
    
    TaskStatus={
    "code": task_id,
    "assigned_staff":"SF-04250",
    "break_assignment":"force",
    }
    payload = json.dumps(TaskStatus)
    
    try:
        response = requests.post(ChangeStatusurl, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print(f"reasignacion exitosa tarea vacia : {str(task_id)} ")
            return(f"reasignacion exitosa tarea vacia : {str(task_id)} ")
        else:
            data = response.json()

            print(f"cambios de asignación de la tarea: {str(task_id)} y con data: {data}")
            return(f"cambios de asignación de la tarea: {str(task_id)} y con data: {data}")

    except Exception as e:
        print(f"Error en la solicitud: Change_asignement_hide {str(e)}")
        return(f"Error en la solicitud: Change_asignement_hide {str(e)}")

def FindTaskDoc(id):
    id = str(id)
    Taskurl = " https://app.sytex.io/api/taskdocument/?task="+id
    return RunApi(Taskurl)    

def MO_active(Id_OM):
    Id_OM = str(Id_OM)
    Taskurl = "https://app.sytex.io/api/simpleoperation/?q="+Id_OM
    return RunApi(Taskurl)

def MO_id(Id_OM):
    Id_OM = str(Id_OM)
    Taskurl = "https://app.sytex.io/api/simpleoperation/?task="+Id_OM
    return RunApi(Taskurl)

def trigger_add_MO(item):
    ChangeStatusurl = " https://app.sytex.io/api/import/SimpleOperationItemImport/go/"
    payload = json.dumps(item)

    try:
        response = requests.post(ChangeStatusurl, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print("añadido corecto de item: "+item['operation'])
            mensaje = 'añadido corecto de item: '
            mensaje += (item['operation'])            
            return True, mensaje
        else:
            data = response.json()
            
            print("Datos de la API:", data)
            if 'serial_number' in item:
                print(item['serial_number'])
            print(item['operation'])
            
            mensaje = 'Datos de la API: '
            mensaje += (str(data))
            if 'serial_number' in item:
                mensaje += (', Con Num Serie: ')
                mensaje += (str(item['serial_number']))
            mensaje += (', en la MO: ')
            mensaje += (str(item['operation']))
            
            return False , mensaje
    except Exception as e:
        print(f"Error:  {str(e)}")
        mensaje = 'Error: '
        mensaje += (str(e))
        mensaje += (', en la MO: ')
        mensaje += (str(item['operation']))
        return False, mensaje
            
def confirm_MO(MO_id):
    ConfirmMO = "https://app.sytex.io/api/import/SimpleOperationImport/go/"
    
    TaskStatus={
    "code": MO_id,
    "status_step":"Confirmada"
    }
    payload = json.dumps(TaskStatus)

    try:
        response = requests.post(ConfirmMO, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print("confirmar MO:",MO_id)
            return True
        else:
            data = response.json()
            mensaje = f"Datos de la API: {str(data)}"
            return mensaje
    except Exception as e:
        return f"Error en la solicitud: {str(e)}"
           
def verify_MO_mat(MO_id,cod_mat,cant_mat):
    MO_id= str(MO_id)
    Taskurl = "https://app.sytex.io/api/simpleoperation/"+MO_id
    dicc = {}
    h = RunApi(Taskurl)
    
    for i in h['simpleoperationitem_set']:
        dicc[i['material']['code']] = i['quantity']
        
    if cod_mat in dicc:
        h = str(dicc[cod_mat])
        if h  ==  cant_mat:
            return False
        else:
            return True
    else:
        return True       
       
def verify_MO_eq(MO_id,cod_eq,serial_eq):
    MO_id=str(MO_id)
    Taskurl = "https://app.sytex.io/api/simpleoperation/"+MO_id
    dicc = {}
    h = RunApi(Taskurl)
    
    for i in h['simpleoperationitem_set']:
        dicc[i['material']['code']] = i['serial_number']
        
    if cod_eq in dicc:
        h = str(dicc[cod_eq])
        if h  ==  serial_eq:
            return False
        else:
            return True
    else:
        return True
    
def create_MO(task_code,tipo):
    ChangeStatusMOurl = "https://app.sytex.io/api/simpleoperation/"
    
    if tipo == 2:
        TaskStatus={
        "operation_type":tipo,
        "task":task_code,
        #"source_location":origen,
        #"destination_location":destino,
        #"preparation_responsible":origen,
        "attributes":[501]
        }
        
    elif tipo == 1:
        TaskStatus={
        "operation_type":tipo,
        "entry_type":4,
        "task":task_code,
        #"preparation_responsible":origen,
        "attributes":[501]
        }
        
    payload = json.dumps(TaskStatus)
    
    try:
        response = requests.post(ChangeStatusMOurl, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print("creacion exitosa de la MO")
            data = response.json()
            #print("Datos de la API:", data)
            return data['code']

        else:
            data = response.json()
            print("Datos de la API:", data)
            print(f"Error en la solicitud. Código de estado: {response.status_code}")

    except Exception as e:
        print(f"Error en la solicitud: {str(e)}")
        return (f"Error en la solicitud: {str(e)}")   
    
def AsignementMO(code_MO,destino):
    ChangeStatusMOurl = "https://app.sytex.io/api/import/SimpleOperationImport/go/"
    
    TaskStatus={
    "code":code_MO,
    "preparation_responsible":destino
    }
    payload = json.dumps(TaskStatus)

    try:
        response = requests.post(ChangeStatusMOurl, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print("asignacion exitosa de la MO")
            data = response.json()
        else:
            data = response.json()
            print("Datos de la API:", data)
            print(f"Error en la solicitud. Código de estado: {response.status_code}")
    except Exception as e:
        print(f"Error en la solicitud: {str(e)}")
        return (f"Error en la solicitud: {str(e)}") 
 
def RunApiPACHT(URL,atribute):
    
    Task_attribute={
    "attributes":[]
    }
    
    Task_attribute['attributes'] = atribute
    
    payload = json.dumps(Task_attribute)
    api_url = URL
    
    try:
    # Realiza una solicitud GET a la API
        response = requests.patch(api_url,headers=headers,data=payload)
        data = response.json()
        if response.status_code in [200,201]:
            #print(response.json())
            print(response.status_code)        
        else:
            data = response.json()
            #print("Datos de la API:", data)
            print(response.status_code)
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud a la API: {str(e)}")
    except Exception as e:
        print(f"Ocurrió un error: {str(e)}") 
    
def find_fom_(id):
    id = str(id)
    Taskurl = f"https://app.sytex.io/api/task/971904/"
    
    Task_attribute={
    "attributes":[313]
    }
    return RunApiPACHT(Taskurl,Task_attribute) 
                      
def change_plan_date(id,fecha_actual):
    
    id = str(id)
    Taskurl = f"https://app.sytex.io/api/task/{id}/"

    Task_plan_date={
    "plan_date":str(fecha_actual)
    }  
                         
    return RunApiPACHT(Taskurl,Task_plan_date)

def task_atribute(id,atribute):
    id = str(id)
    Taskurl = f"https://app.sytex.io/api/task/{id}/"
    return RunApiPACHT(Taskurl,atribute)

def Get_task_atribute(id):
    id = str(id)
    Taskurl = f"https://app.sytex.io/api/task/{id}/"
    return RunApi(Taskurl)

def FindStock(id): 
    Taskurl = " https://app.sytex.io/api/materialstock/?q="+id
    return RunApi(Taskurl)

def create_MO_stock(origen,destino,task_code,tipo,Tipo_consumo):
    ChangeStatusMOurl = "https://app.sytex.io/api/simpleoperation/"
    
    TaskStatus={
    "operation_type":tipo,
    "task":task_code,
    "source_location":{"id": origen,"_class": "staff"},
    "destination_location":{"id": destino,"_class": "client"},
    "preparation_responsible":origen,
    "attributes":[Tipo_consumo]
    }
    
    payload = json.dumps(TaskStatus)
    
    try:
        response = requests.post(ChangeStatusMOurl, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print("creacion exitosa de la MO")
            data = response.json()
            print(data['code'])
            return data['code']

        else:
            data = response.json()
            print("Datos de la API:", data)
            print(f"Error en la solicitud. Código de estado: {response.status_code}")

    except Exception as e:
        print(f"Error en la solicitud: {str(e)}")
        return (f"Error en la solicitud: {str(e)}") 
    
def create_MO(task_code,tipo):
    ChangeStatusMOurl = "https://app.sytex.io/api/simpleoperation/"
    
    if tipo == 2:
        TaskStatus={
        "operation_type":tipo,
        "task":task_code,
        #"source_location":origen,
        #"destination_location":destino,
        #"preparation_responsible":origen,
        "attributes":[501]
        }
        
    elif tipo == 1:
        TaskStatus={
        "operation_type":tipo,
        "entry_type":4,
        "task":task_code,
        #"preparation_responsible":origen,
        "attributes":[501]
        }
        
    payload = json.dumps(TaskStatus)
    
    try:
        response = requests.post(ChangeStatusMOurl, headers=headers,data=payload)

        if response.status_code in [200,201]:
            print("creacion exitosa de la MO")
            data = response.json()
            #print("Datos de la API:", data)
            return data['code']

        else:
            data = response.json()
            print("Datos de la API:", data)
            print(f"Error en la solicitud. Código de estado: {response.status_code}")

    except Exception as e:
        print(f"Error en la solicitud: {str(e)}")
        return (f"Error en la solicitud: {str(e)}") 
    
def RunApiPACHT(URL,atribute):
    
    Task_attribute={
    "attributes":[]
    }
    
    Task_attribute['attributes'] = atribute
    
    payload = json.dumps(Task_attribute)
    api_url = URL
    
    try:
    # Realiza una solicitud GET a la API
        response = requests.patch(api_url,headers=headers,data=payload)
        data = response.json()
        if response.status_code in [200,201]:
            #print(response.json())
            print(response.status_code)        
        else:
            data = response.json()
            #print("Datos de la API:", data)
            print(response.status_code)
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud a la API: {str(e)}")
    except Exception as e:
        print(f"Ocurrió un error: {str(e)}")

def Get_task_atribute(id):
    id = str(id)
    Taskurl = f"https://app.sytex.io/api/task/{id}/"
    return RunApi(Taskurl)

def task_atribute(id,atribute):
    id = str(id)
    Taskurl = f"https://app.sytex.io/api/task/{id}/"
    return RunApiPACHT(Taskurl,atribute)
 
def Findmaterialstock(n):
    n=str(n)
    Taskurl = " https://app.sytex.io/api/materialstock/?q="+n
    return RunApi(Taskurl)
