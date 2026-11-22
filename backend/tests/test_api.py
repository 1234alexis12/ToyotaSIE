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
    # Obtiene el stock previo del item 1 (Toyota Hilux)
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
