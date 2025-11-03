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
