import os
import socket
import mysql.connector
from mysql.connector import Error

# Modulo de configuracion y gestion de la conexion a la base de datos MySQL
class ConexionBD:
    # Parametros de conexion con soporte para variables de entorno
    HOST = os.getenv('MYSQL_HOST', 'localhost')
    USER = os.getenv('MYSQL_USER', 'root')
    PASSWORD = os.getenv('MYSQL_PASSWORD', 'root')
    DATABASE = os.getenv('MYSQL_DATABASE', 'toyota_db')
    PORT = int(os.getenv('MYSQL_PORT', 3306))

    @classmethod
    def esta_puerto_abierto(cls):
        # Comprobacion rapida de socket para verificar si el servidor MySQL esta escuchando
        try:
            with socket.create_connection((cls.HOST, cls.PORT), timeout=0.2):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    @classmethod
    def obtener_conexion(cls):
        # Verifica el puerto antes de conectar para no demorar si MySQL aun no esta levantado
        if not cls.esta_puerto_abierto():
            return None

        # Establece y retorna una conexion activa a MySQL con cursores en formato diccionario
        try:
            conexion = mysql.connector.connect(
                host=cls.HOST,
                user=cls.USER,
                password=cls.PASSWORD,
                database=cls.DATABASE,
                port=cls.PORT,
                autocommit=False,
                connection_timeout=2
            )
            if conexion.is_connected():
                return conexion
        except Error as e:
            # Notifica en consola si el servicio MySQL aun no esta iniciado
            print(f"[Aviso BD] Error al conectar a MySQL ({e}). Usando capa de persistencia simulada.")
            return None

    @classmethod
    def probar_conexion(cls):
        # Metodo de diagnostico para validar conectividad con el servidor MySQL
        if not cls.esta_puerto_abierto():
            return False
        conexion = cls.obtener_conexion()
        if conexion:
            conexion.close()
            return True
        return False
