import os
import socket
import mysql.connector
from mysql.connector import Error

# Modulo de configuracion y gestion de la conexion a la base de datos MySQL
class ConexionBD:
    # Parametros de conexion con deteccion automatica de puertos y contraseñas
    HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    USER = os.getenv('MYSQL_USER', 'root')
    PASSWORD = os.getenv('MYSQL_PASSWORD', '123456')
    DATABASE = os.getenv('MYSQL_DATABASE', 'toyota_db')
    PORT = int(os.getenv('MYSQL_PORT', 3307))

    @classmethod
    def detectar_puerto_activo(cls):
        # Comprueba si el puerto principal o alternativo de MySQL esta escuchando
        puertos = [cls.PORT, 3306, 3307]
        for p in puertos:
            try:
                with socket.create_connection((cls.HOST, p), timeout=0.15):
                    return p
            except (socket.timeout, ConnectionRefusedError, OSError):
                continue
        return None

    @classmethod
    def obtener_conexion(cls):
        # Detecta el puerto de MySQL activo en la maquina local
        puerto_activo = cls.detectar_puerto_activo()
        if not puerto_activo:
            return None

        # Lista de claves comunes para compatibilidad entre las computadoras del equipo
        claves_a_probar = [cls.PASSWORD, '123456', 'root', 'Toyota2026!', '']
        for pass_intento in claves_a_probar:
            try:
                conexion = mysql.connector.connect(
                    host=cls.HOST,
                    user=cls.USER,
                    password=pass_intento,
                    database=cls.DATABASE,
                    port=puerto_activo,
                    autocommit=False,
                    connection_timeout=1
                )
                if conexion.is_connected():
                    return conexion
            except Error:
                continue

        return None

    @classmethod
    def probar_conexion(cls):
        # Metodo de diagnostico para validar conectividad con el servidor MySQL
        conexion = cls.obtener_conexion()
        if conexion:
            conexion.close()
            return True
        return False
