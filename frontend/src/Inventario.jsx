import React, { useState, useEffect } from 'react';
import { apiObtenerInventario, apiCrearItemInventario } from './servicios/api';

/* Componente del modulo de Distribucion, Logistica y Almacen */
export default function Inventario({ usuario }) {
  /* Lista completa de existencias en el inventario */
  const [inventario, setInventario] = useState([]);
  /* Termino de busqueda para filtrar por codigo o descripcion */
  const [busqueda, setBusqueda] = useState('');
  /* Filtro por categoria (Todos, Vehiculo, Repuesto) */
  const [filtroTipo, setFiltroTipo] = useState('Todos');

  /* Estados para el formulario de nuevo item */
  const [codigo, setCodigo] = useState('');
  const [tipo, setTipo] = useState('Vehiculo');
  const [nombreModelo, setNombreModelo] = useState('');
  const [stockActual, setStockActual] = useState('');
  const [stockMinimo, setStockMinimo] = useState('');
  const [precioUsd, setPrecioUsd] = useState('');

  /* Estado de notificacion */
  const [notificacion, setNotificacion] = useState({ tipo: '', mensaje: '' });

  /* Cargar datos del inventario al inicializar */
  useEffect(() => {
    cargarInventario();
  }, []);

  /* Consultar existencias desde el backend o almacenamiento local */
  const cargarInventario = async () => {
    try {
      const datos = await apiObtenerInventario();
      setInventario(datos);
    } catch (err) {
      console.error('Error al cargar inventario:', err);
    }
  };

  /* Registrar un nuevo item en el inventario */
  const registrarItem = async (e) => {
    e.preventDefault();
    if (!codigo || !nombreModelo || !stockActual || !stockMinimo || !precioUsd) {
      setNotificacion({ tipo: 'error', mensaje: 'Por favor complete todos los datos del ítem.' });
      return;
    }

    try {
      await apiCrearItemInventario({
        codigo_vin_sku: codigo,
        tipo,
        nombre_modelo: nombreModelo,
        stock_actual: Number(stockActual),
        stock_minimo: Number(stockMinimo),
        precio_usd: Number(precioUsd)
      });

      setNotificacion({ tipo: 'exito', mensaje: 'Ítem agregado exitosamente al inventario.' });

      /* Limpiar campos del formulario */
      setCodigo('');
      setNombreModelo('');
      setStockActual('');
      setStockMinimo('');
      setPrecioUsd('');
      cargarInventario();
    } catch (err) {
      setNotificacion({ tipo: 'error', mensaje: 'Error al registrar el ítem en inventario.' });
    }
  };

  /* Filtrado dinamico en tiempo real por busqueda y tipo */
  const itemsFiltrados = inventario.filter(item => {
    const coincideTipo = filtroTipo === 'Todos' || item.tipo === filtroTipo;
    const coincideTexto =
      item.nombre_modelo.toLowerCase().includes(busqueda.toLowerCase()) ||
      item.codigo_vin_sku.toLowerCase().includes(busqueda.toLowerCase());
    return coincideTipo && coincideTexto;
  });

  return (
    <div className="vista-interior">
      <div>
        <h2>Logística y Control de Almacén</h2>
        <p style={{ color: 'var(--color-texto-muted)', fontSize: '0.9rem' }}>
          Gestión de inventario de vehículos (VIN) y repuestos originales OEM con monitoreo de stock de seguridad
        </p>
      </div>

      {/* Alerta de accion exitosa o error */}
      {notificacion.mensaje && (
        <div className={`mensaje-alerta ${notificacion.tipo}`}>
          {notificacion.mensaje}
        </div>
      )}

      {/* Formulario de registro de nuevas unidades o repuestos */}
      <div className="tarjeta">
        <div className="tarjeta-encabezado">
          <h3>Registrar Nuevo Ítem en Almacén</h3>
        </div>
        <form onSubmit={registrarItem} className="formulario-grid">
          <div className="campo-grupo">
            <label htmlFor="item-tipo">Tipo de Ítem</label>
            <select id="item-tipo" value={tipo} onChange={(e) => setTipo(e.target.value)}>
              <option value="Vehiculo">Vehículo (Código VIN)</option>
              <option value="Repuesto">Repuesto OEM (Código SKU)</option>
            </select>
          </div>

          <div className="campo-grupo">
            <label htmlFor="item-codigo">Código VIN / SKU</label>
            <input
              id="item-codigo"
              type="text"
              placeholder={tipo === 'Vehiculo' ? 'Ej. 8AJBA3CD4P...' : 'Ej. SKU-04152-YZZA6'}
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              required
            />
          </div>

          <div className="campo-grupo">
            <label htmlFor="item-nombre">Descripción / Modelo</label>
            <input
              id="item-nombre"
              type="text"
              placeholder="Ej. Toyota Hilux 4x4 o Filtro Aceite"
              value={nombreModelo}
              onChange={(e) => setNombreModelo(e.target.value)}
              required
            />
          </div>

          <div className="campo-grupo">
            <label htmlFor="item-stock">Stock Actual</label>
            <input
              id="item-stock"
              type="number"
              min="0"
              placeholder="0"
              value={stockActual}
              onChange={(e) => setStockActual(e.target.value)}
              required
            />
          </div>

          <div className="campo-grupo">
            <label htmlFor="item-minimo">Stock Mínimo</label>
            <input
              id="item-minimo"
              type="number"
              min="1"
              placeholder="1"
              value={stockMinimo}
              onChange={(e) => setStockMinimo(e.target.value)}
              required
            />
          </div>

          <div className="campo-grupo">
            <label htmlFor="item-precio">Precio Unitario ($ USD)</label>
            <input
              id="item-precio"
              type="number"
              step="0.01"
              placeholder="0.00"
              value={precioUsd}
              onChange={(e) => setPrecioUsd(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn btn-primario">
            + Añadir a Almacén
          </button>
        </form>
      </div>

      {/* Tabla de existencias con filtros y alertas visuales */}
      <div className="tarjeta">
        <div className="tarjeta-encabezado" style={{ flexWrap: 'wrap', gap: '1rem' }}>
          <h3>Catálogo de Existencias</h3>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            {/* Buscador por texto */}
            <input
              type="text"
              placeholder="🔍 Buscar por nombre o VIN/SKU..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              style={{ padding: '0.45rem 0.75rem', border: '1px solid var(--color-borde)', borderRadius: '4px', fontSize: '0.85rem' }}
            />
            {/* Filtro por tipo de producto */}
            <select
              value={filtroTipo}
              onChange={(e) => setFiltroTipo(e.target.value)}
              style={{ padding: '0.45rem 0.75rem', border: '1px solid var(--color-borde)', borderRadius: '4px', fontSize: '0.85rem' }}
            >
              <option value="Todos">Todos</option>
              <option value="Vehiculo">Solo Vehículos</option>
              <option value="Repuesto">Solo Repuestos</option>
            </select>
          </div>
        </div>

        <div className="tabla-contenedor">
          <table>
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Código VIN / SKU</th>
                <th>Descripción / Modelo</th>
                <th>Stock Actual</th>
                <th>Stock Mínimo</th>
                <th>Precio Unitario (USD)</th>
                <th>Estado de Reposición</th>
              </tr>
            </thead>
            <tbody>
              {itemsFiltrados.map((item) => {
                /* Condicion de alerta: Si el stock actual es menor o igual al minimo requerido */
                const esAlertaCritica = Number(item.stock_actual) <= Number(item.stock_minimo);
                return (
                  <tr key={item.id_item} className={esAlertaCritica ? 'fila-alerta' : ''}>
                    <td>
                      <span className={`badge ${item.tipo === 'Vehiculo' ? 'badge-neutro' : 'badge-proceso'}`}>
                        {item.tipo}
                      </span>
                    </td>
                    <td><code>{item.codigo_vin_sku}</code></td>
                    <td><strong>{item.nombre_modelo}</strong></td>
                    <td style={{ fontWeight: '700', color: esAlertaCritica ? 'var(--color-alerta)' : 'inherit' }}>
                      {item.stock_actual}
                    </td>
                    <td>{item.stock_minimo}</td>
                    <td>${Number(item.precio_usd).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                    <td>
                      {/* Etiqueta roja en caso de stock insuficiente */}
                      {esAlertaCritica ? (
                        <span className="badge badge-alerta">⚠️ Stock Bajo</span>
                      ) : (
                        <span className="badge badge-exito">✓ Abastecido</span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {itemsFiltrados.length === 0 && (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '1.5rem' }}>No se encontraron ítems con los criterios indicados</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
