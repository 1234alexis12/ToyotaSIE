import datetime
from config.MySQLConexion import ConexionBD
from models.entidades import OrdenTallerDTO
from dao.InventarioDAO import InventarioDAO
from dao.SeguridadDAO import SeguridadDAO

# Datos semilla de ordenes de taller en memoria
_TALLER_MEMORIA = [
    OrdenTallerDTO(1, 1, 'Minera Cerro Verde S.A.A.', 'V9A-782', 'Mantenimiento Preventivo (10,000 km)', 'Tec. Manuel Salinas', 5, 'Filtro de Aceite Original Toyota (Hilux/Fortuner)', 120.00, 'Entregado', '2026-11-19'),
    OrdenTallerDTO(2, 2, 'Juan Perez Delgado', 'V4B-119', 'PDI (Inspeccion Pre-Entrega)', 'Tec. David Paredes', None, 'Ninguno / Solo Mano de Obra', 80.00, 'En proceso', '2026-11-21'),
    OrdenTallerDTO(3, 3, 'Transportes Arequipa Express S.A.C.', 'V7C-554', 'Reparacion de Frenos', 'Tec. Manuel Salinas', 6, 'Pastillas de Freno Delanteras OEM Toyota Hilux', 210.00, 'Pendiente', '2026-11-21')
]

# Capa de Acceso a Datos (DAO) para Operaciones de Taller y Metricas del Dashboard
class TallerDAO:

    @classmethod
    def obtener_todas(cls):
        # Obtiene las ordenes de taller uniendo cliente y repuesto consumido
        conexion = ConexionBD.obtener_conexion()
        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)
                consulta = """
                    SELECT o.id_orden, o.id_cliente, c.nombre_razon AS cliente_nombre,
                           o.placa_vin, o.tipo_servicio, o.tecnico,
                           o.id_item_repuesto, COALESCE(i.nombre_modelo, 'Ninguno / Mano de Obra') AS repuesto_nombre,
                           o.costo_usd, o.estado, o.fecha_ingreso
                    FROM ordenes_taller o
                    INNER JOIN clientes c ON o.id_cliente = c.id_cliente
                    LEFT JOIN inventario i ON o.id_item_repuesto = i.id_item
                    ORDER BY o.fecha_ingreso DESC, o.id_orden DESC
                """
                cursor.execute(consulta)
                filas = cursor.fetchall()
                cursor.close()
                conexion.close()
                return [OrdenTallerDTO(f['id_orden'], f['id_cliente'], f['cliente_nombre'], f['placa_vin'], f['tipo_servicio'], f['tecnico'], f['id_item_repuesto'], f['repuesto_nombre'], f['costo_usd'], f['estado'], f['fecha_ingreso']) for f in filas]
            except Exception as e:
                print(f"[Error TallerDAO obtener_todas] {e}")

        return _TALLER_MEMORIA

    @classmethod
    def crear_orden(cls, orden_dto, id_usuario, username):
        # Registra una orden de servicio tecnico. Si utiliza repuesto OEM, descuenta del almacen
        conexion = ConexionBD.obtener_conexion()
        fecha_actual = datetime.date.today().strftime('%Y-%m-%d')
        orden_dto.fecha_ingreso = fecha_actual

        if conexion:
            try:
                cursor = conexion.cursor()
                consulta = """
                    INSERT INTO ordenes_taller (id_cliente, id_item_repuesto, placa_vin, tipo_servicio, tecnico, costo_usd, estado, fecha_ingreso)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(consulta, (
                    orden_dto.id_cliente,
                    orden_dto.id_item_repuesto,
                    orden_dto.placa_vin,
                    orden_dto.tipo_servicio,
                    orden_dto.tecnico,
                    orden_dto.costo_usd,
                    orden_dto.estado,
                    fecha_actual
                ))
                conexion.commit()
                orden_dto.id_orden = cursor.lastrowid
                cursor.close()
                conexion.close()

                # Descuento automatico del repuesto utilizado en el mantenimiento
                if orden_dto.id_item_repuesto:
                    InventarioDAO.descontar_stock(orden_dto.id_item_repuesto, 1)

                SeguridadDAO.registrar_auditoria(id_usuario, username, 'TALLER', 'INSERT_ORDEN', f"Apertura de orden OT #{orden_dto.id_orden} para placa {orden_dto.placa_vin}")
                return orden_dto
            except Exception as e:
                print(f"[Error TallerDAO crear_orden] {e}")
                if conexion:
                    conexion.rollback()
                    conexion.close()

        # En memoria
        orden_dto.id_orden = len(_TALLER_MEMORIA) + 1
        _TALLER_MEMORIA.insert(0, orden_dto)
        if orden_dto.id_item_repuesto:
            InventarioDAO.descontar_stock(orden_dto.id_item_repuesto, 1)
        SeguridadDAO.registrar_auditoria(id_usuario, username, 'TALLER', 'INSERT_ORDEN', f"Orden para placa {orden_dto.placa_vin}")
        return orden_dto

    @classmethod
    def actualizar_estado(cls, id_orden, nuevo_estado, id_usuario, username):
        # Actualiza el estado del servicio tecnico (Pendiente -> En proceso -> Entregado)
        conexion = ConexionBD.obtener_conexion()
        if conexion:
            try:
                cursor = conexion.cursor()
                cursor.execute("UPDATE ordenes_taller SET estado = %s WHERE id_orden = %s", (nuevo_estado, id_orden))
                conexion.commit()
                cursor.close()
                conexion.close()
                SeguridadDAO.registrar_auditoria(id_usuario, username, 'TALLER', 'UPDATE_ESTADO', f"Orden #{id_orden} actualizada a {nuevo_estado}")
                return True
            except Exception as e:
                print(f"[Error TallerDAO actualizar_estado] {e}")
                if conexion:
                    conexion.rollback()
                    conexion.close()

        # En memoria
        for o in _TALLER_MEMORIA:
            if o.id_orden == id_orden:
                o.estado = nuevo_estado
                SeguridadDAO.registrar_auditoria(id_usuario, username, 'TALLER', 'UPDATE_ESTADO', f"Orden #{id_orden} cambiada a {nuevo_estado}")
                return True
        return False

    @classmethod
    def obtener_metricas_dashboard(cls):
        # Calcula los 4 KPIs clave ejecutando agregaciones SQL (SUM, COUNT)
        conexion = ConexionBD.obtener_conexion()
        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)

                # 1. Total vendido en USD
                cursor.execute("SELECT COALESCE(SUM(precio_total), 0) AS total_vendido FROM ventas WHERE estado = 'Vendido'")
                total_vendido = float(cursor.fetchone()['total_vendido'])

                # 2. Vehiculos en stock disponibles
                cursor.execute("SELECT COALESCE(SUM(stock_actual), 0) AS stock_vehiculos FROM inventario WHERE tipo = 'Vehiculo'")
                stock_vehiculos = int(cursor.fetchone()['stock_vehiculos'])

                # 3. Repuestos con stock critico por debajo del minimo
                cursor.execute("SELECT COUNT(*) AS repuestos_alerta FROM inventario WHERE tipo = 'Repuesto' AND stock_actual <= stock_minimo")
                repuestos_alerta = int(cursor.fetchone()['repuestos_alerta'])

                # 4. Ordenes activas en taller no entregadas
                cursor.execute("SELECT COUNT(*) AS ordenes_activas FROM ordenes_taller WHERE estado != 'Entregado'")
                ordenes_activas = int(cursor.fetchone()['ordenes_activas'])

                cursor.close()
                conexion.close()

                return {
                    'totalVendido': total_vendido,
                    'vehiculosDisponibles': stock_vehiculos,
                    'repuestosAlerta': repuestos_alerta,
                    'ordenesActivas': ordenes_activas
                }
            except Exception as e:
                print(f"[Error Metricas Dashboard] {e}")

        # Calculo en memoria
        from dao.VentasDAO import VentasDAO
        from dao.InventarioDAO import InventarioDAO

        ventas = VentasDAO.obtener_ventas()
        inventario = InventarioDAO.obtener_todos()
        taller = cls.obtener_todas()

        total_vendido = sum(v.precio_total for v in ventas if v.estado == 'Vendido')
        stock_vehiculos = sum(i.stock_actual for i in inventario if i.tipo == 'Vehiculo')
        repuestos_alerta = sum(1 for i in inventario if i.tipo == 'Repuesto' and i.es_stock_critico())
        ordenes_activas = sum(1 for o in taller if o.estado != 'Entregado')

        return {
            'totalVendido': total_vendido,
            'vehiculosDisponibles': stock_vehiculos,
            'repuestosAlerta': repuestos_alerta,
            'ordenesActivas': ordenes_activas
        }
