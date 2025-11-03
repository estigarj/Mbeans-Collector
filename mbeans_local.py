import jpype
import jpype.imports
from jpype.types import *
import json
import time
from datetime import datetime
import os

# ===========================
# CONFIGURACIÓN
# ===========================
# Local (PID)
LOCAL_PID = input("Favor ingrese el PID = ")  # Reemplazar con tu PID local
INTERVALO = int(input("Favor ingrese el intervalo = "))           # Segundos entre capturas

# Ruta al jvm.dll del JDK completo
JVM_PATH = r"C:\Program Files\Java\jdk-24\bin\server\jvm.dll"

# Carpeta donde se guardarán los logs JSON
CARPETA_LOGS = "logs_mbeans"

# ===========================
# UTILIDADES
# ===========================
def asegurar_directorio(path):
    if not os.path.exists(path):
        os.makedirs(path)

def java_to_py(obj):
    """
    Convierte objetos Java en tipos nativos de Python para JSON.
    """
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, dict):
        return {java_to_py(k): java_to_py(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [java_to_py(x) for x in obj]
    else:
        # Cualquier otro objeto (Java u otro), lo convertimos a string
        try:
            return str(obj)
        except:
            return "<no convertible>"


def imprimir_json(data):
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{ahora}] Captura de MBeans:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

def guardar_json(data):
    asegurar_directorio(CARPETA_LOGS)
    ahora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ruta = os.path.join(CARPETA_LOGS, f"mbeans_{ahora}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[{ahora}] Guardado log en {ruta}")

def iniciar_jvm():
    if not jpype.isJVMStarted():
        jpype.startJVM(JVM_PATH)
        print("JVM iniciada desde Python")

# ===========================
# FUNCIONES DE CAPTURA
# ===========================
def attach_local_mbeans(pid):
    from com.sun.tools.attach import VirtualMachine
    from javax.management.remote import JMXServiceURL, JMXConnectorFactory
    from javax.management import ObjectName

    vm = VirtualMachine.attach(pid)
    connector_address = vm.getAgentProperties().getProperty("com.sun.management.jmxremote.localConnectorAddress")

    if connector_address is None:
        agent_path = vm.getSystemProperties().getProperty("java.home") + "/lib/management-agent.jar"
        vm.loadAgent(agent_path)
        connector_address = vm.getAgentProperties().getProperty("com.sun.management.jmxremote.localConnectorAddress")

    url = JMXServiceURL(connector_address)
    connector = JMXConnectorFactory.connect(url)
    mbsc = connector.getMBeanServerConnection()

    mbeans = {}
    for name in mbsc.queryNames(None, None):
        try:
            info = mbsc.getMBeanInfo(name)
            attrs = {}
            for attr in info.getAttributes():
                try:
                    val = mbsc.getAttribute(name, attr.getName())
                    attrs[attr.getName()] = val
                except:
                    attrs[attr.getName()] = "<no accesible>"
            mbeans[name.getCanonicalName()] = attrs
        except:
            mbeans[str(name)] = "<no accesible>"

    connector.close()
    vm.detach()
    return mbeans

def jmx_remote_mbeans(jmx_url):
    try:
        from jmxquery import JMXConnection, JMXQuery
    except ImportError:
        raise ImportError("Para capturar JVM remota necesitas instalar jmxquery: pip install jmxquery")

    conn = JMXConnection(jmx_url)
    queries = [JMXQuery("*:*")]
    results = conn.query(queries)

    mbeans = {}
    for r in results:
        nombre = r.mBeanName
        attr = r.attribute
        valor = str(r.value)
        if nombre not in mbeans:
            mbeans[nombre] = {}
        mbeans[nombre][attr] = valor
    return mbeans

# ===========================
# LOOP PRINCIPAL
# ===========================
if __name__ == "__main__":
    iniciar_jvm()
    print("Iniciando captura de MBeans...\n")

    while True:
        try:
            if LOCAL_PID:
                datos = attach_local_mbeans(LOCAL_PID)
            elif JMX_URL:
                datos = jmx_remote_mbeans(JMX_URL)
            else:
                raise Exception("No configurado LOCAL_PID ni JMX_URL")

            # Convertir objetos Java a tipos nativos
            datos_py = java_to_py(datos)

            # Imprimir en consola
            imprimir_json(datos_py)

            # Guardar en disco
            guardar_json(datos_py)

            time.sleep(INTERVALO)

        except KeyboardInterrupt:
            print("\n💡 Captura finalizada por usuario")
            break
        except Exception as e:
            print(f"❌ Error capturando MBeans: {e}")
            time.sleep(INTERVALO)
