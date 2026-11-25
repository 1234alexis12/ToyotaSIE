import datetime
from config.MySQLConexion import ConexionBD
from models.entidades import TicketTIDTO, TicketHistorialDTO
from dao.SeguridadDAO import SeguridadDAO


SLA_HORAS_POR_PRIORIDAD = {
    'Critica': 2,
    'Alta': 4,
    'Media': 24,
    'Baja': 48,
}

TIPOS_SOLICITUD_VALIDOS = {'Incidente', 'Servicio', 'Informacion', 'Acceso', 'Cambio'}
TIPOS_CAMBIO_VALIDOS = {'N/A', 'Estandar', 'Normal', 'Emergencia'}
ESTADOS_VALIDOS = {'Solicitado', 'En evaluacion', 'Aprobado', 'En atencion', 'Cerrado', 'Rechazado'}

# Datos semilla en memoria si MySQL no esta disponible
_TICKETS_MEMORIA = [
    TicketTIDTO(
        1,
        'TKT-2026-0001',
        2,
        'operador_taller',
        'Marcos Quispe (Asesor de Servicio)',
        'Incidente',
        'N/A',
        'Alta',
        'Taller',
        'Error al imprimir orden de taller en impresora de bahia 2',
        'La impresora termica de red en bahia 2 muestra cola atascada al generar OT de mantenimiento.',
        None,
        None,
        None,
        'En atencion',
        None,
        None,
        'Ing. Luis Mamani (Soporte TI)',
        None,
        4,
        '2026-11-25 08:15:00',
        '2026-11-25 12:15:00',
        None,
        None,
        None,
        False,
        'Pendiente de configuracion de credenciales Jira en .env',
    ),
    TicketTIDTO(
        2,
        'TKT-2026-0002',
        2,
        'operador_taller',
        'Marcos Quispe (Asesor de Servicio)',
        'Acceso',
        'N/A',
        'Media',
        'Ventas',
        'Solicitud de acceso temporal a reportes ejecutivos de ventas',
        'Requiero permiso de lectura para emitir cierre comercial mensual por ausencia del supervisor.',
        'Acceso de solo lectura sujeto a principio de minimo privilegio.',
        None,
        None,
        'Solicitado',
        None,
        None,
        None,
        None,
        24,
        '2026-11-25 09:30:00',
        '2026-11-26 09:30:00',
        None,
        None,
        None,
        False,
        'Pendiente de configuracion de credenciales Jira en .env',
    ),
    TicketTIDTO(
        3,
        'TKT-2026-0003',
        1,
        'admin_gerente',
        'Ing. Carlos Mendoza (Gerente)',
        'Cambio',
        'Normal',
        'Alta',
        'Infraestructura TI',
        'Despliegue de replicacion Master-Slave MySQL 8.0 en Docker',
        'Separar transacciones de escritura en nodo Master (3310) y lecturas del Dashboard en Slave (3311).',
        'Posible latencia minima durante arranque inicial de contenedores.',
        'Validar healthcheck /api/health y bloqueo super_read_only en Slave.',
        'Revertir docker-compose.yml al servicio unico db manteniendo volumen toyota_master_data.',
        'Aprobado',
        1,
        'Ing. Carlos Mendoza (Gerente)',
        'Ing. Luis Mamani (Soporte TI)',
        None,
        4,
        '2026-11-25 10:00:00',
        '2026-11-25 14:00:00',
        None,
        None,
        None,
        False,
        'Pendiente de configuracion de credenciales Jira en .env',
    ),
]

_HISTORIAL_MEMORIA = [
    TicketHistorialDTO(1, 1, 'Marcos Quispe (Asesor de Servicio)', None, 'Solicitado', 'Ticket registrado desde Service Desk.', '2026-11-25 08:15:00'),
    TicketHistorialDTO(2, 1, 'Ing. Luis Mamani (Soporte TI)', 'Solicitado', 'En atencion', 'Revisando driver de impresion en red local.', '2026-11-25 08:30:00'),
    TicketHistorialDTO(3, 2, 'Marcos Quispe (Asesor de Servicio)', None, 'Solicitado', 'Solicitud de acceso pendiente de aprobacion gerencial.', '2026-11-25 09:30:00'),
    TicketHistorialDTO(4, 3, 'Ing. Carlos Mendoza (Gerente)', None, 'Solicitado', 'Control de cambio Normal registrado.', '2026-11-25 10:00:00'),
    TicketHistorialDTO(5, 3, 'Ing. Carlos Mendoza (Gerente)', 'Solicitado', 'Aprobado', 'Cambio aprobado con plan de pruebas y rollback validado.', '2026-11-25 10:10:00'),
]


def _calcular_sla_estado(estado, fecha_limite_str, fecha_cierre_str):
    """Determina si el ticket cumple, esta por vencer o vencio su SLA."""
    try:
        limite = datetime.datetime.strptime(str(fecha_limite_str)[:19], '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return 'A tiempo'

    if estado == 'Cerrado':
        if fecha_cierre_str:
            try:
                cierre = datetime.datetime.strptime(str(fecha_cierre_str)[:19], '%Y-%m-%d %H:%M:%S')
                return 'Cumplido' if cierre <= limite else 'Vencido'
            except ValueError:
                return 'Cumplido'
        return 'Cumplido'

    if estado == 'Rechazado':
        return 'N/A'

    ahora = datetime.datetime.now()
    if ahora > limite:
        return 'Vencido'
    if (limite - ahora).total_seconds() <= 3600:
        return 'Por vencer'
    return 'A tiempo'


def _fila_a_ticket_dto(fila):
    """Convierte una fila MySQL en TicketTIDTO con estado SLA calculado."""
    sla_estado = _calcular_sla_estado(fila['estado'], fila['fecha_limite_sla'], fila.get('fecha_cierre'))
    return TicketTIDTO(
        fila['id_ticket'],
        fila['codigo_ticket'],
        fila['id_usuario_solicitante'],
        fila.get('solicitante_username') or 'sistema',
        fila.get('solicitante_nombre') or 'Usuario',
        fila['tipo_solicitud'],
        fila.get('tipo_cambio') or 'N/A',
        fila['prioridad'],
        fila['area_origen'],
        fila['titulo'],
        fila['descripcion'],
        fila.get('impacto_riesgo'),
        fila.get('plan_pruebas'),
        fila.get('plan_rollback'),
        fila['estado'],
        fila.get('aprobado_por'),
        fila.get('aprobador_nombre'),
        fila.get('tecnico_ti_asignado'),
        fila.get('resolucion_evidencia'),
        fila['sla_horas'],
        fila['fecha_creacion'],
        fila['fecha_limite_sla'],
        fila.get('fecha_cierre'),
        fila.get('jira_issue_key'),
        fila.get('jira_url'),
        fila.get('jira_sincronizado', 0),
        fila.get('jira_ultimo_error'),
        sla_estado=sla_estado,
    )


class ServiceDeskDAO:
    """DAO del Area de TI y Service Desk con lectura en Slave y escritura en Master."""

    @classmethod
    def obtener_tickets(cls, id_usuario_filtro=None):
        """Lista tickets desde el nodo Esclavo (Slave), opcionalmente filtrados por solicitante."""
        conexion = ConexionBD.obtener_conexion_lectura()
        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)
                consulta = """
                    SELECT t.*,
                           u.username AS solicitante_username,
                           u.nombre_completo AS solicitante_nombre,
                           ap.nombre_completo AS aprobador_nombre
                    FROM tickets_ti t
                    INNER JOIN usuarios u ON t.id_usuario_solicitante = u.id_usuario
                    LEFT JOIN usuarios ap ON t.aprobado_por = ap.id_usuario
                """
                params = ()
                if id_usuario_filtro is not None:
                    consulta += " WHERE t.id_usuario_solicitante = %s"
                    params = (id_usuario_filtro,)
                consulta += " ORDER BY t.fecha_creacion DESC, t.id_ticket DESC"
                cursor.execute(consulta, params)
                filas = cursor.fetchall()
                cursor.close()
                conexion.close()
                return [_fila_a_ticket_dto(f) for f in filas]
            except Exception as e:
                print(f"[Error ServiceDeskDAO obtener_tickets] {e}")
                conexion.close()

        tickets = _TICKETS_MEMORIA
        if id_usuario_filtro is not None:
            tickets = [t for t in tickets if t.id_usuario_solicitante == id_usuario_filtro]
        for t in tickets:
            t.sla_estado = _calcular_sla_estado(t.estado, t.fecha_limite_sla, t.fecha_cierre)
        return tickets

    @classmethod
    def obtener_detalle(cls, id_ticket):
        """Obtiene un ticket y su linea de tiempo desde el nodo Esclavo (Slave)."""
        conexion = ConexionBD.obtener_conexion_lectura()
        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT t.*,
                           u.username AS solicitante_username,
                           u.nombre_completo AS solicitante_nombre,
                           ap.nombre_completo AS aprobador_nombre
                    FROM tickets_ti t
                    INNER JOIN usuarios u ON t.id_usuario_solicitante = u.id_usuario
                    LEFT JOIN usuarios ap ON t.aprobado_por = ap.id_usuario
                    WHERE t.id_ticket = %s
                    """,
                    (id_ticket,),
                )
                fila = cursor.fetchone()
                if not fila:
                    cursor.close()
                    conexion.close()
                    return None, []

                cursor.execute(
                    """
                    SELECT h.id_evento, h.id_ticket,
                           COALESCE(u.nombre_completo, 'Sistema') AS usuario_nombre,
                           h.estado_anterior, h.estado_nuevo, h.comentario, h.fecha_hora
                    FROM ticket_historial h
                    LEFT JOIN usuarios u ON h.id_usuario = u.id_usuario
                    WHERE h.id_ticket = %s
                    ORDER BY h.fecha_hora ASC, h.id_evento ASC
                    """,
                    (id_ticket,),
                )
                hist_filas = cursor.fetchall()
                cursor.close()
                conexion.close()
                historial = [
                    TicketHistorialDTO(
                        h['id_evento'],
                        h['id_ticket'],
                        h['usuario_nombre'],
                        h['estado_anterior'],
                        h['estado_nuevo'],
                        h['comentario'],
                        h['fecha_hora'],
                    )
                    for h in hist_filas
                ]
                return _fila_a_ticket_dto(fila), historial
            except Exception as e:
                print(f"[Error ServiceDeskDAO obtener_detalle] {e}")
                conexion.close()

        ticket = next((t for t in _TICKETS_MEMORIA if t.id_ticket == id_ticket), None)
        if not ticket:
            return None, []
        ticket.sla_estado = _calcular_sla_estado(ticket.estado, ticket.fecha_limite_sla, ticket.fecha_cierre)
        historial = [h for h in _HISTORIAL_MEMORIA if h.id_ticket == id_ticket]
        return ticket, historial

    @classmethod
    def crear_ticket(cls, datos_ticket):
        """Inserta un nuevo ticket y su evento inicial en el nodo Maestro (Master)."""
        ahora = datetime.datetime.now()
        prioridad = datos_ticket.get('prioridad', 'Media')
        sla_horas = SLA_HORAS_POR_PRIORIDAD.get(prioridad, 24)
        fecha_limite = ahora + datetime.timedelta(hours=sla_horas)
        fecha_creacion_str = ahora.strftime('%Y-%m-%d %H:%M:%S')
        fecha_limite_str = fecha_limite.strftime('%Y-%m-%d %H:%M:%S')

        tipo_solicitud = datos_ticket.get('tipo_solicitud', 'Incidente')
        tipo_cambio = datos_ticket.get('tipo_cambio', 'N/A') if tipo_solicitud == 'Cambio' else 'N/A'
        id_usuario = int(datos_ticket.get('id_usuario_solicitante') or 1)
        username = datos_ticket.get('solicitante_username') or 'sistema'
        nombre = datos_ticket.get('solicitante_nombre') or username

        conexion = ConexionBD.obtener_conexion()
        if conexion:
            try:
                cursor = conexion.cursor(dictionary=True)
                codigo_temporal = f"TKT-{ahora.strftime('%Y%m%d%H%M%S')}"
                cursor.execute(
                    """
                    INSERT INTO tickets_ti (
                        codigo_ticket, id_usuario_solicitante, tipo_solicitud, tipo_cambio,
                        prioridad, area_origen, titulo, descripcion, impacto_riesgo,
                        plan_pruebas, plan_rollback, estado, sla_horas,
                        fecha_creacion, fecha_limite_sla
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Solicitado', %s, %s, %s)
                    """,
                    (
                        codigo_temporal,
                        id_usuario,
                        tipo_solicitud,
                        tipo_cambio,
                        prioridad,
                        datos_ticket.get('area_origen', 'Operaciones'),
                        datos_ticket['titulo'].strip(),
                        datos_ticket['descripcion'].strip(),
                        datos_ticket.get('impacto_riesgo') or None,
                        datos_ticket.get('plan_pruebas') or None,
                        datos_ticket.get('plan_rollback') or None,
                        sla_horas,
                        fecha_creacion_str,
                        fecha_limite_str,
                    ),
                )
                id_nuevo = cursor.lastrowid
                codigo_final = f"TKT-{ahora.year}-{id_nuevo:04d}"
                cursor.execute(
                    "UPDATE tickets_ti SET codigo_ticket = %s WHERE id_ticket = %s",
                    (codigo_final, id_nuevo),
                )
                cursor.execute(
                    """
                    INSERT INTO ticket_historial (id_ticket, id_usuario, estado_anterior, estado_nuevo, comentario, fecha_hora)
                    VALUES (%s, %s, NULL, 'Solicitado', %s, %s)
                    """,
                    (id_nuevo, id_usuario, f"Ticket {tipo_solicitud} registrado desde Service Desk.", fecha_creacion_str),
                )
                conexion.commit()
                cursor.close()
                conexion.close()

                SeguridadDAO.registrar_auditoria(
                    id_usuario,
                    username,
                    'TI_SERVICEDESK',
                    'INSERT_TICKET',
                    f"Creacion de {codigo_final} ({tipo_solicitud} - {prioridad}): {datos_ticket['titulo'].strip()}",
                )
                ticket_dto, _ = cls.obtener_detalle(id_nuevo)
                if ticket_dto:
                    return ticket_dto
            except Exception as e:
                print(f"[Error ServiceDeskDAO crear_ticket] {e}")
                conexion.rollback()
                conexion.close()

        # Fallback en memoria
        id_nuevo = (max((t.id_ticket for t in _TICKETS_MEMORIA), default=0)) + 1
        codigo_final = f"TKT-{ahora.year}-{id_nuevo:04d}"
        nuevo_dto = TicketTIDTO(
            id_nuevo,
            codigo_final,
            id_usuario,
            username,
            nombre,
            tipo_solicitud,
            tipo_cambio,
            prioridad,
            datos_ticket.get('area_origen', 'Operaciones'),
            datos_ticket['titulo'].strip(),
            datos_ticket['descripcion'].strip(),
            datos_ticket.get('impacto_riesgo') or None,
            datos_ticket.get('plan_pruebas') or None,
            datos_ticket.get('plan_rollback') or None,
            'Solicitado',
            None,
            None,
            None,
            None,
            sla_horas,
            fecha_creacion_str,
            fecha_limite_str,
            None,
            None,
            None,
            False,
            None,
            sla_estado='A tiempo',
        )
        _TICKETS_MEMORIA.insert(0, nuevo_dto)
        _HISTORIAL_MEMORIA.append(
            TicketHistorialDTO(
                len(_HISTORIAL_MEMORIA) + 1,
                id_nuevo,
                nombre,
                None,
                'Solicitado',
                f"Ticket {tipo_solicitud} registrado desde Service Desk.",
                fecha_creacion_str,
            )
        )
        SeguridadDAO.registrar_auditoria(
            id_usuario,
            username,
            'TI_SERVICEDESK',
            'INSERT_TICKET',
            f"Creacion de {codigo_final} ({tipo_solicitud} - {prioridad})",
        )
        return nuevo_dto

    @classmethod
    def actualizar_vinculo_jira(cls, id_ticket, jira_key, jira_url, sincronizado, ultimo_error=None):
        """Actualiza en el Master la clave y estado de sincronizacion con Jira."""
        conexion = ConexionBD.obtener_conexion()
        if conexion:
            try:
                cursor = conexion.cursor()
                cursor.execute(
                    """
                    UPDATE tickets_ti
                    SET jira_issue_key = COALESCE(%s, jira_issue_key),
                        jira_url = COALESCE(%s, jira_url),
                        jira_sincronizado = %s,
                        jira_ultimo_error = %s
                    WHERE id_ticket = %s
                    """,
                    (jira_key, jira_url, 1 if sincronizado else 0, ultimo_error, id_ticket),
                )
                conexion.commit()
                cursor.close()
                conexion.close()
                return True
            except Exception as e:
                print(f"[Error ServiceDeskDAO actualizar_vinculo_jira] {e}")
                conexion.rollback()
                conexion.close()

        for t in _TICKETS_MEMORIA:
            if t.id_ticket == id_ticket:
                if jira_key:
                    t.jira_issue_key = jira_key
                if jira_url:
                    t.jira_url = jira_url
                t.jira_sincronizado = bool(sincronizado)
                t.jira_ultimo_error = ultimo_error
                return True
        return False

    @classmethod
    def _validar_transicion(cls, ticket, nuevo_estado, rol_actor):
        """Aplica reglas de aprobacion de Accesos/Cambios (PDF Semana 10 y 11)."""
        if nuevo_estado not in ESTADOS_VALIDOS:
            return f"Estado '{nuevo_estado}' no es valido."
        if ticket.estado in ('Cerrado', 'Rechazado'):
            return f"El ticket {ticket.codigo_ticket} ya se encuentra en estado final '{ticket.estado}'."

        requiere_aprobacion = ticket.tipo_solicitud in ('Acceso', 'Cambio')
        if requiere_aprobacion and nuevo_estado in ('En atencion', 'Cerrado') and not ticket.aprobado_por and ticket.estado != 'Aprobado':
            return f"Las solicitudes de tipo '{ticket.tipo_solicitud}' requieren aprobacion previa antes de pasar a '{nuevo_estado}'."

        if nuevo_estado == 'Aprobado' and rol_actor not in ('Gerente', 'TI'):
            return "Solo Gerencia o el Area de TI pueden aprobar formalmente una solicitud."

        return None

    @classmethod
    def actualizar_estado(cls, id_ticket, nuevo_estado, id_actor, username_actor, nombre_actor, rol_actor, tecnico_ti=None, resolucion=None, comentario=None):
        """Actualiza el flujo de un ticket en el Master y registra historial + auditoria."""
        ticket, _ = cls.obtener_detalle(id_ticket)
        if not ticket:
            return None, "Ticket no encontrado."

        error_regla = cls._validar_transicion(ticket, nuevo_estado, rol_actor)
        if error_regla:
            return None, error_regla

        ahora_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        estado_anterior = ticket.estado
        aprobado_por = id_actor if nuevo_estado == 'Aprobado' else ticket.aprobado_por
        fecha_cierre = ahora_str if nuevo_estado in ('Cerrado', 'Rechazado') else None
        comentario_final = (comentario or resolucion or f"Estado actualizado a {nuevo_estado}.").strip()

        conexion = ConexionBD.obtener_conexion()
        if conexion:
            try:
                cursor = conexion.cursor()
                cursor.execute(
                    """
                    UPDATE tickets_ti
                    SET estado = %s,
                        aprobado_por = %s,
                        tecnico_ti_asignado = COALESCE(%s, tecnico_ti_asignado),
                        resolucion_evidencia = COALESCE(%s, resolucion_evidencia),
                        fecha_cierre = COALESCE(%s, fecha_cierre)
                    WHERE id_ticket = %s
                    """,
                    (
                        nuevo_estado,
                        aprobado_por,
                        tecnico_ti or None,
                        resolucion or None,
                        fecha_cierre,
                        id_ticket,
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO ticket_historial (id_ticket, id_usuario, estado_anterior, estado_nuevo, comentario, fecha_hora)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (id_ticket, id_actor, estado_anterior, nuevo_estado, comentario_final, ahora_str),
                )
                conexion.commit()
                cursor.close()
                conexion.close()

                SeguridadDAO.registrar_auditoria(
                    id_actor,
                    username_actor,
                    'TI_SERVICEDESK',
                    'UPDATE_TICKET',
                    f"{ticket.codigo_ticket}: {estado_anterior} -> {nuevo_estado}. {comentario_final}",
                )
                actualizado, _ = cls.obtener_detalle(id_ticket)
                return actualizado, None
            except Exception as e:
                print(f"[Error ServiceDeskDAO actualizar_estado] {e}")
                conexion.rollback()
                conexion.close()
                return None, "Error al actualizar el ticket en base de datos."

        # Fallback en memoria
        ticket.estado = nuevo_estado
        ticket.aprobado_por = aprobado_por
        if nuevo_estado == 'Aprobado':
            ticket.aprobador_nombre = nombre_actor
        if tecnico_ti:
            ticket.tecnico_ti_asignado = tecnico_ti
        if resolucion:
            ticket.resolucion_evidencia = resolucion
        if fecha_cierre:
            ticket.fecha_cierre = fecha_cierre
        ticket.sla_estado = _calcular_sla_estado(ticket.estado, ticket.fecha_limite_sla, ticket.fecha_cierre)

        _HISTORIAL_MEMORIA.append(
            TicketHistorialDTO(
                len(_HISTORIAL_MEMORIA) + 1,
                id_ticket,
                nombre_actor,
                estado_anterior,
                nuevo_estado,
                comentario_final,
                ahora_str,
            )
        )
        SeguridadDAO.registrar_auditoria(
            id_actor,
            username_actor,
            'TI_SERVICEDESK',
            'UPDATE_TICKET',
            f"{ticket.codigo_ticket}: {estado_anterior} -> {nuevo_estado}",
        )
        return ticket, None

    @classmethod
    def obtener_metricas(cls):
        """Calcula indicadores clave del Area de TI desde el nodo Esclavo (Slave)."""
        tickets = cls.obtener_tickets()
        abiertos = sum(1 for t in tickets if t.estado not in ('Cerrado', 'Rechazado'))
        criticos_o_vencidos = sum(
            1
            for t in tickets
            if t.estado not in ('Cerrado', 'Rechazado')
            and (t.prioridad in ('Critica', 'Alta') or t.sla_estado == 'Vencido')
        )
        cerrados = sum(1 for t in tickets if t.estado == 'Cerrado')
        sincronizados_jira = sum(1 for t in tickets if t.jira_sincronizado)
        return {
            'ticketsAbiertos': abiertos,
            'ticketsCriticos': criticos_o_vencidos,
            'ticketsCerrados': cerrados,
            'sincronizadosJira': sincronizados_jira,
            'totalTickets': len(tickets),
        }
