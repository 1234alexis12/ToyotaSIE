import React, { useState, useEffect } from 'react';
import { apiObtenerAuditoria } from './servicios/api';

/* Componente del modulo de Seguridad de la Informacion y Auditoria (ISO 27001) */
export default function Auditoria({ usuario }) {
  /* Lista de eventos registrados en la bitacora */
  const [logs, setLogs] = useState([]);
  /* Filtro por modulo */
  const [filtroModulo, setFiltroModulo] = useState('TODOS');
  /* Termino de busqueda general */
  const [busqueda, setBusqueda] = useState('');

  /* Cargar bitacora al montar la vista */
  useEffect(() => {
    cargarLogs();
  }, []);

  /* Consultar eventos de auditoria */
  const cargarLogs = async () => {
    try {
      const datos = await apiObtenerAuditoria();
      setLogs(datos);
    } catch (err) {
      console.error('Error al cargar auditoria:', err);
    }
  };

  /* Filtrar logs segun seleccion de modulo y termino de busqueda */
  const logsFiltrados = logs.filter(log => {
    const coincideModulo = filtroModulo === 'TODOS' || log.modulo === filtroModulo;
    const coincideBusqueda =
      log.username.toLowerCase().includes(busqueda.toLowerCase()) ||
      log.detalle.toLowerCase().includes(busqueda.toLowerCase()) ||
      log.accion.toLowerCase().includes(busqueda.toLowerCase());
    return coincideModulo && coincideBusqueda;
  });

  return (
    <div className="vista-interior">
      <div>
        <h2>Seguridad de la Información y Bitácora de Auditoría</h2>
        <p style={{ color: 'var(--color-texto-muted)', fontSize: '0.9rem' }}>
          Trazabilidad de operaciones, accesos y cambios en el sistema conforme a la norma ISO/IEC 27001 (Control A.12.4)
        </p>
      </div>

      {/* Tarjeta informativa de gobernanza y cumplimiento normativo */}
      <div className="tarjeta" style={{ borderLeft: '5px solid #0284C7', backgroundColor: '#F0F9FF' }}>
        <h4 style={{ color: '#0369A1', marginBottom: '0.35rem' }}>Cumplimiento Normativo ISO 27001 y Ley N.° 29733</h4>
        <p style={{ fontSize: '0.85rem', color: '#0C4A6E' }}>
          Este módulo audita de forma inmutable cada intento de autenticación, transacción comercial, modificación de inventario y orden de servicio técnico. Cada registro vincula la marca de tiempo, el usuario responsable y el detalle de la acción para fines de no repudio.
        </p>
      </div>

      {/* Tabla de registros de auditoria */}
      <div className="tarjeta">
        <div className="tarjeta-encabezado" style={{ flexWrap: 'wrap', gap: '1rem' }}>
          <h3>Registro Histórico de Auditoría (Logs)</h3>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <input
              type="text"
              placeholder="🔍 Buscar en logs..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              style={{ padding: '0.45rem 0.75rem', border: '1px solid var(--color-borde)', borderRadius: '4px', fontSize: '0.85rem' }}
            />
            <select
              value={filtroModulo}
              onChange={(e) => setFiltroModulo(e.target.value)}
              style={{ padding: '0.45rem 0.75rem', border: '1px solid var(--color-borde)', borderRadius: '4px', fontSize: '0.85rem' }}
            >
              <option value="TODOS">Todos los Módulos</option>
              <option value="SEGURIDAD">Seguridad / Login</option>
              <option value="VENTAS">Marketing y Ventas</option>
              <option value="LOGISTICA">Logística / Almacén</option>
              <option value="TALLER">Taller / Operaciones</option>
              <option value="TI_SERVICEDESK">Área de TI / Service Desk</option>
            </select>
          </div>
        </div>

        <div className="tabla-contenedor">
          <table>
            <thead>
              <tr>
                <th>ID Log</th>
                <th>Fecha y Hora</th>
                <th>Usuario</th>
                <th>Módulo</th>
                <th>Acción</th>
                <th>Detalle Técnico del Evento</th>
              </tr>
            </thead>
            <tbody>
              {logsFiltrados.map((log) => (
                <tr key={log.id_log}>
                  <td><code>#{log.id_log}</code></td>
                  <td>{log.fecha_hora}</td>
                  <td><strong>{log.username}</strong></td>
                  <td>
                    <span className="badge badge-neutro">{log.modulo}</span>
                  </td>
                  <td>
                    <span className={`badge ${log.accion.includes('LOGIN') ? 'badge-exito' : log.accion.includes('UPDATE') ? 'badge-proceso' : 'badge-neutro'}`}>
                      {log.accion}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.85rem' }}>{log.detalle}</td>
                </tr>
              ))}
              {logsFiltrados.length === 0 && (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '1.5rem' }}>No hay registros en la bitácora con los filtros aplicados</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
