# Clases de dominio y Objetos de Transferencia de Datos (DTO) del sistema

class UsuarioDTO:
    # DTO para transferir informacion de usuarios sin exponer contraseñas
    def __init__(self, id_usuario, username, nombre_completo, rol, estado='Activo'):
        self.id_usuario = id_usuario
        self.username = username
        self.nombre_completo = nombre_completo
        self.rol = rol
        self.estado = estado

    def a_diccionario(self):
        # Serializa el objeto a diccionario para respuestas JSON en la API
        return {
            'id_usuario': self.id_usuario,
            'username': self.username,
            'nombre_completo': self.nombre_completo,
            'rol': self.rol,
            'estado': self.estado
        }


class ClienteDTO:
    # DTO para representar clientes particulares o corporativos
    def __init__(self, id_cliente, dni_ruc, nombre_razon, telefono, email, tipo_cliente='Particular'):
        self.id_cliente = id_cliente
        self.dni_ruc = dni_ruc
        self.nombre_razon = nombre_razon
        self.telefono = telefono
        self.email = email
        self.tipo_cliente = tipo_cliente

    def a_diccionario(self):
        # Convierte los atributos del cliente a formato JSON
        return {
            'id_cliente': self.id_cliente,
            'dni_ruc': self.dni_ruc,
            'nombre_razon': self.nombre_razon,
            'telefono': self.telefono,
            'email': self.email,
            'tipo_cliente': self.tipo_cliente
        }


class ItemInventarioDTO:
    # DTO para vehiculos y repuestos almacenados en inventario
    def __init__(self, id_item, codigo_vin_sku, tipo, nombre_modelo, stock_actual, stock_minimo, precio_usd):
        self.id_item = id_item
        self.codigo_vin_sku = codigo_vin_sku
        self.tipo = tipo
        self.nombre_modelo = nombre_modelo
        self.stock_actual = stock_actual
        self.stock_minimo = stock_minimo
        self.precio_usd = float(precio_usd)

    def es_stock_critico(self):
        # Regla de negocio: determina si el item requiere reposicion inmediata
        return self.stock_actual <= self.stock_minimo

    def a_diccionario(self):
        # Serializa el item incluyendo el estado calculado de reposicion
        return {
            'id_item': self.id_item,
            'codigo_vin_sku': self.codigo_vin_sku,
            'tipo': self.tipo,
            'nombre_modelo': self.nombre_modelo,
            'stock_actual': self.stock_actual,
            'stock_minimo': self.stock_minimo,
            'precio_usd': self.precio_usd,
            'alerta_stock': self.es_stock_critico()
        }


class VentaDTO:
    # DTO para cotizaciones y transacciones de venta comercial
    def __init__(self, id_venta, id_cliente, cliente_nombre, id_item, vehiculo_nombre, precio_total, estado, fecha):
        self.id_venta = id_venta
        self.id_cliente = id_cliente
        self.cliente_nombre = cliente_nombre
        self.id_item = id_item
        self.vehiculo_nombre = vehiculo_nombre
        self.precio_total = float(precio_total)
        self.estado = estado
        self.fecha = str(fecha)

    def a_diccionario(self):
        # Retorna el detalle de la venta formateado para la interfaz
        return {
            'id_venta': self.id_venta,
            'id_cliente': self.id_cliente,
            'cliente_nombre': self.cliente_nombre,
            'id_item': self.id_item,
            'vehiculo_nombre': self.vehiculo_nombre,
            'precio_total': self.precio_total,
            'estado': self.estado,
            'fecha': self.fecha
        }


class OrdenTallerDTO:
    # DTO para ordenes de trabajo de mantenimiento, reparacion o PDI
    def __init__(self, id_orden, id_cliente, cliente_nombre, placa_vin, tipo_servicio, tecnico, id_item_repuesto, repuesto_nombre, costo_usd, estado, fecha_ingreso):
        self.id_orden = id_orden
        self.id_cliente = id_cliente
        self.cliente_nombre = cliente_nombre
        self.placa_vin = placa_vin
        self.tipo_servicio = tipo_servicio
        self.tecnico = tecnico
        self.id_item_repuesto = id_item_repuesto
        self.repuesto_nombre = repuesto_nombre
        self.costo_usd = float(costo_usd)
        self.estado = estado
        self.fecha_ingreso = str(fecha_ingreso)

    def a_diccionario(self):
        # Convierte los datos de la orden a diccionario JSON
        return {
            'id_orden': self.id_orden,
            'id_cliente': self.id_cliente,
            'cliente_nombre': self.cliente_nombre,
            'placa_vin': self.placa_vin,
            'tipo_servicio': self.tipo_servicio,
            'tecnico': self.tecnico,
            'id_item_repuesto': self.id_item_repuesto,
            'repuesto_nombre': self.repuesto_nombre,
            'costo_usd': self.costo_usd,
            'estado': self.estado,
            'fecha_ingreso': self.fecha_ingreso
        }


class AuditoriaDTO:
    # DTO para registros de trazabilidad y eventos del sistema (ISO 27001)
    def __init__(self, id_log, fecha_hora, username, modulo, accion, detalle):
        self.id_log = id_log
        self.fecha_hora = str(fecha_hora)
        self.username = username
        self.modulo = modulo
        self.accion = accion
        self.detalle = detalle

    def a_diccionario(self):
        # Serializa el evento de auditoria
        return {
            'id_log': self.id_log,
            'fecha_hora': self.fecha_hora,
            'username': self.username,
            'modulo': self.modulo,
            'accion': self.accion,
            'detalle': self.detalle
        }
