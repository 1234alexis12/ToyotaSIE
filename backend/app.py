import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from config.MySQLConexion import ConexionBD
from models.entidades import ClienteDTO, ItemInventarioDTO, VentaDTO, OrdenTallerDTO
from dao.SeguridadDAO import SeguridadDAO
from dao.InventarioDAO import InventarioDAO
from dao.VentasDAO import VentasDAO
from dao.TallerDAO import TallerDAO
from dao.ServiceDeskDAO import ServiceDeskDAO, TIPOS_SOLICITUD_VALIDOS, TIPOS_CAMBIO_VALIDOS
from servicios.JiraService import JiraService

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


# =========================================================================
# MODULO AREA DE TI: SERVICE DESK, CONTROL DE CAMBIOS Y CONEXION JIRA
# =========================================================================

@app.route('/api/tickets/jira-config', methods=['GET'])
def estado_conexion_jira():
    # Verifica configuracion y conectividad con Jira Cloud sin exponer tokens
    return jsonify(JiraService.verificar_conexion()), 200


@app.route('/api/tickets/metricas', methods=['GET'])
def obtener_metricas_ti():
    # Retorna indicadores del Service Desk desde la replica de lectura (Slave)
    return jsonify(ServiceDeskDAO.obtener_metricas()), 200


@app.route('/api/tickets', methods=['GET'])
def listar_tickets_ti():
    # Lista todos los tickets para TI/Gerente o solo los propios para Operador
    rol = request.args.get('rol', '').strip()
    id_usuario_arg = request.args.get('id_usuario')
    id_filtro = int(id_usuario_arg) if (rol == 'Operador' and id_usuario_arg and id_usuario_arg.isdigit()) else None
    tickets = ServiceDeskDAO.obtener_tickets(id_usuario_filtro=id_filtro)
    return jsonify([t.a_diccionario() for t in tickets]), 200


@app.route('/api/tickets', methods=['POST'])
def crear_ticket_ti():
    # Registra el ticket en MySQL Master y lo envia a Jira Cloud si esta configurado
    datos = request.get_json() or {}
    titulo = (datos.get('titulo') or '').strip()
    descripcion = (datos.get('descripcion') or '').strip()
    tipo_solicitud = datos.get('tipo_solicitud', 'Incidente')
    tipo_cambio = datos.get('tipo_cambio', 'N/A')

    if not titulo or not descripcion:
        return jsonify({'error': 'Título y Descripción son obligatorios'}), 400
    if tipo_solicitud not in TIPOS_SOLICITUD_VALIDOS:
        return jsonify({'error': 'Tipo de solicitud inválido'}), 400
    if tipo_solicitud == 'Cambio' and tipo_cambio not in TIPOS_CAMBIO_VALIDOS:
        return jsonify({'error': 'Tipo de cambio inválido'}), 400

    ticket = ServiceDeskDAO.crear_ticket({
        'id_usuario_solicitante': datos.get('id_usuario_solicitante', 1),
        'solicitante_username': datos.get('solicitante_username', 'sistema'),
        'solicitante_nombre': datos.get('solicitante_nombre', 'Usuario SIG-Toyota'),
        'tipo_solicitud': tipo_solicitud,
        'tipo_cambio': tipo_cambio,
        'prioridad': datos.get('prioridad', 'Media'),
        'area_origen': datos.get('area_origen', 'Operaciones'),
        'titulo': titulo,
        'descripcion': descripcion,
        'impacto_riesgo': (datos.get('impacto_riesgo') or '').strip(),
        'plan_pruebas': (datos.get('plan_pruebas') or '').strip(),
        'plan_rollback': (datos.get('plan_rollback') or '').strip(),
    })

    res_jira = JiraService.crear_issue(ticket)
    ServiceDeskDAO.actualizar_vinculo_jira(
        ticket.id_ticket,
        res_jira.get('key'),
        res_jira.get('url'),
        res_jira.get('ok', False),
        res_jira.get('error'),
    )
    ticket_actualizado, _ = ServiceDeskDAO.obtener_detalle(ticket.id_ticket)
    return jsonify((ticket_actualizado or ticket).a_diccionario()), 201


@app.route('/api/tickets/<int:id_ticket>', methods=['GET'])
def obtener_detalle_ticket_ti(id_ticket):
    # Retorna el detalle completo del ticket y su historial cronologico
    ticket, historial = ServiceDeskDAO.obtener_detalle(id_ticket)
    if not ticket:
        return jsonify({'error': 'Ticket no encontrado'}), 404
    return jsonify({
        'ticket': ticket.a_diccionario(),
        'historial': [h.a_diccionario() for h in historial],
    }), 200


@app.route('/api/tickets/<int:id_ticket>/estado', methods=['PUT'])
def actualizar_estado_ticket_ti(id_ticket):
    # Actualiza la etapa del flujo ITIL, valida aprobacion en Accesos/Cambios y sincroniza con Jira
    datos = request.get_json() or {}
    nuevo_estado = datos.get('estado')
    if not nuevo_estado:
        return jsonify({'error': 'Debe especificar el nuevo estado'}), 400

    actualizado, error = ServiceDeskDAO.actualizar_estado(
        id_ticket=id_ticket,
        nuevo_estado=nuevo_estado,
        id_actor=int(datos.get('id_usuario') or 1),
        username_actor=datos.get('username', 'sistema'),
        nombre_actor=datos.get('nombre_completo', 'Soporte TI'),
        rol_actor=datos.get('rol', 'TI'),
        tecnico_ti=datos.get('tecnico_ti_asignado'),
        resolucion=datos.get('resolucion_evidencia'),
        comentario=datos.get('comentario'),
    )
    if error:
        return jsonify({'error': error}), 400

    if actualizado.jira_issue_key and JiraService.esta_configurado():
        detalle_jira = f"[SIG-Toyota] {actualizado.estado} por {datos.get('nombre_completo', 'TI')}: {datos.get('comentario') or datos.get('resolucion_evidencia') or 'Actualizacion de estado'}"
        JiraService.agregar_comentario(actualizado.jira_issue_key, detalle_jira)
        JiraService.transicionar_estado(actualizado.jira_issue_key, actualizado.estado)

    return jsonify(actualizado.a_diccionario()), 200


@app.route('/api/tickets/<int:id_ticket>/jira-sync', methods=['POST'])
def sincronizar_ticket_jira(id_ticket):
    # Reintenta crear el ticket en Jira o consulta su estado actual en Atlassian
    ticket, _ = ServiceDeskDAO.obtener_detalle(id_ticket)
    if not ticket:
        return jsonify({'error': 'Ticket no encontrado'}), 404

    if not JiraService.esta_configurado():
        return jsonify({'error': 'Jira no está configurado en variables de entorno (.env).'}), 400

    if not ticket.jira_issue_key:
        res_jira = JiraService.crear_issue(ticket)
        ServiceDeskDAO.actualizar_vinculo_jira(
            ticket.id_ticket,
            res_jira.get('key'),
            res_jira.get('url'),
            res_jira.get('ok', False),
            res_jira.get('error'),
        )
        actualizado, _ = ServiceDeskDAO.obtener_detalle(id_ticket)
        if res_jira.get('ok'):
            return jsonify({'exito': True, 'mensaje': f"Ticket enviado a Jira como {res_jira['key']}", 'ticket': actualizado.a_diccionario()}), 200
        return jsonify({'error': res_jira.get('error') or 'Error al enviar a Jira'}), 400

    consulta = JiraService.consultar_issue(ticket.jira_issue_key)
    if not consulta.get('ok'):
        return jsonify({'error': consulta.get('error')}), 400

    return jsonify({
        'exito': True,
        'estado_jira': consulta.get('estado_jira'),
        'asignado_jira': consulta.get('asignado_jira'),
        'ticket': ticket.a_diccionario(),
    }), 200


# Ejecucion del servidor Flask en el puerto 5000
if __name__ == '__main__':
    puerto = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=puerto, debug=True)
