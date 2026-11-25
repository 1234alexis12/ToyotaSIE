import React, { useState, useEffect, useCallback } from 'react';
import { apiCrearTicket, apiObtenerTickets } from './servicios/api';

const SLA_TEXTO = {
  Critica: 'SLA: 2 horas (Atención inmediata)',
  Alta: 'SLA: 4 horas',
  Media: 'SLA: 24 horas',
  Baja: 'SLA: 48 horas',
};

/* Boton flotante y modal de Service Desk disponible para reportar incidentes, solicitudes y cambios */
export default function ServiceDeskFlotante({ usuario, onTicketCreado }) {
  const [abierto, setAbierto] = useState(false);
  const [pestana, setPestana] = useState('nuevo');
  const [misTickets, setMisTickets] = useState([]);

  const [tipoSolicitud, setTipoSolicitud] = useState('Incidente');
  const [tipoCambio, setTipoCambio] = useState('Normal');
  const [prioridad, setPrioridad] = useState('Media');
  const [areaOrigen, setAreaOrigen] = useState(usuario?.rol === 'Gerente' ? 'Gerencia' : 'Taller');
  const [titulo, setTitulo] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [impactoRiesgo, setImpactoRiesgo] = useState('');
  const [planPruebas, setPlanPruebas] = useState('');
  const [planRollback, setPlanRollback] = useState('');

  const [enviando, setEnviando] = useState(false);
  const [notificacion, setNotificacion] = useState({ tipo: '', mensaje: '' });

  const cargarMisTickets = useCallback(async () => {
    if (!usuario) return;
    try {
      const lista = await apiObtenerTickets(usuario.id_usuario, 'Operador');
      setMisTickets(lista);
    } catch {
      setMisTickets([]);
    }
  }, [usuario]);

  useEffect(() => {
    if (abierto) {
      cargarMisTickets();
    }
  }, [abierto, cargarMisTickets]);

  const manejarEnvio = async (e) => {
    e.preventDefault();
    if (!titulo.trim() || !descripcion.trim()) {
      setNotificacion({ tipo: 'error', mensaje: 'Complete el título y la descripción del ticket.' });
      return;
    }

    setEnviando(true);
    setNotificacion({ tipo: '', mensaje: '' });
    try {
      const creado = await apiCrearTicket({
        id_usuario_solicitante: usuario.id_usuario,
        solicitante_username: usuario.username,
        solicitante_nombre: usuario.nombre_completo,
        tipo_solicitud: tipoSolicitud,
        tipo_cambio: tipoSolicitud === 'Cambio' ? tipoCambio : 'N/A',
        prioridad,
        area_origen: areaOrigen,
        titulo: titulo.trim(),
        descripcion: descripcion.trim(),
        impacto_riesgo: impactoRiesgo.trim(),
        plan_pruebas: planPruebas.trim(),
        plan_rollback: planRollback.trim(),
      });

      const msgJira = creado.jira_issue_key
        ? ` y sincronizado con Jira (${creado.jira_issue_key}).`
        : ' en el Área de TI (Jira pendiente de credenciales .env).';

      setNotificacion({
        tipo: 'exito',
        mensaje: `Ticket ${creado.codigo_ticket} registrado${msgJira}`,
      });

      setTitulo('');
      setDescripcion('');
      setImpactoRiesgo('');
      setPlanPruebas('');
      setPlanRollback('');
      await cargarMisTickets();
      if (onTicketCreado) {
        onTicketCreado(creado);
      }
    } catch (err) {
      setNotificacion({ tipo: 'error', mensaje: err.message || 'No se pudo enviar el ticket.' });
    } finally {
      setEnviando(false);
    }
  };

  const activos = misTickets.filter((t) => t.estado !== 'Cerrado' && t.estado !== 'Rechazado').length;

  return (
    <>
      {/* Boton flotante inferior derecho visible en la interfaz */}
      <button
        type="button"
        className="btn-flotante-sd no-imprimir"
        onClick={() => setAbierto(true)}
        title="Abrir Service Desk TI (Reportar incidente o solicitud)"
      >
        <span>🎫 Service Desk TI</span>
        {activos > 0 && <span className="sd-flotante-badge">{activos}</span>}
      </button>

      {abierto && (
        <div className="sd-modal-overlay no-imprimir" onClick={() => setAbierto(false)}>
          <div className="sd-modal" onClick={(e) => e.stopPropagation()}>
            <div className="sd-modal-header">
              <div>
                <h3>🎫 Mesa de Ayuda TI — Service Desk</h3>
                <p>Gestión de Incidentes, Solicitudes de Servicio, Accesos y Control de Cambios</p>
              </div>
              <button type="button" className="sd-modal-cerrar" onClick={() => setAbierto(false)}>
                ✕
              </button>
            </div>

            <div className="sd-tabs">
              <button
                type="button"
                className={`sd-tab-btn ${pestana === 'nuevo' ? 'activo' : ''}`}
                onClick={() => setPestana('nuevo')}
              >
                + Nueva Solicitud / Incidente
              </button>
              <button
                type="button"
                className={`sd-tab-btn ${pestana === 'mis' ? 'activo' : ''}`}
                onClick={() => setPestana('mis')}
              >
                📋 Mis Tickets ({misTickets.length})
              </button>
            </div>

            <div className="sd-modal-body">
              {notificacion.mensaje && (
                <div className={`mensaje-alerta ${notificacion.tipo}`}>
                  {notificacion.mensaje}
                </div>
              )}

              {pestana === 'nuevo' ? (
                <form onSubmit={manejarEnvio} className="sd-form">
                  <div className="formulario-grid">
                    <div className="campo-grupo">
                      <label htmlFor="sd-tipo">Tipo de Ticket</label>
                      <select
                        id="sd-tipo"
                        value={tipoSolicitud}
                        onChange={(e) => setTipoSolicitud(e.target.value)}
                      >
                        <option value="Incidente">Incidente / Falla Técnica</option>
                        <option value="Servicio">Solicitud de Servicio</option>
                        <option value="Informacion">Solicitud de Información</option>
                        <option value="Acceso">Solicitud de Acceso (Mínimo Privilegio)</option>
                        <option value="Cambio">Control de Cambio (ITIL)</option>
                      </select>
                    </div>

                    <div className="campo-grupo">
                      <label htmlFor="sd-prioridad">Prioridad</label>
                      <select
                        id="sd-prioridad"
                        value={prioridad}
                        onChange={(e) => setPrioridad(e.target.value)}
                      >
                        <option value="Baja">Baja (48h)</option>
                        <option value="Media">Media (24h)</option>
                        <option value="Alta">Alta (4h)</option>
                        <option value="Critica">Crítica (2h)</option>
                      </select>
                    </div>

                    <div className="campo-grupo">
                      <label htmlFor="sd-area">Área Solicitante</label>
                      <select
                        id="sd-area"
                        value={areaOrigen}
                        onChange={(e) => setAreaOrigen(e.target.value)}
                      >
                        <option value="Ventas">Marketing y Ventas</option>
                        <option value="Almacen">Logística y Almacén</option>
                        <option value="Taller">Operaciones y Taller</option>
                        <option value="Gerencia">Dirección General</option>
                        <option value="TI">Área de TI</option>
                      </select>
                    </div>
                  </div>

                  <div className="sd-sla-hint">
                    <span>⏱️ {SLA_TEXTO[prioridad]}</span>
                    {tipoSolicitud === 'Acceso' && (
                      <span className="badge badge-proceso">Requiere aprobación formal previa</span>
                    )}
                    {tipoSolicitud === 'Cambio' && (
                      <span className="badge badge-alerta">Requiere plan de pruebas y rollback</span>
                    )}
                  </div>

                  <div className="campo-grupo">
                    <label htmlFor="sd-titulo">Título / Asunto</label>
                    <input
                      id="sd-titulo"
                      type="text"
                      placeholder="Ej. Error al imprimir reporte o Solicitud de acceso a Ventas"
                      value={titulo}
                      onChange={(e) => setTitulo(e.target.value)}
                      required
                    />
                  </div>

                  <div className="campo-grupo">
                    <label htmlFor="sd-desc">Descripción Detallada</label>
                    <textarea
                      id="sd-desc"
                      rows="3"
                      placeholder="Describe qué ocurrió, pasos para reproducirlo o detalle de tu solicitud..."
                      value={descripcion}
                      onChange={(e) => setDescripcion(e.target.value)}
                      required
                    />
                  </div>

                  {tipoSolicitud === 'Cambio' && (
                    <div className="sd-cambio-box">
                      <h4>Detalles de Control de Cambios</h4>
                      <div className="formulario-grid">
                        <div className="campo-grupo">
                          <label htmlFor="sd-tipo-cambio">Clasificación del Cambio</label>
                          <select
                            id="sd-tipo-cambio"
                            value={tipoCambio}
                            onChange={(e) => setTipoCambio(e.target.value)}
                          >
                            <option value="Normal">Normal (Nueva funcionalidad)</option>
                            <option value="Estandar">Estándar (Repetitivo)</option>
                            <option value="Emergencia">Emergencia (Corrección crítica)</option>
                          </select>
                        </div>
                        <div className="campo-grupo">
                          <label htmlFor="sd-impacto">Evaluación de Impacto / Riesgo</label>
                          <input
                            id="sd-impacto"
                            type="text"
                            placeholder="Ej. Afecta módulo de facturación en horario nocturno"
                            value={impactoRiesgo}
                            onChange={(e) => setImpactoRiesgo(e.target.value)}
                          />
                        </div>
                        <div className="campo-grupo">
                          <label htmlFor="sd-pruebas">Plan de Pruebas</label>
                          <input
                            id="sd-pruebas"
                            type="text"
                            placeholder="Ej. Ejecutar pytest y prueba en QA"
                            value={planPruebas}
                            onChange={(e) => setPlanPruebas(e.target.value)}
                          />
                        </div>
                        <div className="campo-grupo">
                          <label htmlFor="sd-rollback">Plan de Rollback</label>
                          <input
                            id="sd-rollback"
                            type="text"
                            placeholder="Ej. Restaurar tag previo en Docker y backup MySQL"
                            value={planRollback}
                            onChange={(e) => setPlanRollback(e.target.value)}
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
                    <button type="button" className="btn btn-secundario" onClick={() => setAbierto(false)}>
                      Cancelar
                    </button>
                    <button type="submit" className="btn btn-primario" disabled={enviando}>
                      {enviando ? 'Enviando a TI y Jira...' : 'Enviar Ticket al Área de TI'}
                    </button>
                  </div>
                </form>
              ) : (
                <div className="tabla-contenedor">
                  <table>
                    <thead>
                      <tr>
                        <th>Código</th>
                        <th>Tipo</th>
                        <th>Título</th>
                        <th>Prioridad</th>
                        <th>Estado</th>
                        <th>Jira</th>
                      </tr>
                    </thead>
                    <tbody>
                      {misTickets.map((t) => (
                        <tr key={t.id_ticket}>
                          <td><code>{t.codigo_ticket}</code></td>
                          <td>{t.tipo_solicitud}</td>
                          <td><strong>{t.titulo}</strong></td>
                          <td>
                            <span className={`badge ${t.prioridad === 'Critica' || t.prioridad === 'Alta' ? 'badge-alerta' : 'badge-proceso'}`}>
                              {t.prioridad}
                            </span>
                          </td>
                          <td>
                            <span className={`badge ${t.estado === 'Cerrado' ? 'badge-exito' : t.estado === 'Rechazado' ? 'badge-alerta' : 'badge-neutro'}`}>
                              {t.estado}
                            </span>
                          </td>
                          <td>
                            {t.jira_issue_key ? (
                              t.jira_url ? (
                                <a href={t.jira_url} target="_blank" rel="noreferrer" className="badge badge-exito" style={{ textDecoration: 'none' }}>
                                  {t.jira_issue_key} ↗
                                </a>
                              ) : (
                                <span className="badge badge-exito">{t.jira_issue_key}</span>
                              )
                            ) : (
                              <span className="badge badge-neutro">Local</span>
                            )}
                          </td>
                        </tr>
                      ))}
                      {misTickets.length === 0 && (
                        <tr>
                          <td colSpan="6" style={{ textAlign: 'center', padding: '1.25rem' }}>
                            Aún no has enviado tickets al Área de TI.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
