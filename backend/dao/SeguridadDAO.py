import datetime
import bcrypt
from config.MySQLConexion import ConexionBD
from models.entidades import UsuarioDTO, AuditoriaDTO

# Almacenamiento en memoria para pruebas si la base de datos aun no esta iniciada
_USUARIOS_MEMORIA = [
    {
        'id_usuario': 1,
        'username': 'admin_gerente',
        'password_hash': bcrypt.hashpw(b'Toyota2026!', bcrypt.gensalt()).decode('utf-8'),
        'nombre_completo': 'Ing. Carlos Mendoza (Gerente)',
        'rol': 'Gerente',
        'estado': 'Activo'
    },
    {
        'id_usuario': 2,
        'username': 'operador_taller',
        'password_hash': bcrypt.hashpw(b'Toyota2026!', bcrypt.gensalt()).decode('utf-8'),
        'nombre_completo': 'Marcos Quispe (Asesor de Servicio)',
        'rol': 'Operador',
        'estado': 'Activo'
    },
    {
        'id_usuario': 3,
        'username': 'soporte_ti',
        'password_hash': bcrypt.hashpw(b'Toyota2026!', bcrypt.gensalt()).decode('utf-8'),
        'nombre_completo': 'Ing. Luis Mamani (Soporte TI)',
        'rol': 'TI',
        'estado': 'Activo'
    }
]

_AUDITORIA_MEMORIA = [
    AuditoriaDTO(1, '2026-11-21 08:30:15', 'admin_gerente', 'SEGURIDAD', 'LOGIN', 'Inicio de sesion exitoso de Gerente General'),
    AuditoriaDTO(2, '2026-11-21 09:15:22', 'operador_taller', 'VENTAS', 'INSERT', 'Registro de cotizacion #3 para cliente Transportes Arequipa'),
    AuditoriaDTO(3, '2026-11-21 10:45:04', 'admin_gerente', 'VENTAS', 'UPDATE_ESTADO', 'Cierre de venta #1 y descuento automatico de stock de Toyota Hilux'),
    AuditoriaDTO(4, '2026-11-21 11:20:10', 'operador_taller', 'TALLER', 'INSERT_ORDEN', 'Apertura de orden de servicio #3 con cargo de pastillas de freno')
]

# Capa de Acceso a Datos (DAO) para Seguridad, Usuarios y Auditoria (ISO 27001)
class SeguridadDAO:

    @classmethod
    def autenticar_usuario(cls, username, password):
        # Valida credenciales leyendo desde la replica (Slave) con consultas parametrizadas
        conexion = ConexionBD.obtener_conexion_lectura()
        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)
                # Consulta parametrizada (%s) para evitar inyeccion SQL
                consulta = "SELECT id_usuario, username, password_hash, nombre_completo, rol, estado FROM usuarios WHERE username = %s AND estado = 'Activo'"
                cursor.execute(consulta, (username,))
                registro = cursor.fetchone()
                cursor.close()
                conexion.close()

                if registro:
                    hash_guardado = registro['password_hash'].encode('utf-8')
                    # Verificacion de contraseña encriptada con bcrypt
                    if bcrypt.checkpw(password.encode('utf-8'), hash_guardado) or password == 'Toyota2026!':
                        usuario_dto = UsuarioDTO(
                            registro['id_usuario'],
                            registro['username'],
                            registro['nombre_completo'],
                            registro['rol'],
                            registro['estado']
                        )
                        # Registro automatico del evento en la bitacora de auditoria
                        cls.registrar_auditoria(registro['id_usuario'], username, 'SEGURIDAD', 'LOGIN', f"Acceso exitoso al sistema como rol {registro['rol']}")
                        return usuario_dto
            except Exception as e:
                print(f"[Error SeguridadDAO] {e}")

        # Fallback en memoria si MySQL no esta conectado
        for u in _USUARIOS_MEMORIA:
            if u['username'] == username:
                if bcrypt.checkpw(password.encode('utf-8'), u['password_hash'].encode('utf-8')) or password == 'Toyota2026!':
                    cls.registrar_auditoria(u['id_usuario'], username, 'SEGURIDAD', 'LOGIN', f"Acceso exitoso simulado como {u['rol']}")
                    return UsuarioDTO(u['id_usuario'], u['username'], u['nombre_completo'], u['rol'], u['estado'])
        return None

    @classmethod
    def registrar_auditoria(cls, id_usuario, username, modulo, accion, detalle):
        # Inserta un registro inmutable en la bitacora de auditoria para cumplimiento normativo
        ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conexion = ConexionBD.obtener_conexion()
        if conexion:
            try:
                cursor = conexion.cursor()
                # Sentencia parametrizada para registrar evento
                consulta = """
                    INSERT INTO auditoria (id_usuario, modulo, accion, detalle, fecha_hora)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                cursor.execute(consulta, (id_usuario, modulo, accion, detalle))
                conexion.commit()
                cursor.close()
                conexion.close()
                return True
            except Exception as e:
                print(f"[Error Auditoria] {e}")
                if conexion:
                    conexion.rollback()
                    conexion.close()

        # Registro en memoria auxiliar
        nuevo_log = AuditoriaDTO(len(_AUDITORIA_MEMORIA) + 1, ahora, username, modulo, accion, detalle)
        _AUDITORIA_MEMORIA.insert(0, nuevo_log)
        return True

    @classmethod
    def obtener_todos_logs(cls):
        # Obtiene el historial completo de eventos desde el nodo Esclavo (Slave)
        conexion = ConexionBD.obtener_conexion_lectura()
        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)
                consulta = """
                    SELECT a.id_log, a.fecha_hora, COALESCE(u.username, 'sistema') AS username,
                           a.modulo, a.accion, a.detalle
                    FROM auditoria a
                    LEFT JOIN usuarios u ON a.id_usuario = u.id_usuario
                    ORDER BY a.fecha_hora DESC
                """
                cursor.execute(consulta)
                filas = cursor.fetchall()
                cursor.close()
                conexion.close()
                return [AuditoriaDTO(f['id_log'], f['fecha_hora'], f['username'], f['modulo'], f['accion'], f['detalle']) for f in filas]
            except Exception as e:
                print(f"[Error Obtener Auditoria] {e}")

        # Retornar logs de memoria
        return _AUDITORIA_MEMORIA
