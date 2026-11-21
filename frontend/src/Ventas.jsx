import React, { useState, useEffect } from 'react';
import {
  apiObtenerVentas,
  apiObtenerClientes,
  apiObtenerInventario,
  apiCrearVenta,
  apiCrearCliente,
  apiActualizarEstadoVenta
} from './servicios/api';

/* Componente del modulo de Marketing y Ventas */
export default function Ventas({ usuario }) {
  /* Lista principal de transacciones de ventas */
  const [ventas, setVentas] = useState([]);
  /* Lista de clientes disponibles para cotizar */
  const [clientes, setClientes] = useState([]);
  /* Lista de vehiculos disponibles en inventario */
  const [vehiculos, setVehiculos] = useState([]);

  /* Estados para el formulario de nueva venta */
  const [idCliente, setIdCliente] = useState('');
  const [idItem, setIdItem] = useState('');
  const [precioTotal, setPrecioTotal] = useState('');
  const [estadoVenta, setEstadoVenta] = useState('Cotizado');

  /* Estados para creacion rapida de cliente nuevo */
  const [mostrarNuevoCliente, setMostrarNuevoCliente] = useState(false);
  const [nuevoDni, setNuevoDni] = useState('');
  const [nuevoNombre, setNuevoNombre] = useState('');
  const [nuevoTelefono, setNuevoTelefono] = useState('');
  const [nuevoTipo, setNuevoTipo] = useState('Particular');

  /* Estado para mensajes de confirmacion o alerta */
  const [notificacion, setNotificacion] = useState({ tipo: '', mensaje: '' });

  /* Cargar datos iniciales al montar la vista */
  useEffect(() => {
    cargarDatos();
  }, []);

  /* Funcion para consultar ventas, clientes e inventario */
  const cargarDatos = async () => {
    try {
      const listaVentas = await apiObtenerVentas();
      const listaClientes = await apiObtenerClientes();
      const listaInventario = await apiObtenerInventario();
      setVentas(listaVentas);
      setClientes(listaClientes);
      /* Filtrar unicamente los items de tipo Vehiculo */
      setVehiculos(listaInventario.filter(item => item.tipo === 'Vehiculo'));
    } catch (err) {
      console.error('Error al cargar datos de ventas:', err);
    }
  };

  /* Actualizar el precio sugerido automaticamente cuando el usuario selecciona un vehiculo */
  const manejarSeleccionVehiculo = (idSeleccionado) => {
    setIdItem(idSeleccionado);
    const seleccionado = vehiculos.find(v => Number(v.id_item) === Number(idSeleccionado));
    if (seleccionado) {
      setPrecioTotal(seleccionado.precio_usd);
    }
  };

  /* Registrar un nuevo cliente desde el formulario rapido */
  const registrarClienteRapido = async (e) => {
    e.preventDefault();
    if (!nuevoDni || !nuevoNombre) return;
    try {
      const clienteCreado = await apiCrearCliente({
        dni_ruc: nuevoDni,
        nombre_razon: nuevoNombre,
        telefono: nuevoTelefono,
        email: 'contacto@cliente.pe',
        tipo_cliente: nuevoTipo
      });
      setClientes(prev => [clienteCreado, ...prev]);
      setIdCliente(clienteCreado.id_cliente);
      setMostrarNuevoCliente(false);
      setNuevoDni('');
      setNuevoNombre('');
      setNuevoTelefono('');
      setNotificacion({ tipo: 'exito', mensaje: 'Cliente registrado correctamente.' });
    } catch (err) {
      setNotificacion({ tipo: 'error', mensaje: 'Error al registrar el cliente.' });
    }
  };

  /* Registrar una nueva cotizacion o venta */
  const registrarOperacionVenta = async (e) => {
    e.preventDefault();
    if (!idCliente || !idItem || !precioTotal) {
      setNotificacion({ tipo: 'error', mensaje: 'Por favor complete todos los campos requeridos.' });
      return;
    }

    const clienteObj = clientes.find(c => Number(c.id_cliente) === Number(idCliente));
    const vehiculoObj = vehiculos.find(v => Number(v.id_item) === Number(idItem));

    /* Validar disponibilidad de stock si se intenta registrar directamente como Vendido */
    if (estadoVenta === 'Vendido' && vehiculoObj && vehiculoObj.stock_actual <= 0) {
      setNotificacion({ tipo: 'error', mensaje: 'No hay stock disponible para concretar la venta de este modelo.' });
      return;
    }

    try {
      await apiCrearVenta({
        id_cliente: Number(idCliente),
        cliente_nombre: clienteObj ? clienteObj.nombre_razon : 'Cliente',
        id_item: Number(idItem),
        vehiculo_nombre: vehiculoObj ? vehiculoObj.nombre_modelo : 'Vehículo',
        precio_total: Number(precioTotal),
        estado: estadoVenta
      }, usuario?.username || 'sistema');

      setNotificacion({
        tipo: 'exito',
        mensaje: estadoVenta === 'Vendido'
          ? '¡Venta completada con éxito! Se descontó 1 unidad del inventario.'
          : 'Cotización guardada exitosamente.'
      });

      /* Limpiar formulario y recargar datos */
      setIdCliente('');
      setIdItem('');
      setPrecioTotal('');
      setEstadoVenta('Cotizado');
      cargarDatos();
    } catch (err) {
      setNotificacion({ tipo: 'error', mensaje: 'Error al procesar la operación de venta.' });
    }
  };

  /* Confirmar el cierre de una venta y descontar stock */
  const confirmarVenta = async (idVenta) => {
    try {
      await apiActualizarEstadoVenta(idVenta, 'Vendido', usuario?.username || 'sistema');
      setNotificacion({ tipo: 'exito', mensaje: 'Venta confirmada. Stock actualizado en almacén.' });
      cargarDatos();
    } catch (err) {
      setNotificacion({ tipo: 'error', mensaje: 'Error al confirmar la venta.' });
    }
  };

  return (
    <div className="vista-interior">
      <div>
        <h2>Gestión Comercial: Marketing y Ventas</h2>
        <p style={{ color: 'var(--color-texto-muted)', fontSize: '0.9rem' }}>
          Registro de clientes, emisión de cotizaciones y cierre transaccional de ventas de vehículos
        </p>
      </div>

      {/* Alerta dinamica de exito o error */}
      {notificacion.mensaje && (
        <div className={`mensaje-alerta ${notificacion.tipo}`}>
          {notificacion.mensaje}
        </div>
      )}

      {/* Tarjeta de formulario para nueva cotizacion o venta */}
      <div className="tarjeta">
        <div className="tarjeta-encabezado">
          <h3>Nueva Cotización / Venta de Unidad</h3>
          <button
            type="button"
            className="btn btn-secundario btn-sm"
            onClick={() => setMostrarNuevoCliente(!mostrarNuevoCliente)}
          >
            {mostrarNuevoCliente ? 'Cancelar Nuevo Cliente' : '+ Registrar Nuevo Cliente'}
          </button>
        </div>

        {/* Formulario desplegable para registrar cliente nuevo si no existe en la lista */}
        {mostrarNuevoCliente && (
          <form onSubmit={registrarClienteRapido} style={{ marginBottom: '1.5rem', padding: '1rem', background: '#F8FAFC', borderRadius: '6px' }}>
            <h4 style={{ marginBottom: '0.75rem', fontSize: '0.9rem', color: 'var(--color-secundario)' }}>Datos del Nuevo Cliente</h4>
            <div className="formulario-grid">
              <div className="campo-grupo">
                <label>DNI o RUC</label>
                <input
                  type="text"
                  placeholder="Ej. 20601234567"
                  value={nuevoDni}
                  onChange={(e) => setNuevoDni(e.target.value)}
                  required
                />
              </div>
              <div className="campo-grupo">
                <label>Nombre o Razón Social</label>
                <input
                  type="text"
                  placeholder="Ej. Juan Perez o Empresa SAC"
                  value={nuevoNombre}
                  onChange={(e) => setNuevoNombre(e.target.value)}
                  required
                />
              </div>
              <div className="campo-grupo">
                <label>Teléfono</label>
                <input
                  type="text"
                  placeholder="Ej. 958123456"
                  value={nuevoTelefono}
                  onChange={(e) => setNuevoTelefono(e.target.value)}
                />
              </div>
              <div className="campo-grupo">
                <label>Tipo</label>
                <select value={nuevoTipo} onChange={(e) => setNuevoTipo(e.target.value)}>
                  <option value="Particular">Particular</option>
                  <option value="Corporativo">Corporativo</option>
                </select>
              </div>
              <button type="submit" className="btn btn-primario btn-sm">Guardar Cliente</button>
            </div>
          </form>
        )}

        {/* Formulario principal de venta */}
        <form onSubmit={registrarOperacionVenta} className="formulario-grid">
          <div className="campo-grupo">
            <label htmlFor="cliente-select">Cliente</label>
            <select
              id="cliente-select"
              value={idCliente}
              onChange={(e) => setIdCliente(e.target.value)}
              required
            >
              <option value="">-- Seleccione Cliente --</option>
              {clientes.map(c => (
                <option key={c.id_cliente} value={c.id_cliente}>
                  {c.nombre_razon} ({c.dni_ruc})
                </option>
              ))}
            </select>
          </div>

          <div className="campo-grupo">
            <label htmlFor="vehiculo-select">Modelo Toyota</label>
            <select
              id="vehiculo-select"
              value={idItem}
              onChange={(e) => manejarSeleccionVehiculo(e.target.value)}
              required
            >
              <option value="">-- Seleccione Modelo --</option>
              {vehiculos.map(v => (
                <option key={v.id_item} value={v.id_item}>
                  {v.nombre_modelo} (Stock: {v.stock_actual})
                </option>
              ))}
            </select>
          </div>

          <div className="campo-grupo">
            <label htmlFor="precio-input">Precio Final ($ USD)</label>
            <input
              id="precio-input"
              type="number"
              step="0.01"
              placeholder="0.00"
              value={precioTotal}
              onChange={(e) => setPrecioTotal(e.target.value)}
              required
            />
          </div>

          <div className="campo-grupo">
            <label htmlFor="estado-select">Estado Inicial</label>
            <select
              id="estado-select"
              value={estadoVenta}
              onChange={(e) => setEstadoVenta(e.target.value)}
            >
              <option value="Cotizado">Cotizado</option>
              <option value="Prospecto">Prospecto</option>
              <option value="Vendido">Vendido (Descuenta Stock)</option>
            </select>
          </div>

          <button type="submit" className="btn btn-primario">
            Guardar Operación
          </button>
        </form>
      </div>

      {/* Tabla con el historial de cotizaciones y ventas */}
      <div className="tarjeta">
        <div className="tarjeta-encabezado">
          <h3>Historial de Cotizaciones y Ventas</h3>
          <span className="badge badge-neutro">{ventas.length} registros</span>
        </div>
        <div className="tabla-contenedor">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Fecha</th>
                <th>Cliente</th>
                <th>Vehículo</th>
                <th>Monto (USD)</th>
                <th>Estado</th>
                <th className="no-imprimir">Acción</th>
              </tr>
            </thead>
            <tbody>
              {ventas.map((v) => (
                <tr key={v.id_venta}>
                  <td>#{v.id_venta}</td>
                  <td>{v.fecha}</td>
                  <td><strong>{v.cliente_nombre}</strong></td>
                  <td>{v.vehiculo_nombre}</td>
                  <td>${Number(v.precio_total).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  <td>
                    <span className={`badge ${v.estado === 'Vendido' ? 'badge-exito' : v.estado === 'Cotizado' ? 'badge-proceso' : 'badge-neutro'}`}>
                      {v.estado}
                    </span>
                  </td>
                  <td className="no-imprimir">
                    {/* Boton para cerrar venta si aun esta pendiente */}
                    {v.estado !== 'Vendido' ? (
                      <button
                        onClick={() => confirmarVenta(v.id_venta)}
                        className="btn btn-exito btn-sm"
                        title="Confirmar venta y descontar stock"
                      >
                        ✓ Cerrar Venta
                      </button>
                    ) : (
                      <span style={{ fontSize: '0.8rem', color: 'var(--color-exito)', fontWeight: 'bold' }}>Facturado</span>
                    )}
                  </td>
                </tr>
              ))}
              {ventas.length === 0 && (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '1.5rem' }}>No hay ventas registradas</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
