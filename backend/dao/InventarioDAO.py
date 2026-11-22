from config.MySQLConexion import ConexionBD
from models.entidades import ItemInventarioDTO

# Datos semilla de inventario en memoria para pruebas directas
_INVENTARIO_MEMORIA = [
    ItemInventarioDTO(1, '8AJBA3CD4P123456', 'Vehiculo', 'Toyota Hilux 4x4 Doble Cabina SRX', 4, 2, 48500.00),
    ItemInventarioDTO(2, '93XBA3CD4P789012', 'Vehiculo', 'Toyota Corolla Sedan 1.8 XEI', 2, 2, 24200.00),
    ItemInventarioDTO(3, '8AJBA3CD4P345678', 'Vehiculo', 'Toyota RAV4 Hibrida 2.5 AWD', 3, 1, 39900.00),
    ItemInventarioDTO(4, '93XBA3CD4P901234', 'Vehiculo', 'Toyota Yaris Sedan 1.5 GLI', 1, 2, 18900.00),
    ItemInventarioDTO(5, 'SKU-04152-YZZA6', 'Repuesto', 'Filtro de Aceite Original Toyota (Hilux/Fortuner)', 18, 10, 22.50),
    ItemInventarioDTO(6, 'SKU-04465-0K340', 'Repuesto', 'Pastillas de Freno Delanteras OEM Toyota Hilux', 3, 5, 95.00),
    ItemInventarioDTO(7, 'SKU-08880-80845', 'Repuesto', 'Aceite Motor Sintetico Toyota 5W-30 (Galon)', 2, 6, 45.00),
    ItemInventarioDTO(8, 'SKU-17801-0L040', 'Repuesto', 'Filtro de Aire Original Hilux/Prado', 12, 5, 38.00)
]

# Capa de Acceso a Datos (DAO) para el Inventario de Vehiculos y Repuestos
class InventarioDAO:

    @classmethod
    def obtener_todos(cls):
        # Consulta el listado completo de vehiculos y repuestos con su stock actual
        conexion = ConexionBD.obtener_conexion()
        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)
                consulta = "SELECT id_item, codigo_vin_sku, tipo, nombre_modelo, stock_actual, stock_minimo, precio_usd FROM inventario ORDER BY tipo DESC, nombre_modelo ASC"
                cursor.execute(consulta)
                filas = cursor.fetchall()
                cursor.close()
                conexion.close()
                return [ItemInventarioDTO(f['id_item'], f['codigo_vin_sku'], f['tipo'], f['nombre_modelo'], f['stock_actual'], f['stock_minimo'], f['precio_usd']) for f in filas]
            except Exception as e:
                print(f"[Error InventarioDAO obtener_todos] {e}")

        # Retorna el inventario en memoria
        return _INVENTARIO_MEMORIA

    @classmethod
    def crear_item(cls, item_dto):
        # Inserta un nuevo vehiculo o repuesto en la base de datos
        conexion = ConexionBD.obtener_conexion()
        if conexion:
            try:
                cursor = conexion.cursor()
                consulta = """
                    INSERT INTO inventario (codigo_vin_sku, tipo, nombre_modelo, stock_actual, stock_minimo, precio_usd)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(consulta, (
                    item_dto.codigo_vin_sku,
                    item_dto.tipo,
                    item_dto.nombre_modelo,
                    item_dto.stock_actual,
                    item_dto.stock_minimo,
                    item_dto.precio_usd
                ))
                conexion.commit()
                item_dto.id_item = cursor.lastrowid
                cursor.close()
                conexion.close()
                return item_dto
            except Exception as e:
                print(f"[Error InventarioDAO crear_item] {e}")
                if conexion:
                    conexion.rollback()
                    conexion.close()

        # Insercion en memoria
        item_dto.id_item = len(_INVENTARIO_MEMORIA) + 1
        _INVENTARIO_MEMORIA.append(item_dto)
        return item_dto

    @classmethod
    def descontar_stock(cls, id_item, cantidad=1):
        # Reduce de forma transaccional el stock asegurando que no quede en valores negativos
        conexion = ConexionBD.obtener_conexion()
        if conexion:
            try:
                cursor = conexion.cursor()
                # Sentencia con validacion de disponibilidad para consistencia ACID
                consulta = """
                    UPDATE inventario
                    SET stock_actual = stock_actual - %s
                    WHERE id_item = %s AND stock_actual >= %s
                """
                cursor.execute(consulta, (cantidad, id_item, cantidad))
                afectadas = cursor.rowcount
                conexion.commit()
                cursor.close()
                conexion.close()
                return afectadas > 0
            except Exception as e:
                print(f"[Error Descontar Stock] {e}")
                if conexion:
                    conexion.rollback()
                    conexion.close()

        # Descuento en memoria
        for item in _INVENTARIO_MEMORIA:
            if item.id_item == id_item and item.stock_actual >= cantidad:
                item.stock_actual -= cantidad
                return True
        return False
