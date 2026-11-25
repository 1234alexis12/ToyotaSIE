/* URL base para consumir los endpoints del backend en Flask */
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

/* Datos semilla iniciales para pruebas en caso de que el backend este temporalmente inactivo */
const DATOS_SEMILLA = {
  usuarios: [
    { id_usuario: 1, username: 'admin_gerente', rol: 'Gerente', nombre_completo: 'Ing. Carlos Mendoza (Gerente)' },
    { id_usuario: 2, username: 'operador_taller', rol: 'Operador', nombre_completo: 'Marcos Quispe (Asesor de Servicio)' },
    { id_usuario: 3, username: 'soporte_ti', rol: 'TI', nombre_completo: 'Ing. Luis Mamani (Soporte TI)' }
  ],
  tickets_ti: [
    {
      id_ticket: 1,
      codigo_ticket: 'TKT-2026-0001',
      id_usuario_solicitante: 2,
      solicitante_username: 'operador_taller',
      solicitante_nombre: 'Marcos Quispe (Asesor de Servicio)',
      tipo_solicitud: 'Incidente',
      tipo_cambio: 'N/A',
      prioridad: 'Alta',
      area_origen: 'Taller',
      titulo: 'Error al imprimir orden de taller en impresora de bahia 2',
      descripcion: 'La impresora termica de red en bahia 2 muestra cola atascada al generar OT.',
      estado: 'En atencion',
      tecnico_ti_asignado: 'Ing. Luis Mamani (Soporte TI)',
      sla_horas: 4,
      fecha_creacion: '2026-11-25 08:15:00',
      fecha_limite_sla: '2026-11-25 12:15:00',
      sla_estado: 'A tiempo',
      jira_issue_key: null,
      jira_url: null,
      jira_sincronizado: false
    },
    {
      id_ticket: 2,
      codigo_ticket: 'TKT-2026-0002',
      id_usuario_solicitante: 2,
      solicitante_username: 'operador_taller',
      solicitante_nombre: 'Marcos Quispe (Asesor de Servicio)',
      tipo_solicitud: 'Acceso',
      tipo_cambio: 'N/A',
      prioridad: 'Media',
      area_origen: 'Ventas',
      titulo: 'Solicitud de acceso temporal a reportes ejecutivos de ventas',
      descripcion: 'Requiero permiso de lectura para cierre comercial mensual.',
      impacto_riesgo: 'Acceso de solo lectura sujeto a minimo privilegio.',
      estado: 'Solicitado',
      sla_horas: 24,
      fecha_creacion: '2026-11-25 09:30:00',
      fecha_limite_sla: '2026-11-26 09:30:00',
      sla_estado: 'A tiempo',
      jira_issue_key: null,
      jira_url: null,
      jira_sincronizado: false
    },
    {
      id_ticket: 3,
      codigo_ticket: 'TKT-2026-0003',
      id_usuario_solicitante: 1,
      solicitante_username: 'admin_gerente',
      solicitante_nombre: 'Ing. Carlos Mendoza (Gerente)',
      tipo_solicitud: 'Cambio',
      tipo_cambio: 'Normal',
      prioridad: 'Alta',
      area_origen: 'Infraestructura TI',
      titulo: 'Despliegue de replicacion Master-Slave MySQL 8.0 en Docker',
      descripcion: 'Separar escrituras en Master (3310) y lecturas en Slave (3311).',
      impacto_riesgo: 'Latencia minima durante arranque inicial.',
      plan_pruebas: 'Validar /api/health y bloqueo super_read_only en Slave.',
      plan_rollback: 'Revertir docker-compose.yml manteniendo volumen toyota_master_data.',
      estado: 'Aprobado',
      aprobado_por: 1,
      aprobador_nombre: 'Ing. Carlos Mendoza (Gerente)',
      tecnico_ti_asignado: 'Ing. Luis Mamani (Soporte TI)',
      sla_horas: 4,
      fecha_creacion: '2026-11-25 10:00:00',
      fecha_limite_sla: '2026-11-25 14:00:00',
      sla_estado: 'A tiempo',
      jira_issue_key: null,
      jira_url: null,
      jira_sincronizado: false
    }
  ],
  ticket_historial: [
    { id_evento: 1, id_ticket: 1, usuario_nombre: 'Marcos Quispe (Asesor de Servicio)', estado_anterior: null, estado_nuevo: 'Solicitado', comentario: 'Ticket registrado desde Service Desk.', fecha_hora: '2026-11-25 08:15:00' },
    { id_evento: 2, id_ticket: 2, usuario_nombre: 'Marcos Quispe (Asesor de Servicio)', estado_anterior: null, estado_nuevo: 'Solicitado', comentario: 'Solicitud pendiente de aprobacion gerencial.', fecha_hora: '2026-11-25 09:30:00' },
    { id_evento: 3, id_ticket: 3, usuario_nombre: 'Ing. Carlos Mendoza (Gerente)', estado_anterior: 'Solicitado', estado_nuevo: 'Aprobado', comentario: 'Cambio aprobado con plan de pruebas y rollback.', fecha_hora: '2026-11-25 10:10:00' }
  ],
  clientes: [
    { id_cliente: 1, dni_ruc: '20601234567', nombre_razon: 'Minera Cerro Verde S.A.A.', telefono: '958123456', email: 'logistica@cerroverde.pe', tipo_cliente: 'Corporativo' },
    { id_cliente: 2, dni_ruc: '45678912', nombre_razon: 'Juan Perez Delgado', telefono: '959987654', email: 'jperez@gmail.com', tipo_cliente: 'Particular' },
    { id_cliente: 3, dni_ruc: '20456789012', nombre_razon: 'Transportes Arequipa Express S.A.C.', telefono: '954332211', email: 'flota@arequipaexpress.pe', tipo_cliente: 'Corporativo' }
  ],
  inventario: [
    { id_item: 1, codigo_vin_sku: '8AJBA3CD4P123456', tipo: 'Vehiculo', nombre_modelo: 'Toyota Hilux 4x4 Doble Cabina SRX', stock_actual: 4, stock_minimo: 2, precio_usd: 48500.00 },
    { id_item: 2, codigo_vin_sku: '93XBA3CD4P789012', tipo: 'Vehiculo', nombre_modelo: 'Toyota Corolla Sedan 1.8 XEI', stock_actual: 2, stock_minimo: 2, precio_usd: 24200.00 },
    { id_item: 3, codigo_vin_sku: '8AJBA3CD4P345678', tipo: 'Vehiculo', nombre_modelo: 'Toyota RAV4 Hibrida 2.5 AWD', stock_actual: 3, stock_minimo: 1, precio_usd: 39900.00 },
    { id_item: 4, codigo_vin_sku: '93XBA3CD4P901234', tipo: 'Vehiculo', nombre_modelo: 'Toyota Yaris Sedan 1.5 GLI', stock_actual: 1, stock_minimo: 2, precio_usd: 18900.00 },
    { id_item: 5, codigo_vin_sku: 'SKU-04152-YZZA6', tipo: 'Repuesto', nombre_modelo: 'Filtro de Aceite Original Toyota (Hilux/Fortuner)', stock_actual: 18, stock_minimo: 10, precio_usd: 22.50 },
    { id_item: 6, codigo_vin_sku: 'SKU-04465-0K340', tipo: 'Repuesto', nombre_modelo: 'Pastillas de Freno Delanteras OEM Toyota Hilux', stock_actual: 3, stock_minimo: 5, precio_usd: 95.00 },
    { id_item: 7, codigo_vin_sku: 'SKU-08880-80845', tipo: 'Repuesto', nombre_modelo: 'Aceite Motor Sintetico Toyota 5W-30 (Galon)', stock_actual: 2, stock_minimo: 6, precio_usd: 45.00 },
    { id_item: 8, codigo_vin_sku: 'SKU-17801-0L040', tipo: 'Repuesto', nombre_modelo: 'Filtro de Aire Original Hilux/Prado', stock_actual: 12, stock_minimo: 5, precio_usd: 38.00 }
  ],
  ventas: [
    { id_venta: 1, id_cliente: 1, cliente_nombre: 'Minera Cerro Verde S.A.A.', id_item: 1, vehiculo_nombre: 'Toyota Hilux 4x4 Doble Cabina SRX', precio_total: 48500.00, estado: 'Vendido', fecha: '2026-11-18' },
    { id_venta: 2, id_cliente: 2, cliente_nombre: 'Juan Perez Delgado', id_item: 2, vehiculo_nombre: 'Toyota Corolla Sedan 1.8 XEI', precio_total: 24200.00, estado: 'Cotizado', fecha: '2026-11-20' },
    { id_venta: 3, id_cliente: 3, cliente_nombre: 'Transportes Arequipa Express S.A.C.', id_item: 4, vehiculo_nombre: 'Toyota Yaris Sedan 1.5 GLI', precio_total: 18900.00, estado: 'Prospecto', fecha: '2026-11-21' }
  ],
  taller: [
    { id_orden: 1, id_cliente: 1, cliente_nombre: 'Minera Cerro Verde S.A.A.', placa_vin: 'V9A-782', tipo_servicio: 'Mantenimiento Preventivo (10,000 km)', tecnico: 'Tec. Manuel Salinas', id_item_repuesto: 5, repuesto_nombre: 'Filtro de Aceite Original Toyota', costo_usd: 120.00, estado: 'Entregado', fecha_ingreso: '2026-11-19' },
    { id_orden: 2, id_cliente: 2, cliente_nombre: 'Juan Perez Delgado', placa_vin: 'V4B-119', tipo_servicio: 'PDI (Inspeccion Pre-Entrega)', tecnico: 'Tec. David Paredes', id_item_repuesto: null, repuesto_nombre: 'Ninguno', costo_usd: 80.00, estado: 'En proceso', fecha_ingreso: '2026-11-21' },
    { id_orden: 3, id_cliente: 3, cliente_nombre: 'Transportes Arequipa Express S.A.C.', placa_vin: 'V7C-554', tipo_servicio: 'Reparacion Sistema de Frenos', tecnico: 'Tec. Manuel Salinas', id_item_repuesto: 6, repuesto_nombre: 'Pastillas de Freno Delanteras OEM', costo_usd: 210.00, estado: 'Pendiente', fecha_ingreso: '2026-11-21' }
  ],
  auditoria: [
    { id_log: 1, fecha_hora: '2026-11-21 08:30:15', username: 'admin_gerente', modulo: 'SEGURIDAD', accion: 'LOGIN', detalle: 'Inicio de sesion exitoso de Gerente General' },
    { id_log: 2, fecha_hora: '2026-11-21 09:15:22', username: 'operador_taller', modulo: 'VENTAS', accion: 'INSERT', detalle: 'Registro de cotizacion #3 para cliente Transportes Arequipa' },
    { id_log: 3, fecha_hora: '2026-11-21 10:45:04', username: 'admin_gerente', modulo: 'VENTAS', accion: 'UPDATE_ESTADO', detalle: 'Cierre de venta #1 y descuento automatico de stock de Toyota Hilux' },
    { id_log: 4, fecha_hora: '2026-11-21 11:20:10', username: 'operador_taller', modulo: 'TALLER', accion: 'INSERT_ORDEN', detalle: 'Apertura de orden de servicio #3 con cargo de pastillas de freno' }
  ]
};

/* Funcion de inicializacion de almacenamiento local para pruebas en frontend */
function obtenerAlmacenamiento(clave, porDefecto) {
  const guardado = localStorage.getItem('toyota_' + clave);
  if (!guardado) {
    localStorage.setItem('toyota_' + clave, JSON.stringify(porDefecto));
    return porDefecto;
  }
  return JSON.parse(guardado);
}

/* Guardar actualizacion en el almacenamiento local */
function guardarAlmacenamiento(clave, datos) {
  localStorage.setItem('toyota_' + clave, JSON.stringify(datos));
}

/* Registrar evento de auditoria tanto en local como por API */
export async function registrarEventoAuditoria(username, modulo, accion, detalle) {
  const nuevoLog = {
    id_log: Date.now(),
    fecha_hora: new Date().toISOString().replace('T', ' ').substring(0, 19),
    username,
    modulo,
    accion,
    detalle
  };
  try {
    /* Intento de envio al backend Flask */
    await fetch(`${API_URL}/auditoria`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(nuevoLog)
    });
  } catch (err) {
    /* Si el backend aun no esta corriendo, almacena en localStorage */
    const logs = obtenerAlmacenamiento('auditoria', DATOS_SEMILLA.auditoria);
    logs.unshift(nuevoLog);
    guardarAlmacenamiento('auditoria', logs);
  }
}

/* Servicio de autenticacion */
export async function apiLogin(username, password) {
  try {
    const respuesta = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (respuesta.ok) {
      return await respuesta.json();
    }
  } catch (error) {
    /* Fallback local para pruebas inmediatas en navegador */
  }

  /* Validacion local con usuarios semilla */
  const usuario = DATOS_SEMILLA.usuarios.find(u => u.username === username);
  if (usuario && (password === 'Toyota2026!' || password === '123456')) {
    registrarEventoAuditoria(usuario.username, 'SEGURIDAD', 'LOGIN', `Acceso exitoso al sistema como rol ${usuario.rol}`);
    return { exito: true, usuario };
  }
  throw new Error('Credenciales incorrectas. Verifique usuario y clave.');
}

/* Servicio para obtener los datos consolidados del Dashboard */
export async function apiObtenerDashboard() {
  try {
    const res = await fetch(`${API_URL}/dashboard`);
    if (res.ok) return await res.json();
  } catch (err) {
    /* Calculo dinamico local si el backend no responde */
  }

  const ventas = obtenerAlmacenamiento('ventas', DATOS_SEMILLA.ventas);
  const inventario = obtenerAlmacenamiento('inventario', DATOS_SEMILLA.inventario);
  const taller = obtenerAlmacenamiento('taller', DATOS_SEMILLA.taller);

  const totalVendido = ventas
    .filter(v => v.estado === 'Vendido')
    .reduce((acc, v) => acc + Number(v.precio_total), 0);

  const vehiculosDisponibles = inventario
    .filter(i => i.tipo === 'Vehiculo')
    .reduce((acc, i) => acc + Number(i.stock_actual), 0);

  const repuestosAlerta = inventario
    .filter(i => i.tipo === 'Repuesto' && Number(i.stock_actual) <= Number(i.stock_minimo))
    .length;

  const ordenesActivas = taller
    .filter(o => o.estado !== 'Entregado')
    .length;

  return {
    kpis: {
      totalVendido,
      vehiculosDisponibles,
      repuestosAlerta,
      ordenesActivas
    },
    ventasRecientes: ventas.slice(0, 5),
    ordenesRecientes: taller.slice(0, 5)
  };
}

/* Obtener listado de clientes */
export async function apiObtenerClientes() {
  try {
    const res = await fetch(`${API_URL}/clientes`);
    if (res.ok) return await res.json();
  } catch (e) {}
  return obtenerAlmacenamiento('clientes', DATOS_SEMILLA.clientes);
}

/* Registrar nuevo cliente */
export async function apiCrearCliente(cliente) {
  try {
    const res = await fetch(`${API_URL}/clientes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cliente)
    });
    if (res.ok) return await res.json();
  } catch (e) {}
  const lista = obtenerAlmacenamiento('clientes', DATOS_SEMILLA.clientes);
  const nuevo = { ...cliente, id_cliente: Date.now() };
  lista.unshift(nuevo);
  guardarAlmacenamiento('clientes', lista);
  return nuevo;
}

/* Obtener inventario de vehiculos y repuestos */
export async function apiObtenerInventario() {
  try {
    const res = await fetch(`${API_URL}/inventario`);
    if (res.ok) return await res.json();
  } catch (e) {}
  return obtenerAlmacenamiento('inventario', DATOS_SEMILLA.inventario);
}

/* Registrar o actualizar item en inventario */
export async function apiCrearItemInventario(item) {
  try {
    const res = await fetch(`${API_URL}/inventario`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item)
    });
    if (res.ok) return await res.json();
  } catch (e) {}
  const lista = obtenerAlmacenamiento('inventario', DATOS_SEMILLA.inventario);
  const nuevo = { ...item, id_item: Date.now() };
  lista.unshift(nuevo);
  guardarAlmacenamiento('inventario', lista);
  return nuevo;
}

/* Obtener lista de ventas */
export async function apiObtenerVentas() {
  try {
    const res = await fetch(`${API_URL}/ventas`);
    if (res.ok) return await res.json();
  } catch (e) {}
  return obtenerAlmacenamiento('ventas', DATOS_SEMILLA.ventas);
}

/* Crear cotizacion o venta */
export async function apiCrearVenta(venta, username) {
  try {
    const res = await fetch(`${API_URL}/ventas`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...venta, username })
    });
    if (res.ok) return await res.json();
  } catch (e) {}

  const ventas = obtenerAlmacenamiento('ventas', DATOS_SEMILLA.ventas);
  const nueva = {
    ...venta,
    id_venta: Date.now(),
    fecha: new Date().toISOString().substring(0, 10)
  };
  ventas.unshift(nueva);
  guardarAlmacenamiento('ventas', ventas);

  /* Si se crea directamente como Vendido, descontar stock */
  if (venta.estado === 'Vendido') {
    descontarStockLocal(venta.id_item, 1);
  }

  registrarEventoAuditoria(username, 'VENTAS', 'INSERT_VENTA', `Registro de operacion para item ID ${venta.id_item} por $${venta.precio_total}`);
  return nueva;
}

/* Cambiar estado de una cotizacion a Vendido con descuento de stock */
export async function apiActualizarEstadoVenta(idVenta, nuevoEstado, username) {
  try {
    const res = await fetch(`${API_URL}/ventas/${idVenta}/estado`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ estado: nuevoEstado, username })
    });
    if (res.ok) return await res.json();
  } catch (e) {}

  const ventas = obtenerAlmacenamiento('ventas', DATOS_SEMILLA.ventas);
  const venta = ventas.find(v => v.id_venta === idVenta);
  if (venta) {
    const estadoPrevio = venta.estado;
    venta.estado = nuevoEstado;
    guardarAlmacenamiento('ventas', ventas);

    /* Descontar 1 unidad del inventario al pasar a Vendido */
    if (nuevoEstado === 'Vendido' && estadoPrevio !== 'Vendido') {
      descontarStockLocal(venta.id_item, 1);
      registrarEventoAuditoria(username, 'VENTAS', 'UPDATE_VENTA', `Venta #${idVenta} confirmada como VENDIDO. Descuento automatico de 1 unidad.`);
    }
  }
  return venta;
}

/* Obtener ordenes de trabajo de taller */
export async function apiObtenerOrdenesTaller() {
  try {
    const res = await fetch(`${API_URL}/taller`);
    if (res.ok) return await res.json();
  } catch (e) {}
  return obtenerAlmacenamiento('taller', DATOS_SEMILLA.taller);
}

/* Registrar orden de servicio en taller con consumo de repuesto */
export async function apiCrearOrdenTaller(orden, username) {
  try {
    const res = await fetch(`${API_URL}/taller`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...orden, username })
    });
    if (res.ok) return await res.json();
  } catch (e) {}

  const lista = obtenerAlmacenamiento('taller', DATOS_SEMILLA.taller);
  const nueva = {
    ...orden,
    id_orden: Date.now(),
    fecha_ingreso: new Date().toISOString().substring(0, 10)
  };
  lista.unshift(nueva);
  guardarAlmacenamiento('taller', lista);

  /* Si se selecciono un repuesto, descontar 1 unidad en inventario */
  if (orden.id_item_repuesto) {
    descontarStockLocal(orden.id_item_repuesto, 1);
  }

  registrarEventoAuditoria(username, 'TALLER', 'INSERT_ORDEN', `Apertura de orden de servicio para placa/VIN ${orden.placa_vin}`);
  return nueva;
}

/* Actualizar estado de orden en taller */
export async function apiActualizarEstadoTaller(idOrden, nuevoEstado, username) {
  try {
    const res = await fetch(`${API_URL}/taller/${idOrden}/estado`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ estado: nuevoEstado, username })
    });
    if (res.ok) return await res.json();
  } catch (e) {}

  const lista = obtenerAlmacenamiento('taller', DATOS_SEMILLA.taller);
  const orden = lista.find(o => o.id_orden === idOrden);
  if (orden) {
    orden.estado = nuevoEstado;
    guardarAlmacenamiento('taller', lista);
    registrarEventoAuditoria(username, 'TALLER', 'UPDATE_ESTADO', `Orden #${idOrden} actualizada a estado ${nuevoEstado}`);
  }
  return orden;
}

/* Obtener bitacora de auditoria */
export async function apiObtenerAuditoria() {
  try {
    const res = await fetch(`${API_URL}/auditoria`);
    if (res.ok) return await res.json();
  } catch (e) {}
  return obtenerAlmacenamiento('auditoria', DATOS_SEMILLA.auditoria);
}

/* Funcion auxiliar para descontar existencias en el inventario local */
function descontarStockLocal(idItem, cantidad) {
  const inventario = obtenerAlmacenamiento('inventario', DATOS_SEMILLA.inventario);
  const item = inventario.find(i => Number(i.id_item) === Number(idItem));
  if (item && item.stock_actual >= cantidad) {
    item.stock_actual = Number(item.stock_actual) - cantidad;
    guardarAlmacenamiento('inventario', inventario);
  }
}


/* =========================================================================
   SERVICIOS DE AREA DE TI: SERVICE DESK, CONTROL DE CAMBIOS Y JIRA
   ========================================================================= */

const SLA_LOCAL = { Critica: 2, Alta: 4, Media: 24, Baja: 48 };

export async function apiObtenerEstadoJira() {
  try {
    const res = await fetch(`${API_URL}/tickets/jira-config`);
    if (res.ok) return await res.json();
  } catch {
    /* Fallback offline */
  }
  return { configurado: false, conectado: false, mensaje: 'Backend no disponible.' };
}

export async function apiObtenerMetricasTI() {
  try {
    const res = await fetch(`${API_URL}/tickets/metricas`);
    if (res.ok) return await res.json();
  } catch {
    /* Calculo local */
  }
  const lista = obtenerAlmacenamiento('tickets_ti', DATOS_SEMILLA.tickets_ti);
  return {
    ticketsAbiertos: lista.filter(t => t.estado !== 'Cerrado' && t.estado !== 'Rechazado').length,
    ticketsCriticos: lista.filter(t => t.estado !== 'Cerrado' && t.estado !== 'Rechazado' && (t.prioridad === 'Critica' || t.prioridad === 'Alta')).length,
    ticketsCerrados: lista.filter(t => t.estado === 'Cerrado').length,
    sincronizadosJira: lista.filter(t => t.jira_sincronizado).length,
    totalTickets: lista.length
  };
}

export async function apiObtenerTickets(idUsuario, rol) {
  try {
    const params = new URLSearchParams();
    if (idUsuario) params.set('id_usuario', String(idUsuario));
    if (rol) params.set('rol', rol);
    const res = await fetch(`${API_URL}/tickets?${params.toString()}`);
    if (res.ok) return await res.json();
  } catch {
    /* Fallback local */
  }
  const lista = obtenerAlmacenamiento('tickets_ti', DATOS_SEMILLA.tickets_ti);
  if (rol === 'Operador' && idUsuario) {
    return lista.filter(t => Number(t.id_usuario_solicitante) === Number(idUsuario));
  }
  return lista;
}

export async function apiCrearTicket(ticket) {
  let respuesta = null;
  try {
    respuesta = await fetch(`${API_URL}/tickets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ticket)
    });
  } catch {
    respuesta = null;
  }

  if (respuesta) {
    const body = await respuesta.json().catch(() => ({}));
    if (respuesta.ok) return body;
    throw new Error(body.error || 'No se pudo registrar el ticket.');
  }

  const lista = obtenerAlmacenamiento('tickets_ti', DATOS_SEMILLA.tickets_ti);
  const historial = obtenerAlmacenamiento('ticket_historial', DATOS_SEMILLA.ticket_historial);
  const idNuevo = Date.now();
  const ahora = new Date();
  const slaHoras = SLA_LOCAL[ticket.prioridad] || 24;
  const limite = new Date(ahora.getTime() + slaHoras * 3600000);
  const nuevo = {
    ...ticket,
    id_ticket: idNuevo,
    codigo_ticket: `TKT-LOC-${String(lista.length + 1).padStart(4, '0')}`,
    estado: 'Solicitado',
    sla_horas: slaHoras,
    sla_estado: 'A tiempo',
    fecha_creacion: ahora.toISOString().replace('T', ' ').substring(0, 19),
    fecha_limite_sla: limite.toISOString().replace('T', ' ').substring(0, 19),
    jira_issue_key: null,
    jira_sincronizado: false
  };
  lista.unshift(nuevo);
  historial.push({
    id_evento: Date.now() + 1,
    id_ticket: idNuevo,
    usuario_nombre: ticket.solicitante_nombre || 'Usuario',
    estado_anterior: null,
    estado_nuevo: 'Solicitado',
    comentario: `Ticket ${ticket.tipo_solicitud} registrado localmente.`,
    fecha_hora: nuevo.fecha_creacion
  });
  guardarAlmacenamiento('tickets_ti', lista);
  guardarAlmacenamiento('ticket_historial', historial);
  registrarEventoAuditoria(ticket.solicitante_username || 'sistema', 'TI_SERVICEDESK', 'INSERT_TICKET', `Ticket ${nuevo.codigo_ticket} creado`);
  return nuevo;
}

export async function apiObtenerDetalleTicket(idTicket) {
  try {
    const res = await fetch(`${API_URL}/tickets/${idTicket}`);
    if (res.ok) return await res.json();
  } catch {
    /* Fallback local */
  }
  const lista = obtenerAlmacenamiento('tickets_ti', DATOS_SEMILLA.tickets_ti);
  const historial = obtenerAlmacenamiento('ticket_historial', DATOS_SEMILLA.ticket_historial);
  const ticket = lista.find(t => Number(t.id_ticket) === Number(idTicket));
  if (!ticket) throw new Error('Ticket no encontrado.');
  return {
    ticket,
    historial: historial.filter(h => Number(h.id_ticket) === Number(idTicket))
  };
}

export async function apiActualizarEstadoTicket(idTicket, payload) {
  let respuesta = null;
  try {
    respuesta = await fetch(`${API_URL}/tickets/${idTicket}/estado`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  } catch {
    respuesta = null;
  }

  if (respuesta) {
    const body = await respuesta.json().catch(() => ({}));
    if (respuesta.ok) return body;
    throw new Error(body.error || 'No se pudo actualizar el estado del ticket.');
  }

  const lista = obtenerAlmacenamiento('tickets_ti', DATOS_SEMILLA.tickets_ti);
  const historial = obtenerAlmacenamiento('ticket_historial', DATOS_SEMILLA.ticket_historial);
  const ticket = lista.find(t => Number(t.id_ticket) === Number(idTicket));
  if (!ticket) throw new Error('Ticket no encontrado.');

  const estadoPrevio = ticket.estado;
  ticket.estado = payload.estado;
  if (payload.estado === 'Aprobado') {
    ticket.aprobado_por = payload.id_usuario;
    ticket.aprobador_nombre = payload.nombre_completo;
  }
  if (payload.tecnico_ti_asignado) ticket.tecnico_ti_asignado = payload.tecnico_ti_asignado;
  if (payload.resolucion_evidencia) ticket.resolucion_evidencia = payload.resolucion_evidencia;

  historial.push({
    id_evento: Date.now(),
    id_ticket: idTicket,
    usuario_nombre: payload.nombre_completo || 'Soporte TI',
    estado_anterior: estadoPrevio,
    estado_nuevo: payload.estado,
    comentario: payload.comentario || `Estado actualizado a ${payload.estado}`,
    fecha_hora: new Date().toISOString().replace('T', ' ').substring(0, 19)
  });

  guardarAlmacenamiento('tickets_ti', lista);
  guardarAlmacenamiento('ticket_historial', historial);
  return ticket;
}

export async function apiSincronizarTicketJira(idTicket) {
  const res = await fetch(`${API_URL}/tickets/${idTicket}/jira-sync`, { method: 'POST' });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(body.error || 'No se pudo sincronizar con Jira.');
  }
  return body;
}
