import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from config.MySQLConexion import ConexionBD
from models.entidades import ClienteDTO, ItemInventarioDTO, VentaDTO, OrdenTallerDTO
from dao.SeguridadDAO import SeguridadDAO
from dao.InventarioDAO import InventarioDAO
from dao.VentasDAO import VentasDAO
from dao.TallerDAO import TallerDAO

# Inicializacion de la aplicacion Flask y habilitacion de CORS para comunicacion con React
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Endpoint de diagnostico de salud del servidor y estado Master-Slave de MySQL
@app.route('/api/health', methods=['GET'])
def estado_salud():
    # Verifica conectividad con los nodos Master (escritura) y Slave (lectura)
    nodos = ConexionBD.obtener_estado_replicacion()
    master_activo = nodos['master']['conectado']
    slave_activo = nodos['slave']['conectado']
    return jsonify({
        'estado': 'Activo',
        'servicio': 'API SIG-Toyota Backend',
        'mysql_conectado': master_activo,
        'master': nodos['master'],
        'slave': nodos['slave'],
        'enrutamiento': 'Escrituras -> Master | Lecturas -> Slave' if slave_activo else 'Modo nodo unico / memoria'
    }), 200

# Endpoint de autenticacion de usuarios y asignacion de roles (Login)
@app.route('/api/login', methods=['POST'])
def login():
    # Valida credenciales contra la base de datos y retorna datos del usuario sin clave
    datos = request.get_json() or {}
    username = datos.get('username', '').strip()
    password = datos.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': 'Debe ingresar usuario y contraseña'}), 400

    usuario = SeguridadDAO.autenticar_usuario(username, password)
    if usuario:
        return jsonify({
            'exito': True,
            'mensaje': 'Autenticación exitosa',
            'usuario': usuario.a_diccionario()
        }), 200

    return jsonify({'error': 'Credenciales inválidas. Verifique usuario o clave'}), 401

# Endpoint consolidado para el Dashboard de Direccion General
@app.route('/api/dashboard', methods=['GET'])
def obtener_dashboard():
    # Retorna los 4 KPIs clave y las 5 transacciones mas recientes
    kpis = TallerDAO.obtener_metricas_dashboard()
    ventas = VentasDAO.obtener_ventas()[:5]
    ordenes = TallerDAO.obtener_todas()[:5]

    return jsonify({
        'kpis': kpis,
        'ventasRecientes': [v.a_diccionario() for v in ventas],
        'ordenesRecientes': [o.a_diccionario() for o in ordenes]
    }), 200

# Endpoint para listar clientes registrados
@app.route('/api/clientes', methods=['GET'])
def listar_clientes():
    # Retorna la lista completa de clientes ordenados alfabeticamente
    clientes = VentasDAO.obtener_clientes()
    return jsonify([c.a_diccionario() for c in clientes]), 200

# Endpoint para registrar un nuevo cliente
@app.route('/api/clientes', methods=['POST'])
def registrar_cliente():
    # Recibe datos del cliente y los persiste en la tabla clientes
    datos = request.get_json() or {}
    if not datos.get('dni_ruc') or not datos.get('nombre_razon'):
        return jsonify({'error': 'DNI/RUC y Nombre o Razón Social son obligatorios'}), 400

    cliente_dto = ClienteDTO(
        id_cliente=None,
        dni_ruc=datos['dni_ruc'].strip(),
        nombre_razon=datos['nombre_razon'].strip(),
        telefono=datos.get('telefono', '').strip(),
        email=datos.get('email', '').strip(),
        tipo_cliente=datos.get('tipo_cliente', 'Particular')
    )
    nuevo_cliente = VentasDAO.crear_cliente(cliente_dto)
    return jsonify(nuevo_cliente.a_diccionario()), 201

# Endpoint para consultar el inventario de vehiculos y repuestos OEM
@app.route('/api/inventario', methods=['GET'])
def listar_inventario():
    # Retorna todos los items incluyendo calculo de alerta de reposicion
    items = InventarioDAO.obtener_todos()
    return jsonify([i.a_diccionario() for i in items]), 200

# Endpoint para registrar o reponer existencias en inventario
@app.route('/api/inventario', methods=['POST'])
def agregar_item_inventario():
    # Registra un nuevo vehiculo o repuesto con su stock de seguridad
    datos = request.get_json() or {}
    requeridos = ['codigo_vin_sku', 'tipo', 'nombre_modelo', 'stock_actual', 'stock_minimo', 'precio_usd']
    if any(campo not in datos for campo in requeridos):
        return jsonify({'error': 'Faltan campos obligatorios para el ítem'}), 400

    item_dto = ItemInventarioDTO(
        id_item=None,
        codigo_vin_sku=datos['codigo_vin_sku'].strip(),
        tipo=datos['tipo'],
        nombre_modelo=datos['nombre_modelo'].strip(),
        stock_actual=int(datos['stock_actual']),
        stock_minimo=int(datos['stock_minimo']),
        precio_usd=float(datos['precio_usd'])
    )
    nuevo_item = InventarioDAO.crear_item(item_dto)
    return jsonify(nuevo_item.a_diccionario()), 201

# Endpoint para consultar el historial de cotizaciones y ventas
@app.route('/api/ventas', methods=['GET'])
def listar_ventas():
    # Retorna las operaciones comerciales realizadas
    ventas = VentasDAO.obtener_ventas()
    return jsonify([v.a_diccionario() for v in ventas]), 200

# Endpoint para registrar una cotizacion o concretar una venta
@app.route('/api/ventas', methods=['POST'])
def crear_venta():
    # Registra la venta y descuenta stock de vehiculo si el estado es Vendido
    datos = request.get_json() or {}
    if not datos.get('id_cliente') or not datos.get('id_item') or not datos.get('precio_total'):
        return jsonify({'error': 'Cliente, Modelo y Precio son obligatorios'}), 400

    venta_dto = VentaDTO(
        id_venta=None,
        id_cliente=int(datos['id_cliente']),
        cliente_nombre=datos.get('cliente_nombre', ''),
        id_item=int(datos['id_item']),
        vehiculo_nombre=datos.get('vehiculo_nombre', ''),
        precio_total=float(datos['precio_total']),
        estado=datos.get('estado', 'Cotizado'),
        fecha=''
    )
    usuario_nombre = datos.get('username', 'sistema')
    nueva_venta = VentasDAO.crear_venta(venta_dto, id_usuario=1, username=usuario_nombre)
    return jsonify(nueva_venta.a_diccionario()), 201

# Endpoint para actualizar el estado de una venta (ej. Cotizado -> Vendido)
@app.route('/api/ventas/<int:id_venta>/estado', methods=['PUT'])
def actualizar_estado_venta(id_venta):
    # Cambia el estado a Vendido y descuenta 1 unidad del inventario automaticamente
    datos = request.get_json() or {}
    nuevo_estado = datos.get('estado', 'Vendido')
    usuario_nombre = datos.get('username', 'sistema')

    exito = VentasDAO.actualizar_estado(id_venta, nuevo_estado, id_usuario=1, username=usuario_nombre)
    if exito:
        return jsonify({'exito': True, 'mensaje': f'Venta actualizada a {nuevo_estado}'}), 200
    return jsonify({'error': 'No se pudo actualizar la venta'}), 400

# Endpoint para listar ordenes de servicio de taller
@app.route('/api/taller', methods=['GET'])
def listar_ordenes_taller():
    # Retorna las ordenes tecnicas de mantenimiento y PDI
    ordenes = TallerDAO.obtener_todas()
    return jsonify([o.a_diccionario() for o in ordenes]), 200

# Endpoint para registrar una orden de servicio en taller
@app.route('/api/taller', methods=['POST'])
def registrar_orden_taller():
    # Crea una orden de servicio y descuenta repuesto OEM si fue seleccionado
    datos = request.get_json() or {}
    if not datos.get('id_cliente') or not datos.get('placa_vin') or not datos.get('costo_usd'):
        return jsonify({'error': 'Cliente, Placa/VIN y Costo son requeridos'}), 400

    orden_dto = OrdenTallerDTO(
        id_orden=None,
        id_cliente=int(datos['id_cliente']),
        cliente_nombre=datos.get('cliente_nombre', ''),
        placa_vin=datos['placa_vin'].strip().upper(),
        tipo_servicio=datos.get('tipo_servicio', 'Mantenimiento Preventivo (10,000 km)'),
        tecnico=datos.get('tecnico', 'Tec. Manuel Salinas'),
        id_item_repuesto=int(datos['id_item_repuesto']) if datos.get('id_item_repuesto') else None,
        repuesto_nombre=datos.get('repuesto_nombre', ''),
        costo_usd=float(datos['costo_usd']),
        estado=datos.get('estado', 'Pendiente'),
        fecha_ingreso=''
    )
    usuario_nombre = datos.get('username', 'sistema')
    nueva_orden = TallerDAO.crear_orden(orden_dto, id_usuario=1, username=usuario_nombre)
    return jsonify(nueva_orden.a_diccionario()), 201

# Endpoint para actualizar el estado de una orden de taller
@app.route('/api/taller/<int:id_orden>/estado', methods=['PUT'])
def actualizar_estado_taller(id_orden):
    # Actualiza el estado (Pendiente -> En proceso -> Entregado)
    datos = request.get_json() or {}
    nuevo_estado = datos.get('estado', 'Entregado')
    usuario_nombre = datos.get('username', 'sistema')

    exito = TallerDAO.actualizar_estado(id_orden, nuevo_estado, id_usuario=1, username=usuario_nombre)
    if exito:
        return jsonify({'exito': True, 'mensaje': f'Orden actualizada a {nuevo_estado}'}), 200
    return jsonify({'error': 'No se pudo actualizar la orden de taller'}), 400

# Endpoint para consultar la bitacora de auditoria (ISO 27001)
@app.route('/api/auditoria', methods=['GET'])
def listar_auditoria():
    # Retorna el historial inmutable de acciones y accesos
    logs = SeguridadDAO.obtener_todos_logs()
    return jsonify([l.a_diccionario() for l in logs]), 200

# Endpoint para registrar eventos manuales de auditoria
@app.route('/api/auditoria', methods=['POST'])
def registrar_log():
    # Registra una accion manual en la bitacora
    datos = request.get_json() or {}
    SeguridadDAO.registrar_auditoria(
        id_usuario=datos.get('id_usuario', 1),
        username=datos.get('username', 'sistema'),
        modulo=datos.get('modulo', 'GENERAL'),
        accion=datos.get('accion', 'EVENTO'),
        detalle=datos.get('detalle', 'Registro manual')
    )
    return jsonify({'exito': True}), 201

# Ejecucion del servidor Flask en el puerto 5000
if __name__ == '__main__':
    puerto = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=puerto, debug=True)
