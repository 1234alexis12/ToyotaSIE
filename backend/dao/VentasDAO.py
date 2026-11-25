import datetime
from config.MySQLConexion import ConexionBD
from models.entidades import ClienteDTO, VentaDTO
from dao.InventarioDAO import InventarioDAO
from dao.SeguridadDAO import SeguridadDAO

# Datos semilla de clientes en memoria
_CLIENTES_MEMORIA = [
    ClienteDTO(1, '20601234567', 'Minera Cerro Verde S.A.A.', '958123456', 'logistica@cerroverde.pe', 'Corporativo'),
    ClienteDTO(2, '45678912', 'Juan Perez Delgado', '959987654', 'jperez@gmail.com', 'Particular'),
    ClienteDTO(3, '20456789012', 'Transportes Arequipa Express S.A.C.', '954332211', 'flota@arequipaexpress.pe', 'Corporativo')
]

# Datos semilla de ventas en memoria
_VENTAS_MEMORIA = [
    VentaDTO(1, 1, 'Minera Cerro Verde S.A.A.', 1, 'Toyota Hilux 4x4 Doble Cabina SRX', 48500.00, 'Vendido', '2026-11-18'),
    VentaDTO(2, 2, 'Juan Perez Delgado', 2, 'Toyota Corolla Sedan 1.8 XEI', 24200.00, 'Cotizado', '2026-11-20'),
    VentaDTO(3, 3, 'Transportes Arequipa Express S.A.C.', 4, 'Toyota Yaris Sedan 1.5 GLI', 18900.00, 'Prospecto', '2026-11-21')
]

# Capa de Acceso a Datos (DAO) para Clientes y Marketing/Ventas
class VentasDAO:

    @classmethod
    def obtener_clientes(cls):
        # Obtiene la lista completa de clientes desde el nodo Esclavo (Slave)
        conexion = ConexionBD.obtener_conexion_lectura()
        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)
                consulta = "SELECT id_cliente, dni_ruc, nombre_razon, telefono, email, tipo_cliente FROM clientes ORDER BY nombre_razon ASC"
                cursor.execute(consulta)
                filas = cursor.fetchall()
                cursor.close()
                conexion.close()
                return [ClienteDTO(f['id_cliente'], f['dni_ruc'], f['nombre_razon'], f['telefono'], f['email'], f['tipo_cliente']) for f in filas]
            except Exception as e:
                print(f"[Error VentasDAO obtener_clientes] {e}")

        return _CLIENTES_MEMORIA

    @classmethod
    def crear_cliente(cls, cliente_dto):
        # Registra un nuevo cliente con verificacion de DNI o RUC
        conexion = ConexionBD.obtener_conexion()
        if conexion:
            try:
                cursor = conexion.cursor()
                consulta = """
                    INSERT INTO clientes (dni_ruc, nombre_razon, telefono, email, tipo_cliente)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(consulta, (
                    cliente_dto.dni_ruc,
                    cliente_dto.nombre_razon,
                    cliente_dto.telefono,
                    cliente_dto.email,
                    cliente_dto.tipo_cliente
                ))
                conexion.commit()
                cliente_dto.id_cliente = cursor.lastrowid
                cursor.close()
                conexion.close()
                return cliente_dto
            except Exception as e:
                print(f"[Error VentasDAO crear_cliente] {e}")
                if conexion:
                    conexion.rollback()
                    conexion.close()

        cliente_dto.id_cliente = len(_CLIENTES_MEMORIA) + 1
        _CLIENTES_MEMORIA.insert(0, cliente_dto)
        return cliente_dto

    @classmethod
    def obtener_ventas(cls):
        # Consulta transacciones de ventas desde el nodo Esclavo (Slave)
        conexion = ConexionBD.obtener_conexion_lectura()
        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)
                consulta = """
                    SELECT v.id_venta, v.id_cliente, c.nombre_razon AS cliente_nombre,
                           v.id_item, i.nombre_modelo AS vehiculo_nombre,
                           v.precio_total, v.estado, v.fecha
                    FROM ventas v
                    INNER JOIN clientes c ON v.id_cliente = c.id_cliente
                    INNER JOIN inventario i ON v.id_item = i.id_item
                    ORDER BY v.fecha DESC, v.id_venta DESC
                """
                cursor.execute(consulta)
                filas = cursor.fetchall()
                cursor.close()
                conexion.close()
                return [VentaDTO(f['id_venta'], f['id_cliente'], f['cliente_nombre'], f['id_item'], f['vehiculo_nombre'], f['precio_total'], f['estado'], f['fecha']) for f in filas]
            except Exception as e:
                print(f"[Error VentasDAO obtener_ventas] {e}")

        return _VENTAS_MEMORIA

    @classmethod
    def crear_venta(cls, venta_dto, id_usuario, username):
        # Registra una cotizacion o venta. Si el estado es 'Vendido', descuenta 1 vehiculo del inventario
        conexion = ConexionBD.obtener_conexion()
        fecha_actual = datetime.date.today().strftime('%Y-%m-%d')
        venta_dto.fecha = fecha_actual

        if conexion:
            try:
                cursor = conexion.cursor()
                consulta = """
                    INSERT INTO ventas (id_cliente, id_item, id_usuario, precio_total, estado, fecha)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(consulta, (
                    venta_dto.id_cliente,
                    venta_dto.id_item,
                    id_usuario or 1,
                    venta_dto.precio_total,
                    venta_dto.estado,
                    fecha_actual
                ))
                conexion.commit()
                venta_dto.id_venta = cursor.lastrowid
                cursor.close()
                conexion.close()

                # Descuento automatico de stock si la operacion fue cerrada como Vendido
                if venta_dto.estado == 'Vendido':
                    InventarioDAO.descontar_stock(venta_dto.id_item, 1)

                SeguridadDAO.registrar_auditoria(id_usuario, username, 'VENTAS', 'INSERT_VENTA', f"Registro de {venta_dto.estado} para item ID {venta_dto.id_item} por ${venta_dto.precio_total}")
                return venta_dto
            except Exception as e:
                print(f"[Error VentasDAO crear_venta] {e}")
                if conexion:
                    conexion.rollback()
                    conexion.close()

        # Fallback en memoria
        venta_dto.id_venta = len(_VENTAS_MEMORIA) + 1
        _VENTAS_MEMORIA.insert(0, venta_dto)
        if venta_dto.estado == 'Vendido':
            InventarioDAO.descontar_stock(venta_dto.id_item, 1)
        SeguridadDAO.registrar_auditoria(id_usuario, username, 'VENTAS', 'INSERT_VENTA', f"Venta simulada por ${venta_dto.precio_total}")
        return venta_dto

    @classmethod
    def actualizar_estado(cls, id_venta, nuevo_estado, id_usuario, username):
        # Cambia el estado de una cotizacion a 'Vendido' y descuenta la unidad de patio
        conexion = ConexionBD.obtener_conexion()
        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)
                # Obtener el item asociado para descontar
                cursor.execute("SELECT id_item, estado FROM ventas WHERE id_venta = %s", (id_venta,))
                venta_actual = cursor.fetchone()

                if venta_actual:
                    cursor.execute("UPDATE ventas SET estado = %s WHERE id_venta = %s", (nuevo_estado, id_venta))
                    conexion.commit()

                    if nuevo_estado == 'Vendido' and venta_actual['estado'] != 'Vendido':
                        InventarioDAO.descontar_stock(venta_actual['id_item'], 1)

                    cursor.close()
                    conexion.close()
                    SeguridadDAO.registrar_auditoria(id_usuario, username, 'VENTAS', 'UPDATE_ESTADO', f"Venta #{id_venta} actualizada a {nuevo_estado}")
                    return True
            except Exception as e:
                print(f"[Error VentasDAO actualizar_estado] {e}")
                if conexion:
                    conexion.rollback()
                    conexion.close()

        # Actualizacion en memoria
        for v in _VENTAS_MEMORIA:
            if v.id_venta == id_venta:
                estado_anterior = v.estado
                v.estado = nuevo_estado
                if nuevo_estado == 'Vendido' and estado_anterior != 'Vendido':
                    InventarioDAO.descontar_stock(v.id_item, 1)
                SeguridadDAO.registrar_auditoria(id_usuario, username, 'VENTAS', 'UPDATE_ESTADO', f"Venta #{id_venta} cambiada a {nuevo_estado}")
                return True
        return False
