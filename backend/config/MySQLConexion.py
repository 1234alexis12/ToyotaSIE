import os
import socket
import mysql.connector
from mysql.connector import Error
from servicios.MetricsService import DB_QUERIES_TOTAL

# Modulo de configuracion y gestion de conexiones Master (Escritura) y Slave (Lectura)
class ConexionBD:
    # Parametros del nodo Maestro (Escritura transaccional)
    HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    USER = os.getenv('MYSQL_USER', 'root')
    PASSWORD = os.getenv('MYSQL_PASSWORD', '123456')
    DATABASE = os.getenv('MYSQL_DATABASE', 'toyota_db')
    PORT = int(os.getenv('MYSQL_PORT', 3307))

    # Parametros del nodo Esclavo / Read Replica (Consultas de lectura)
    SLAVE_HOST = os.getenv('MYSQL_SLAVE_HOST', '').strip()
    SLAVE_PORT = int(os.getenv('MYSQL_SLAVE_PORT', PORT))

    @classmethod
    def detectar_puerto_activo(cls, host=None, puerto_preferido=None):
        """Comprueba si el puerto objetivo de MySQL esta escuchando."""
        host_objetivo = host or cls.HOST
        puerto_base = puerto_preferido or cls.PORT

        # En contenedores Docker o hosts remotos se consulta directamente el puerto configurado
        if host_objetivo not in ('127.0.0.1', 'localhost'):
            puertos = [puerto_base]
        else:
            puertos = list(dict.fromkeys([puerto_base, 3306, 3307]))

        for p in puertos:
            try:
                with socket.create_connection((host_objetivo, p), timeout=0.5):
                    return p
            except (socket.timeout, ConnectionRefusedError, OSError):
                continue
        return None

    @classmethod
    def _conectar_nodo(cls, host, puerto_preferido):
        """Abre una conexion MySQL hacia el nodo especificado (Master o Slave)."""
        puerto_activo = cls.detectar_puerto_activo(host, puerto_preferido)
        if not puerto_activo:
            return None

        # Evita reintentos duplicados manteniendo compatibilidad en entorno local
        claves_a_probar = list(dict.fromkeys([cls.PASSWORD, '123456', 'root', 'Toyota2026!', '']))
        for pass_intento in claves_a_probar:
            try:
                conexion = mysql.connector.connect(
                    host=host,
                    user=cls.USER,
                    password=pass_intento,
                    database=cls.DATABASE,
                    port=puerto_activo,
                    autocommit=False,
                    connection_timeout=2
                )
                if conexion.is_connected():
                    return conexion
            except Error:
                continue

        return None

    @classmethod
    def obtener_conexion(cls):
        """Retorna conexion al nodo Maestro (Master) para operaciones de escritura."""
        conexion = cls._conectar_nodo(cls.HOST, cls.PORT)
        if conexion:
            DB_QUERIES_TOTAL.labels(nodo='master').inc()
        return conexion

    @classmethod
    def obtener_conexion_lectura(cls):
        """Retorna conexion al nodo Esclavo (Slave) para lectura; cae a Master si no esta disponible."""
        if cls.SLAVE_HOST:
            conexion_slave = cls._conectar_nodo(cls.SLAVE_HOST, cls.SLAVE_PORT)
            if conexion_slave:
                DB_QUERIES_TOTAL.labels(nodo='slave').inc()
                return conexion_slave
        return cls.obtener_conexion()

    @classmethod
    def _inspeccionar_nodo(cls, host, port):
        """Consulta server_id y modo read_only de un nodo MySQL para diagnostico."""
        conexion = cls._conectar_nodo(host, port)
        if not conexion:
            return {'conectado': False, 'host': host, 'puerto': port}
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT @@server_id AS server_id, @@read_only AS read_only, @@super_read_only AS super_read_only")
            info = cursor.fetchone()
            cursor.close()
            conexion.close()
            return {
                'conectado': True,
                'host': host,
                'puerto': port,
                'server_id': int(info['server_id']),
                'read_only': bool(info['read_only']),
                'super_read_only': bool(info['super_read_only'])
            }
        except Error:
            conexion.close()
            return {'conectado': False, 'host': host, 'puerto': port}

    @classmethod
    def obtener_estado_replicacion(cls):
        """Retorna el diagnostico de conectividad tanto del nodo Master como del Slave."""
        master_info = cls._inspeccionar_nodo(cls.HOST, cls.PORT)
        slave_info = (
            cls._inspeccionar_nodo(cls.SLAVE_HOST, cls.SLAVE_PORT)
            if cls.SLAVE_HOST
            else {'conectado': False, 'host': None, 'puerto': None}
        )
        return {'master': master_info, 'slave': slave_info}

    @classmethod
    def probar_conexion(cls):
        # Metodo de diagnostico para validar conectividad con el servidor MySQL Maestro
        conexion = cls.obtener_conexion()
        if conexion:
            conexion.close()
            return True
        return False
