import jpype
import jpype.imports
import os
import json
import time
from datetime import datetime

# ---------------- CONFIGURACIÓN ----------------
host_port= input("Favor ingrese host:port = ")
JMX_URL = f"service:jmx:rmi:///jndi/rmi://{host_port}/jmxrmi"
CARPETA_LOGS = "logs_mbeans"
DOMINIO_FILTRO = input("Favor ingrese el dominio = ")   # Ejemplo: "java.nio" o None para todos
INTERVALO_SEGUNDOS = int(input("Favor ingrese el intervalo = ")) # ⏱ Intervalo entre capturas
# ------------------------------------------------


def asegurar_directorio(directorio):
    if not os.path.exists(directorio):
        os.makedirs(directorio)


def safe_str(s):
    if s is None:
        return None
    try:
        return (
            str(s)
            .replace('\\', '\\\\')
            .replace('"', '\\"')
            .replace('\n', '\\n')
            .replace('\r', '\\r')
        )
    except Exception as e:
        return f"<no convertible: {e}>"


def serialize_mbean(obj):
    try:
        if obj is None:
            return None
        elif isinstance(obj, (bool, int, float)):
            return obj
        elif isinstance(obj, str):
            return safe_str(obj)
        elif isinstance(obj, dict):
            return {safe_str(str(k)): serialize_mbean(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple, set)):
            return [serialize_mbean(x) for x in obj]
        else:
            # objetos Java complejos → string seguro
            return safe_str(obj)
    except Exception as e:
        return f"<no convertible: {e}>"


def guardar_json(datos):
    asegurar_directorio(CARPETA_LOGS)
    ahora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ruta = os.path.join(CARPETA_LOGS, f"mbeans_{ahora}.json")
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"[{ahora}] ✅ Log JSON guardado en {ruta}")
    except Exception as e:
        print(f"❌ Error guardando JSON: {e}")


def iniciar_jvm():
    if not jpype.isJVMStarted():
        print("Iniciando JVM desde Python...")
        jvm_path = r"C:\Program Files\Java\jdk-24\bin\server\jvm.dll"
        jpype.startJVM(jvm_path, "--enable-native-access=ALL-UNNAMED", convertStrings=False)


def conectar_remoto():
    from javax.management.remote import JMXServiceURL, JMXConnectorFactory
    try:
        url = JMXServiceURL(JMX_URL)
        jmxc = JMXConnectorFactory.connect(url, None)
        return jmxc.getMBeanServerConnection()
    except Exception as e:
        print(f"❌ Error conectando JMX remoto: {e}")
        return None


def capturar_mbeans(mbsc):
    try:
        from javax.management import ObjectName

        if DOMINIO_FILTRO:
            filtro = ObjectName(f"{DOMINIO_FILTRO}:*")
            mbeans = mbsc.queryMBeans(filtro, None)
        else:
            mbeans = mbsc.queryMBeans(None, None)

        datos = {}
        for mbean in mbeans:
            # Convertir explícitamente el nombre a string
            name = str(mbean.getObjectName())
            try:
                info = mbsc.getMBeanInfo(mbean.getObjectName())
                mbean_data = {
                    'attributes': {},
                    'operations': {},
                    'notifications': []
                }

                # Capturar atributos
                for attr in info.getAttributes():
                    # Asegurar que el nombre del atributo sea string
                    attr_name = str(attr.getName())
                    try:
                        value = mbsc.getAttribute(mbean.getObjectName(), attr_name)
                        mbean_data['attributes'][attr_name] = serialize_mbean(value)
                    except:
                        mbean_data['attributes'][attr_name] = "<no accesible>"

                # Capturar operaciones
                for operation in info.getOperations():
                    # Asegurar que el nombre de la operación sea string
                    op_name = str(operation.getName())
                    op_data = {
                        'name': op_name,
                        'return_type': str(operation.getReturnType()),
                        'parameters': [{
                            'name': str(param.getName()),
                            'type': str(param.getType())
                        } for param in operation.getSignature()]
                    }
                    mbean_data['operations'][op_name] = serialize_mbean(op_data)

                # Capturar notificaciones
                for notification in info.getNotifications():
                    notif_data = {
                        'name': str(notification.getName()),
                        'description': str(notification.getDescription()),
                        'types': serialize_mbean([str(t) for t in notification.getNotifTypes()])
                    }
                    mbean_data['notifications'].append(serialize_mbean(notif_data))

                datos[str(name)] = mbean_data
            except:
                datos[str(name)] = "<no accesible>"

        return datos
    except Exception as e:
        print(f"❌ Error capturando MBeans: {e}")
        return {}


def main():
    iniciar_jvm()
    print("Conectando a JMX remoto...")
    mbsc = conectar_remoto()
    if not mbsc:
        return

    print(f"Iniciando captura de MBeans cada {INTERVALO_SEGUNDOS} segundos... (Ctrl + C para detener)")
    try:
        while True:
            datos = capturar_mbeans(mbsc)
            print(f"Total MBeans capturados: {len(datos)}")
            guardar_json(datos)
            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        print("\n🛑 Captura interrumpida por el usuario.")
    finally:
        if jpype.isJVMStarted():
            jpype.shutdownJVM()


if __name__ == "__main__":
    main()
