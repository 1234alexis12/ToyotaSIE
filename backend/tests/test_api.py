import pytest
from app import app
from dao.InventarioDAO import InventarioDAO

# Fixture de Pytest para configurar el cliente de pruebas de Flask
@pytest.fixture
def cliente():
    app.config['TESTING'] = True
    with app.test_client() as cliente_prueba:
        yield cliente_prueba

# Prueba 1: Diagnostico de salud de la API
def test_salud_api(cliente):
    # Valida que el endpoint /api/health responda con codigo 200
    respuesta = cliente.get('/api/health')
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos['estado'] == 'Activo'

# Prueba 2: Autenticacion exitosa con rol de Gerente
def test_login_gerente_exitoso(cliente):
    # Valida que las credenciales correctas retornen el objeto usuario y su rol
    payload = {'username': 'admin_gerente', 'password': 'Toyota2026!'}
    respuesta = cliente.post('/api/login', json=payload)
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos['exito'] is True
    assert datos['usuario']['rol'] == 'Gerente'

# Prueba 3: Rechazo de credenciales incorrectas (Seguridad)
def test_login_credenciales_invalidas(cliente):
    # Valida que contraseñas erroneas retornen codigo 401
    payload = {'username': 'admin_gerente', 'password': 'clave_incorrecta'}
    respuesta = cliente.post('/api/login', json=payload)
    assert respuesta.status_code == 401

# Prueba 4: Consulta de metricas del Dashboard
def test_metricas_dashboard(cliente):
    # Valida la estructura de los 4 KPIs del panel gerencial
    respuesta = cliente.get('/api/dashboard')
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert 'kpis' in datos
    assert 'totalVendido' in datos['kpis']
    assert 'vehiculosDisponibles' in datos['kpis']
    assert 'repuestosAlerta' in datos['kpis']
    assert 'ordenesActivas' in datos['kpis']

# Prueba 5: Registro de operacion de venta y descuento automatico de stock
def test_crear_venta_con_descuento_stock(cliente):
    # Asegura stock disponible para la prueba de consistencia
    from config.MySQLConexion import ConexionBD
    items_antes = InventarioDAO.obtener_todos()
    item_hilux_antes = next(i for i in items_antes if i.id_item == 1)
    if item_hilux_antes.stock_actual <= 0:
        conexion = ConexionBD.obtener_conexion()
        if conexion:
            try:
                cursor = conexion.cursor()
                cursor.execute("UPDATE inventario SET stock_actual = 5 WHERE id_item = 1")
                conexion.commit()
                cursor.close()
                conexion.close()
            except Exception:
                pass
        items_antes = InventarioDAO.obtener_todos()
        item_hilux_antes = next(i for i in items_antes if i.id_item == 1)
    stock_previo = item_hilux_antes.stock_actual

    # Registra una venta cerrada como 'Vendido'
    payload = {
        'id_cliente': 1,
        'cliente_nombre': 'Minera Cerro Verde S.A.A.',
        'id_item': 1,
        'vehiculo_nombre': 'Toyota Hilux 4x4 Doble Cabina SRX',
        'precio_total': 48500.00,
        'estado': 'Vendido',
        'username': 'admin_gerente'
    }
    respuesta = cliente.post('/api/ventas', json=payload)
    assert respuesta.status_code == 201

    # Verifica que el stock del vehiculo se haya reducido exactamente en 1 unidad
    items_despues = InventarioDAO.obtener_todos()
    item_hilux_despues = next(i for i in items_despues if i.id_item == 1)
    assert item_hilux_despues.stock_actual == stock_previo - 1

# Prueba 6: Trazabilidad en la bitacora de auditoria (ISO 27001)
def test_registro_en_bitacora_auditoria(cliente):
    # Valida que la bitacora de auditoria contenga registros y conserve el formato de eventos
    respuesta = cliente.get('/api/auditoria')
    assert respuesta.status_code == 200
    logs = respuesta.get_json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    assert 'modulo' in logs[0]
    assert 'accion' in logs[0]


# Prueba 7: Autenticacion del nuevo rol Soporte TI
def test_login_soporte_ti_exitoso(cliente):
    payload = {'username': 'soporte_ti', 'password': 'Toyota2026!'}
    respuesta = cliente.post('/api/login', json=payload)
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos['exito'] is True
    assert datos['usuario']['rol'] == 'TI'


# Prueba 8: Creacion de ticket en Service Desk con calculo SLA y mock de Jira
def test_crear_ticket_service_desk_y_jira(cliente, monkeypatch):
    from servicios.JiraService import JiraService

    monkeypatch.setattr(
        JiraService,
        'crear_issue',
        classmethod(lambda cls, t: {
            'ok': True,
            'key': 'TSIE-99',
            'url': 'https://demo.atlassian.net/browse/TSIE-99',
            'error': None,
        }),
    )

    payload = {
        'id_usuario_solicitante': 2,
        'solicitante_username': 'operador_taller',
        'solicitante_nombre': 'Marcos Quispe (Asesor de Servicio)',
        'tipo_solicitud': 'Incidente',
        'prioridad': 'Critica',
        'area_origen': 'Taller',
        'titulo': 'Caida de lector de codigos VIN',
        'descripcion': 'El escaner de recepcion no responde al registrar ingreso.',
    }
    respuesta = cliente.post('/api/tickets', json=payload)
    assert respuesta.status_code == 201
    ticket = respuesta.get_json()
    assert ticket['sla_horas'] == 2
    assert ticket['jira_issue_key'] == 'TSIE-99'
    assert ticket['jira_sincronizado'] is True


# Prueba 9: Regla de aprobacion obligatoria en Solicitudes de Acceso y Control de Cambios
def test_regla_aprobacion_acceso_service_desk(cliente):
    res_crear = cliente.post('/api/tickets', json={
        'id_usuario_solicitante': 2,
        'solicitante_username': 'operador_taller',
        'solicitante_nombre': 'Marcos Quispe',
        'tipo_solicitud': 'Acceso',
        'prioridad': 'Media',
        'area_origen': 'Ventas',
        'titulo': 'Acceso a exportacion de clientes corporativos',
        'descripcion': 'Solicitud temporal para auditoria.',
    })
    assert res_crear.status_code == 201
    id_ticket = res_crear.get_json()['id_ticket']

    # No debe permitir pasar directo a 'En atencion' sin aprobacion previa
    res_bloqueado = cliente.put(f'/api/tickets/{id_ticket}/estado', json={
        'estado': 'En atencion',
        'id_usuario': 3,
        'username': 'soporte_ti',
        'nombre_completo': 'Ing. Luis Mamani (Soporte TI)',
        'rol': 'TI',
    })
    assert res_bloqueado.status_code == 400

    # Aprobar primero como Gerente y luego atender
    res_aprobado = cliente.put(f'/api/tickets/{id_ticket}/estado', json={
        'estado': 'Aprobado',
        'id_usuario': 1,
        'username': 'admin_gerente',
        'nombre_completo': 'Ing. Carlos Mendoza (Gerente)',
        'rol': 'Gerente',
        'comentario': 'Aprobado por 48 horas bajo minimo privilegio.',
    })
    assert res_aprobado.status_code == 200
    assert res_aprobado.get_json()['estado'] == 'Aprobado'


# Prueba 10: Endpoint de metricas Prometheus (/metrics) y estado de Redis en /api/health
def test_endpoint_metricas_prometheus_y_health(cliente):
    res_health = cliente.get('/api/health')
    assert res_health.status_code == 200
    datos_health = res_health.get_json()
    assert 'redis' in datos_health

    res_metrics = cliente.get('/metrics')
    assert res_metrics.status_code == 200
    cuerpo = res_metrics.get_data(as_text=True)
    assert 'toyota_http_requests_total' in cuerpo
    assert 'toyota_http_request_duration_seconds' in cuerpo


# Prueba 11: Cache Redis (HIT/MISS e invalidacion en escritura)
def test_cache_redis_hit_miss_e_invalidacion(cliente, monkeypatch):
    from servicios.CacheService import CacheService

    almacen_falso = {}

    def fake_get(cls, clave):
        return almacen_falso.get(clave)

    def fake_set(cls, clave, valor, ttl_segundos=30):
        almacen_falso[clave] = valor
        return True

    def fake_del(cls, *claves):
        for c in claves:
            almacen_falso.pop(c, None)
        return True

    monkeypatch.setattr(CacheService, 'obtener_json', classmethod(fake_get))
    monkeypatch.setattr(CacheService, 'guardar_json', classmethod(fake_set))
    monkeypatch.setattr(CacheService, 'invalidar', classmethod(fake_del))

    r1 = cliente.get('/api/dashboard')
    assert r1.status_code == 200
    assert r1.headers.get('X-Cache') == 'MISS'

    r2 = cliente.get('/api/dashboard')
    assert r2.status_code == 200
    assert r2.headers.get('X-Cache') == 'HIT'

    # Al registrar un ticket nuevo se invalida el cache de metricas TI
    almacen_falso['tickets_metricas'] = {'totalTickets': 99}
    cliente.post('/api/tickets', json={
        'titulo': 'Test invalidacion cache',
        'descripcion': 'Prueba unitaria de invalidacion',
    })
    assert 'tickets_metricas' not in almacen_falso
