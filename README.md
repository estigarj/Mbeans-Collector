# MBeans Collector

Herramienta en Python para capturar y guardar MBeans de JVMs locales o remotas en archivos JSON.

## Archivos principales
- mbeans_remote.py:  captura MBeans desde JMX remoto. 
- mbeans_local.py: captura MBeans de una JVM local (attach). 

## Requisitos
- Python 3.8+
- Java JDK completo (necesario jvm.dll para JPype)
- Dependencias Python:
  - jpype (pip install jpype1)
  - opcional para jmx remoto alternativo: jmxquery (pip install jmxquery)

## Configuración rápida

### Para captura remota (mbeans_remote.py):
1. Configurar la JVM objetivo para permitir conexiones JMX:
   ```bash
   java -Dcom.sun.management.jmxremote 
        -Dcom.sun.management.jmxremote.port=9000
        -Dcom.sun.management.jmxremote.ssl=false
        -Dcom.sun.management.jmxremote.authenticate=false
   ```
2. Verificar que el JVM_PATH apunte correctamente al jvm.dll:
   ```python
   JVM_PATH = r"C:\Program Files\Java\jdk-24\bin\server\jvm.dll"
   ```

3. Al ejecutar el script se solicitará:
   - host:port (ejemplo: localhost:9000)
   - dominio para filtrar (ejemplo: java.lang)
   - intervalo de captura en segundos
   - credenciales (opcional)

### Para captura local (mbeans_local.py):
1. Verificar que el JVM_PATH apunte correctamente al jvm.dll:
   ```python
   JVM_PATH = r"C:\Program Files\Java\jdk-24\bin\server\jvm.dll"
   ```

2. Al ejecutar el script se solicitará:
   - PID de la JVM local
   - dominio para filtrar (ejemplo: java.lang)
   - intervalo de captura en segundos

### Salida
- Los archivos JSON se guardan en la carpeta `logs_mbeans/`
- Formato: `mbeans_YYYY-MM-DD_HH-MM-SS.json`
- Incluye atributos, operaciones y notificaciones de los MBeans
