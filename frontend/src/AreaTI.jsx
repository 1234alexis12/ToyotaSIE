import React, { useState, useEffect, useCallback } from 'react';
import {
  apiObtenerTickets,
  apiObtenerMetricasTI,
  apiObtenerDetalleTicket,
  apiActualizarEstadoTicket,
  apiSincronizarTicketJira,
  apiObtenerEstadoJira,
} from './servicios/api';

const ETAPAS_FLUJO = ['Solicitado', 'En evaluacion', 'Aprobado', 'En atencion', 'Cerrado'];

const TECNICOS_TI = [
  'Ing. Luis Mamani (Soporte TI)',
  'Ing. Sofía Quispe (Infraestructura & BD)',
  'Téc. Diego Torres (Mesa de Ayuda)',
];

/* Consola completa del Area de TI: Service Desk, Control de Cambios, SLA y Jira */
export default function AreaTI({ usuario, refrescoExterno }) {
  const [tickets, setTickets] = useState([]);
  const [metricas, setMetricas] = useState({
    ticketsAbiertos: 0,
    ticketsCriticos: 0,
    ticketsCerrados: 0,
    sincronizadosJira: 0,
  });
  const [estadoJira, setEstadoJira] = useState({ configurado: false, conectado: false, mensaje: '' });

  const [busqueda, setBusqueda] = useState('');
  const [filtroTipo, setFiltroTipo] = useState('TODOS');
  const [filtroEstado, setFiltroEstado] = useState('TODOS');

  const [seleccionado, setSeleccionado] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [tecnicoAsignado, setTecnicoAsignado] = useState(TECNICOS_TI[0]);
  const [comentarioAccion, setComentarioAccion] = useState('');
  const [notificacion, setNotificacion] = useState({ tipo: '', mensaje: '' });

  const cargarBandeja = useCallback(async () => {
    try {
      const [lista, kpis, jiraInfo] = await Promise.all([
        apiObtenerTickets(usuario?.id_usuario, usuario?.rol),
        apiObtenerMetricasTI(),
        apiObtenerEstadoJira(),
      ]);
      setTickets(lista);
      setMetricas(kpis);
      setEstadoJira(jiraInfo);
    } catch (err) {
      setNotificacion({ tipo: 'error', mensaje: err.message || 'Error al cargar el Área de TI.' });
    }
  }, [usuario]);

  useEffect(() => {
    cargarBandeja();
  }, [cargarBandeja, refrescoExterno]);

  const abrirDetalle = async (idTicket) => {
    setNotificacion({ tipo: '', mensaje: '' });
    try {
      const data = await apiObtenerDetalleTicket(idTicket);
      setSeleccionado(data.ticket);
      setHistorial(data.historial || []);
      setTecnicoAsignado(data.ticket.tecnico_ti_asignado || TECNICOS_TI[0]);
      setComentarioAccion('');
    } catch (err) {
      setNotificacion({ tipo: 'error', mensaje: err.message || 'No se pudo cargar el detalle.' });
    }
  };

  const cambiarEtapa = async (nuevoEstado) => {
    if (!seleccionado) return;
    if (nuevoEstado === 'Cerrado' && !comentarioAccion.trim() && !seleccionado.resolucion_evidencia) {
      setNotificacion({ tipo: 'error', mensaje: 'Ingrese la evidencia o descripción de la solución antes de cerrar el ticket.' });
      return;
    }

    try {
      await apiActualizarEstadoTicket(seleccionado.id_ticket, {
        estado: nuevoEstado,
        id_usuario: usuario.id_usuario,
        username: usuario.username,
        nombre_completo: usuario.nombre_completo,
        rol: usuario.rol,
        tecnico_ti_asignado: tecnicoAsignado,
        resolucion_evidencia: nuevoEstado === 'Cerrado' ? comentarioAccion.trim() : undefined,
        comentario: comentarioAccion.trim() || `Ticket movido a ${nuevoEstado}`,
      });

      setNotificacion({
        tipo: 'exito',
        mensaje: `Ticket ${seleccionado.codigo_ticket} actualizado a "${nuevoEstado}".`,
      });
      await cargarBandeja();
      await abrirDetalle(seleccionado.id_ticket);
    } catch (err) {
      setNotificacion({ tipo: 'error', mensaje: err.message || 'No se pudo cambiar el estado del ticket.' });
    }
  };

  const sincronizarConJira = async (idTicket) => {
    try {
      const res = await apiSincronizarTicketJira(idTicket);
      const extra = res.estado_jira ? ` (Estado en Jira: ${res.estado_jira})` : '';
      setNotificacion({
        tipo: 'exito',
        mensaje: (res.mensaje || 'Sincronización con Jira completada.') + extra,
      });
      await cargarBandeja();
      if (seleccionado && seleccionado.id_ticket === idTicket) {
        await abrirDetalle(idTicket);
      }
    } catch (err) {
      setNotificacion({ tipo: 'error', mensaje: err.message || 'No se pudo sincronizar con Jira.' });
    }
  };

  const ticketsFiltrados = tickets.filter((t) => {
    const coincideTipo = filtroTipo === 'TODOS' || t.tipo_solicitud === filtroTipo;
    const coincideEstado = filtroEstado === 'TODOS' || t.estado === filtroEstado;
    const texto = busqueda.toLowerCase();
    const coincideTexto =
      t.codigo_ticket.toLowerCase().includes(texto) ||
      t.titulo.toLowerCase().includes(texto) ||
      (t.solicitante_nombre || '').toLowerCase().includes(texto) ||
      (t.jira_issue_key || '').toLowerCase().includes(texto);
    return coincideTipo && coincideEstado && coincideTexto;
  });

  const esAprobador = usuario?.rol === 'Gerente' || usuario?.rol === 'TI';

  return (
    <div className="vista-interior">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2>Área de TI — Service Desk y Control de Cambios</h2>
          <p style={{ color: 'var(--color-texto-muted)', fontSize: '0.9rem' }}>
            Gestión integral de Incidentes, Solicitudes (Servicio/Información/Acceso), Control de Cambios, SLA y Jira Cloud
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <a
            href={typeof window !== 'undefined' ? `http://${window.location.hostname}:3001` : 'http://localhost:3001'}
            target="_blank"
            rel="noreferrer"
            className="btn btn-secundario btn-sm"
            style={{ textDecoration: 'none' }}
          >
            📈 Abrir Grafana (Rendimiento)
          </a>
          <div className={`badge ${estadoJira.conectado ? 'badge-exito' : 'badge-proceso'}`} style={{ padding: '0.45rem 0.85rem' }}>
            {estadoJira.conectado
              ? `🔗 Jira Conectado (${estadoJira.project_key})`
              : estadoJira.configurado
              ? '⚠️ Jira con error de conexión'
              : '🔌 Jira en espera de credenciales (.env)'}
          </div>
        </div>
      </div>

      {notificacion.mensaje && (
        <div className={`mensaje-alerta ${notificacion.tipo}`}>
          {notificacion.mensaje}
        </div>
      )}

      {/* 4 KPIs del Area de TI */}
      <div className="grilla-kpis">
        <div className="kpi-tarjeta proceso">
          <div className="kpi-titulo">Tickets Activos</div>
          <div className="kpi-valor">{metricas.ticketsAbiertos}</div>
          <div className="kpi-subtexto">Pendientes de atención o cierre</div>
        </div>
        <div className="kpi-tarjeta alerta">
          <div className="kpi-titulo">Alta Prioridad / SLA Vencido</div>
          <div className="kpi-valor">{metricas.ticketsCriticos}</div>
          <div className="kpi-subtexto">Requieren atención prioritaria</div>
        </div>
        <div className="kpi-tarjeta exito">
          <div className="kpi-titulo">Tickets Cerrados</div>
          <div className="kpi-valor">{metricas.ticketsCerrados}</div>
          <div className="kpi-subtexto">Resueltos con evidencia documentada</div>
        </div>
        <div className="kpi-tarjeta">
          <div className="kpi-titulo">Sincronizados en Jira</div>
          <div className="kpi-valor">{metricas.sincronizadosJira}</div>
          <div className="kpi-subtexto">Vinculados a Jira Cloud REST API</div>
        </div>
      </div>

      {/* Bandeja principal de tickets */}
      <div className="tarjeta">
        <div className="tarjeta-encabezado" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
          <h3>Bandeja Global de Tickets ({ticketsFiltrados.length})</h3>
          <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
            <input
              type="text"
              placeholder="🔍 Código, título, solicitante o Jira..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              style={{ padding: '0.45rem 0.75rem', border: '1px solid var(--color-borde)', borderRadius: '4px', fontSize: '0.85rem' }}
            />
            <select
              value={filtroTipo}
              onChange={(e) => setFiltroTipo(e.target.value)}
              style={{ padding: '0.45rem 0.75rem', border: '1px solid var(--color-borde)', borderRadius: '4px', fontSize: '0.85rem' }}
            >
              <option value="TODOS">Todos los Tipos</option>
              <option value="Incidente">Incidente</option>
              <option value="Servicio">Solicitud Servicio</option>
              <option value="Informacion">Solicitud Información</option>
              <option value="Acceso">Solicitud Acceso</option>
              <option value="Cambio">Control de Cambio</option>
            </select>
            <select
              value={filtroEstado}
              onChange={(e) => setFiltroEstado(e.target.value)}
              style={{ padding: '0.45rem 0.75rem', border: '1px solid var(--color-borde)', borderRadius: '4px', fontSize: '0.85rem' }}
            >
              <option value="TODOS">Todos los Estados</option>
              <option value="Solicitado">Solicitado</option>
              <option value="En evaluacion">En evaluación</option>
              <option value="Aprobado">Aprobado</option>
              <option value="En atencion">En atención</option>
              <option value="Cerrado">Cerrado</option>
              <option value="Rechazado">Rechazado</option>
            </select>
          </div>
        </div>

        <div className="tabla-contenedor">
          <table>
            <thead>
              <tr>
                <th>Código</th>
                <th>Tipo</th>
                <th>Asunto</th>
                <th>Solicitante / Área</th>
                <th>Prioridad</th>
                <th>SLA</th>
                <th>Estado</th>
                <th>Jira</th>
                <th className="no-imprimir">Gestionar</th>
              </tr>
            </thead>
            <tbody>
              {ticketsFiltrados.map((t) => (
                <tr key={t.id_ticket} className={t.sla_estado === 'Vencido' ? 'fila-alerta' : ''}>
                  <td><code>{t.codigo_ticket}</code></td>
                  <td>
                    <span className="badge badge-neutro">
                      {t.tipo_solicitud}{t.tipo_solicitud === 'Cambio' ? ` (${t.tipo_cambio})` : ''}
                    </span>
                  </td>
                  <td><strong>{t.titulo}</strong></td>
                  <td>
                    <div>{t.solicitante_nombre}</div>
                    <small style={{ color: 'var(--color-texto-muted)' }}>{t.area_origen}</small>
                  </td>
                  <td>
                    <span className={`badge ${t.prioridad === 'Critica' || t.prioridad === 'Alta' ? 'badge-alerta' : t.prioridad === 'Media' ? 'badge-proceso' : 'badge-neutro'}`}>
                      {t.prioridad}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${t.sla_estado === 'Vencido' ? 'badge-alerta' : t.sla_estado === 'Cumplido' ? 'badge-exito' : 'badge-proceso'}`}>
                      {t.sla_horas}h • {t.sla_estado}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${t.estado === 'Cerrado' ? 'badge-exito' : t.estado === 'Rechazado' ? 'badge-alerta' : 'badge-proceso'}`}>
                      {t.estado}
                    </span>
                  </td>
                  <td>
                    {t.jira_issue_key ? (
                      <a href={t.jira_url || '#'} target="_blank" rel="noreferrer" className="badge badge-exito" style={{ textDecoration: 'none' }}>
                        {t.jira_issue_key}
                      </a>
                    ) : (
                      <span className="badge badge-neutro">Pendiente</span>
                    )}
                  </td>
                  <td className="no-imprimir">
                    <button
                      type="button"
                      className="btn btn-secundario btn-sm"
                      onClick={() => abrirDetalle(t.id_ticket)}
                    >
                      Ver / Atender
                    </button>
                  </td>
                </tr>
              ))}
              {ticketsFiltrados.length === 0 && (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', padding: '1.5rem' }}>
                    No se encontraron tickets con los filtros aplicados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Panel de detalle completo y flujo ITIL cuando se selecciona un ticket */}
      {seleccionado && (
        <div className="tarjeta" style={{ borderLeft: '5px solid var(--color-toyota-rojo)' }}>
          <div className="tarjeta-encabezado">
            <div>
              <h3>{seleccionado.codigo_ticket} — {seleccionado.titulo}</h3>
              <small style={{ color: 'var(--color-texto-muted)' }}>
                Registrado: {seleccionado.fecha_creacion} | Límite SLA: {seleccionado.fecha_limite_sla} ({seleccionado.sla_estado})
              </small>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                type="button"
                className="btn btn-secundario btn-sm"
                onClick={() => sincronizarConJira(seleccionado.id_ticket)}
              >
                🔄 {seleccionado.jira_issue_key ? `Sync Jira (${seleccionado.jira_issue_key})` : 'Enviar a Jira'}
              </button>
              <button
                type="button"
                className="btn btn-secundario btn-sm"
                onClick={() => setSeleccionado(null)}
              >
                Cerrar Detalle
              </button>
            </div>
          </div>

          {/* Stepper visual de etapas del procedimiento (PDF Semana 10/11) */}
          <div className="sd-stepper">
            {ETAPAS_FLUJO.map((etapa) => {
              const indiceActual = ETAPAS_FLUJO.indexOf(seleccionado.estado);
              const indiceEtapa = ETAPAS_FLUJO.indexOf(etapa);
              const completado = indiceEtapa <= indiceActual && seleccionado.estado !== 'Rechazado';
              return (
                <div key={etapa} className={`sd-step ${completado ? 'activo' : ''}`}>
                  <span>{etapa}</span>
                </div>
              );
            })}
          </div>

          <div className="sd-detalle-grid">
            <div>
              <p><strong>Solicitante:</strong> {seleccionado.solicitante_nombre} ({seleccionado.area_origen})</p>
              <p><strong>Tipo:</strong> {seleccionado.tipo_solicitud} {seleccionado.tipo_solicitud === 'Cambio' ? `— ${seleccionado.tipo_cambio}` : ''}</p>
              <p><strong>Descripción:</strong> {seleccionado.descripcion}</p>
              {seleccionado.impacto_riesgo && <p><strong>Impacto / Riesgo:</strong> {seleccionado.impacto_riesgo}</p>}
              {seleccionado.plan_pruebas && <p><strong>Plan de Pruebas:</strong> {seleccionado.plan_pruebas}</p>}
              {seleccionado.plan_rollback && <p><strong>Plan de Rollback:</strong> {seleccionado.plan_rollback}</p>}
              {seleccionado.aprobador_nombre && <p><strong>Aprobado por:</strong> {seleccionado.aprobador_nombre}</p>}
              {seleccionado.resolucion_evidencia && <p><strong>Resolución / Evidencia:</strong> {seleccionado.resolucion_evidencia}</p>}
              {seleccionado.jira_ultimo_error && !seleccionado.jira_sincronizado && (
                <p style={{ color: 'var(--color-proceso)', fontSize: '0.85rem' }}>
                  <strong>Nota Jira:</strong> {seleccionado.jira_ultimo_error}
                </p>
              )}
            </div>

            {seleccionado.estado !== 'Cerrado' && seleccionado.estado !== 'Rechazado' && (
              <div className="sd-acciones-box">
                <div className="campo-grupo">
                  <label htmlFor="ti-tecnico">Especialista TI Asignado</label>
                  <select
                    id="ti-tecnico"
                    value={tecnicoAsignado}
                    onChange={(e) => setTecnicoAsignado(e.target.value)}
                  >
                    {TECNICOS_TI.map((tec) => (
                      <option key={tec} value={tec}>{tec}</option>
                    ))}
                  </select>
                </div>

                <div className="campo-grupo">
                  <label htmlFor="ti-comentario">Comentario técnico / Evidencia de cierre</label>
                  <textarea
                    id="ti-comentario"
                    rows="3"
                    placeholder="Detalle de evaluación, aprobación o solución aplicada..."
                    value={comentarioAccion}
                    onChange={(e) => setComentarioAccion(e.target.value)}
                  />
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {seleccionado.estado === 'Solicitado' && (
                    <button type="button" className="btn btn-secundario btn-sm" onClick={() => cambiarEtapa('En evaluacion')}>
                      🔍 Evaluar
                    </button>
                  )}
                  {esAprobador && ['Solicitado', 'En evaluacion'].includes(seleccionado.estado) && (
                    <button type="button" className="btn btn-secundario btn-sm" onClick={() => cambiarEtapa('Aprobado')}>
                      👍 Aprobar
                    </button>
                  )}
                  {['Solicitado', 'En evaluacion', 'Aprobado'].includes(seleccionado.estado) && (
                    <button type="button" className="btn btn-primario btn-sm" onClick={() => cambiarEtapa('En atencion')}>
                      🛠️ Atender
                    </button>
                  )}
                  <button type="button" className="btn btn-exito btn-sm" onClick={() => cambiarEtapa('Cerrado')}>
                    ✓ Cerrar con Evidencia
                  </button>
                  <button type="button" className="btn btn-secundario btn-sm" onClick={() => cambiarEtapa('Rechazado')}>
                    ✕ Rechazar
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Trazabilidad historica del ticket */}
          <h4 style={{ marginTop: '1.25rem', marginBottom: '0.5rem', color: 'var(--color-secundario)' }}>
            Historial de Trazabilidad del Ticket
          </h4>
          <div className="sd-timeline">
            {historial.map((h) => (
              <div key={h.id_evento} className="sd-timeline-item">
                <div className="sd-timeline-meta">
                  <strong>{h.estado_nuevo}</strong> — {h.usuario_nombre} <span>({h.fecha_hora})</span>
                </div>
                <div>{h.comentario}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
