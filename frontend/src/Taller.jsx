import React, { useState, useEffect } from 'react';
import {
  apiObtenerOrdenesTaller,
  apiObtenerClientes,
  apiObtenerInventario,
  apiCrearOrdenTaller,
  apiActualizarEstadoTaller
} from './servicios/api';

/* Componente del modulo de Produccion y Operaciones: Taller Tecnico y Posventa */
export default function Taller({ usuario }) {
  /* Lista de ordenes de trabajo registradas */
  const [ordenes, setOrdenes] = useState([]);
  /* Clientes disponibles */
  const [clientes, setClientes] = useState([]);
  /* Repuestos disponibles para consumir en la orden */
  const [repuestos, setRepuestos] = useState([]);

  /* Estados para el formulario de orden de servicio */
  const [idCliente, setIdCliente] = useState('');
  const [placaVin, setPlacaVin] = useState('');
  const [tipoServicio, setTipoServicio] = useState('Mantenimiento Preventivo (10,000 km)');
  const [tecnico, setTecnico] = useState('Tec. Manuel Salinas');
  const [idRepuesto, setIdRepuesto] = useState('');
  const [costoUsd, setCostoUsd] = useState('120.00');
  const [estadoOrden, setEstadoOrden] = useState('Pendiente');

  /* Notificacion de alerta */
  const [notificacion, setNotificacion] = useState({ tipo: '', mensaje: '' });

  /* Cargar datos iniciales */
  useEffect(() => {
    cargarDatos();
  }, []);

  /* Consultar ordenes, clientes y repuestos */
  const cargarDatos = async () => {
    try {
      const listaOrdenes = await apiObtenerOrdenesTaller();
      const listaClientes = await apiObtenerClientes();
      const listaInventario = await apiObtenerInventario();
      setOrdenes(listaOrdenes);
      setClientes(listaClientes);
      /* Filtrar solo repuestos con existencias */
      setRepuestos(listaInventario.filter(i => i.tipo === 'Repuesto'));
    } catch (err) {
      console.error('Error al cargar datos del taller:', err);
    }
  };

  /* Registrar una nueva orden de servicio en taller */
  const registrarOrdenServicio = async (e) => {
    e.preventDefault();
    if (!idCliente || !placaVin || !costoUsd) {
      setNotificacion({ tipo: 'error', mensaje: 'Por favor complete cliente, placa/VIN y costo.' });
      return;
    }

    const clienteObj = clientes.find(c => Number(c.id_cliente) === Number(idCliente));
    const repuestoObj = repuestos.find(r => Number(r.id_item) === Number(idRepuesto));

    try {
      await apiCrearOrdenTaller({
        id_cliente: Number(idCliente),
        cliente_nombre: clienteObj ? clienteObj.nombre_razon : 'Cliente',
        placa_vin: placaVin.toUpperCase(),
        tipo_servicio: tipoServicio,
        tecnico,
        id_item_repuesto: idRepuesto ? Number(idRepuesto) : null,
        repuesto_nombre: repuestoObj ? repuestoObj.nombre_modelo : 'Ninguno / Mano de Obra',
        costo_usd: Number(costoUsd),
        estado: estadoOrden
      }, usuario?.username || 'sistema');

      setNotificacion({
        tipo: 'exito',
        mensaje: idRepuesto
          ? 'Orden creada. Se descontó automáticamente 1 unidad del repuesto asignado.'
          : 'Orden de servicio creada con éxito.'
      });

      /* Restablecer formulario y refrescar listado */
      setIdCliente('');
      setPlacaVin('');
      setIdRepuesto('');
      setCostoUsd('120.00');
      setEstadoOrden('Pendiente');
      cargarDatos();
    } catch (err) {
      setNotificacion({ tipo: 'error', mensaje: 'Error al registrar la orden de taller.' });
    }
  };

  /* Cambiar estado de la orden de taller (En proceso / Entregado) */
  const cambiarEstado = async (idOrden, nuevoEstado) => {
    try {
      await apiActualizarEstadoTaller(idOrden, nuevoEstado, usuario?.username || 'sistema');
      setNotificacion({ tipo: 'exito', mensaje: `Orden #${idOrden} actualizada a estado: ${nuevoEstado}` });
      cargarDatos();
    } catch (err) {
      setNotificacion({ tipo: 'error', mensaje: 'Error al actualizar estado de la orden.' });
    }
  };

  return (
    <div className="vista-interior">
      <div>
        <h2>Operaciones de Taller y Servicio Técnico</h2>
        <p style={{ color: 'var(--color-texto-muted)', fontSize: '0.9rem' }}>
          Gestión de Órdenes de Trabajo (OT), inspecciones PDI, mantenimiento y control de repuestos consumidos
        </p>
      </div>

      {/* Alerta dinamica */}
      {notificacion.mensaje && (
        <div className={`mensaje-alerta ${notificacion.tipo}`}>
          {notificacion.mensaje}
        </div>
      )}

      {/* Formulario para apertura de orden de servicio */}
      <div className="tarjeta">
        <div className="tarjeta-encabezado">
          <h3>Apertura de Orden de Trabajo (OT)</h3>
        </div>
        <form onSubmit={registrarOrdenServicio} className="formulario-grid">
          <div className="campo-grupo">
            <label htmlFor="taller-cliente">Propietario / Cliente</label>
            <select
              id="taller-cliente"
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
            <label htmlFor="taller-placa">Placa o VIN del Vehículo</label>
            <input
              id="taller-placa"
              type="text"
              placeholder="Ej. V9A-782 o 8AJBA3CD4..."
              value={placaVin}
              onChange={(e) => setPlacaVin(e.target.value)}
              required
            />
          </div>

          <div className="campo-grupo">
            <label htmlFor="taller-servicio">Tipo de Servicio</label>
            <select
              id="taller-servicio"
              value={tipoServicio}
              onChange={(e) => setTipoServicio(e.target.value)}
            >
              <option value="Mantenimiento Preventivo (5,000 km)">Mantenimiento Preventivo (5,000 km)</option>
              <option value="Mantenimiento Preventivo (10,000 km)">Mantenimiento Preventivo (10,000 km)</option>
              <option value="PDI (Inspeccion Pre-Entrega)">PDI (Inspección Pre-Entrega)</option>
              <option value="Reparacion de Frenos">Reparación Sistema de Frenos</option>
              <option value="Diagnostico Computarizado">Diagnóstico Computarizado</option>
            </select>
          </div>

          <div className="campo-grupo">
            <label htmlFor="taller-tecnico">Técnico Mecánico</label>
            <select
              id="taller-tecnico"
              value={tecnico}
              onChange={(e) => setTecnico(e.target.value)}
            >
              <option value="Tec. Manuel Salinas">Tec. Manuel Salinas (Especialista Hilux/Prado)</option>
              <option value="Tec. David Paredes">Tec. David Paredes (Técnico Híbridos/PDI)</option>
              <option value="Tec. Jorge Huanca">Tec. Jorge Huanca (Mecánico General)</option>
            </select>
          </div>

          <div className="campo-grupo">
            <label htmlFor="taller-repuesto">Repuesto OEM Asignado</label>
            <select
              id="taller-repuesto"
              value={idRepuesto}
              onChange={(e) => setIdRepuesto(e.target.value)}
            >
              <option value="">-- Ninguno / Solo Mano de Obra --</option>
              {repuestos.map(r => (
                <option key={r.id_item} value={r.id_item}>
                  {r.nombre_modelo} (Stock: {r.stock_actual})
                </option>
              ))}
            </select>
          </div>

          <div className="campo-grupo">
            <label htmlFor="taller-costo">Costo Total ($ USD)</label>
            <input
              id="taller-costo"
              type="number"
              step="0.01"
              value={costoUsd}
              onChange={(e) => setCostoUsd(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn btn-primario">
            + Crear Orden de Taller
          </button>
        </form>
      </div>

      {/* Tabla de seguimiento operativo de ordenes en taller */}
      <div className="tarjeta">
        <div className="tarjeta-encabezado">
          <h3>Órdenes de Trabajo en Curso</h3>
          <span className="badge badge-neutro">{ordenes.length} órdenes</span>
        </div>
        <div className="tabla-contenedor">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Fecha</th>
                <th>Placa / VIN</th>
                <th>Cliente</th>
                <th>Servicio</th>
                <th>Técnico</th>
                <th>Repuesto Consumido</th>
                <th>Total (USD)</th>
                <th>Estado</th>
                <th className="no-imprimir">Actualizar</th>
              </tr>
            </thead>
            <tbody>
              {ordenes.map((o) => (
                <tr key={o.id_orden}>
                  <td>#{o.id_orden}</td>
                  <td>{o.fecha_ingreso}</td>
                  <td><strong>{o.placa_vin}</strong></td>
                  <td>{o.cliente_nombre}</td>
                  <td>{o.tipo_servicio}</td>
                  <td>{o.tecnico}</td>
                  <td>{o.repuesto_nombre}</td>
                  <td>${Number(o.costo_usd).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  <td>
                    <span className={`badge ${o.estado === 'Entregado' ? 'badge-exito' : o.estado === 'En proceso' ? 'badge-proceso' : 'badge-alerta'}`}>
                      {o.estado}
                    </span>
                  </td>
                  <td className="no-imprimir" style={{ display: 'flex', gap: '0.4rem' }}>
                    {/* Boton para avanzar a En Proceso */}
                    {o.estado === 'Pendiente' && (
                      <button
                        onClick={() => cambiarEstado(o.id_orden, 'En proceso')}
                        className="btn btn-secundario btn-sm"
                      >
                        Iniciar
                      </button>
                    )}
                    {/* Boton para culminar entrega */}
                    {o.estado !== 'Entregado' && (
                      <button
                        onClick={() => cambiarEstado(o.id_orden, 'Entregado')}
                        className="btn btn-exito btn-sm"
                      >
                        Entregar
                      </button>
                    )}
                    {o.estado === 'Entregado' && (
                      <span style={{ fontSize: '0.8rem', color: 'var(--color-exito)', fontWeight: 'bold' }}>Finalizado</span>
                    )}
                  </td>
                </tr>
              ))}
              {ordenes.length === 0 && (
                <tr>
                  <td colSpan="10" style={{ textAlign: 'center', padding: '1.5rem' }}>No hay órdenes registradas en taller</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
