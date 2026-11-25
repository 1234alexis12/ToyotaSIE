import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request


class JiraService:
    """Cliente ligero para sincronizar tickets del Service Desk con Jira Cloud y JSM."""

    TIMEOUT_SEGUNDOS = 8

    @classmethod
    def _obtener_config(cls):
        base_url = os.getenv('JIRA_BASE_URL', '').strip().rstrip('/')
        email = os.getenv('JIRA_EMAIL', '').strip()
        api_token = os.getenv('JIRA_API_TOKEN', '').strip()
        project_key = os.getenv('JIRA_PROJECT_KEY', '').strip().upper()
        issue_type_env = os.getenv('JIRA_ISSUE_TYPE', '').strip()
        return {
            'base_url': base_url,
            'email': email,
            'api_token': api_token,
            'project_key': project_key,
            'issue_type_env': issue_type_env,
        }

    @classmethod
    def esta_configurado(cls):
        """Indica si todas las credenciales minimas de Jira estan presentes."""
        cfg = cls._obtener_config()
        return all([cfg['base_url'], cfg['email'], cfg['api_token'], cfg['project_key']])

    @classmethod
    def _construir_headers(cls, cfg):
        credenciales = f"{cfg['email']}:{cfg['api_token']}".encode('utf-8')
        token_b64 = base64.b64encode(credenciales).decode('ascii')
        return {
            'Authorization': f'Basic {token_b64}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    @classmethod
    def _peticion_json(cls, metodo, url, headers, payload=None):
        """Ejecuta una llamada HTTP JSON hacia Jira y retorna (status, data, error)."""
        cuerpo = json.dumps(payload).encode('utf-8') if payload is not None else None
        req = urllib.request.Request(url, data=cuerpo, headers=headers, method=metodo)
        try:
            with urllib.request.urlopen(req, timeout=cls.TIMEOUT_SEGUNDOS) as resp:
                raw = resp.read().decode('utf-8')
                data = json.loads(raw) if raw else {}
                return resp.status, data, None
        except urllib.error.HTTPError as e:
            detalle = e.read().decode('utf-8', errors='replace')
            return e.code, None, f"HTTP {e.code}: {detalle[:200]}"
        except Exception as e:
            return 0, None, str(e)[:200]

    @classmethod
    def verificar_conexion(cls):
        """Diagnostica la configuracion y conectividad real contra Jira (/rest/api/3/myself)."""
        cfg = cls._obtener_config()
        if not cls.esta_configurado():
            return {
                'configurado': False,
                'conectado': False,
                'project_key': cfg['project_key'] or None,
                'base_url': cfg['base_url'] or None,
                'mensaje': 'Faltan variables JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN o JIRA_PROJECT_KEY.',
            }

        headers = cls._construir_headers(cfg)
        status, data, err = cls._peticion_json('GET', f"{cfg['base_url']}/rest/api/3/myself", headers)
        if status == 200 and data:
            return {
                'configurado': True,
                'conectado': True,
                'project_key': cfg['project_key'],
                'base_url': cfg['base_url'],
                'cuenta_jira': data.get('displayName') or data.get('emailAddress'),
                'mensaje': 'Conectado correctamente a Jira Cloud.',
            }

        return {
            'configurado': True,
            'conectado': False,
            'project_key': cfg['project_key'],
            'base_url': cfg['base_url'],
            'mensaje': f'No se pudo autenticar con Jira: {err}',
        }

    @classmethod
    def _construir_lineas_descripcion(cls, ticket_dto):
        """Construye las lineas estructuradas del detalle del ticket."""
        lineas = [
            f"Codigo Interno SIG-Toyota: {ticket_dto.codigo_ticket}",
            f"Solicitante: {ticket_dto.solicitante_nombre} ({ticket_dto.solicitante_username})",
            f"Area de Origen: {ticket_dto.area_origen}",
            f"Tipo de Solicitud: {ticket_dto.tipo_solicitud}"
            + (f" ({ticket_dto.tipo_cambio})" if ticket_dto.tipo_solicitud == 'Cambio' else ''),
            f"Prioridad: {ticket_dto.prioridad} | SLA: {ticket_dto.sla_horas}h (Limite: {ticket_dto.fecha_limite_sla})",
            f"Descripcion: {ticket_dto.descripcion}",
        ]
        if ticket_dto.tipo_solicitud == 'Cambio':
            lineas.extend([
                f"Impacto / Riesgo: {ticket_dto.impacto_riesgo or 'No especificado'}",
                f"Plan de Pruebas: {ticket_dto.plan_pruebas or 'No especificado'}",
                f"Plan de Rollback: {ticket_dto.plan_rollback or 'No especificado'}",
            ])
        return lineas

    @classmethod
    def _resolver_jsm_request_type(cls, cfg, headers, tipo_solicitud):
        """Obtiene (serviceDeskId, requestTypeId) si el proyecto es Jira Service Management."""
        st, sds, _ = cls._peticion_json('GET', f"{cfg['base_url']}/rest/servicedeskapi/servicedesk", headers)
        if st != 200 or not sds:
            return None, None

        sd_match = next(
            (sd for sd in sds.get('values', []) if (sd.get('projectKey') or '').upper() == cfg['project_key']),
            None,
        )
        if not sd_match:
            return None, None

        sd_id = str(sd_match['id'])
        st_rt, rts, _ = cls._peticion_json(
            'GET',
            f"{cfg['base_url']}/rest/servicedeskapi/servicedesk/{sd_id}/requesttype",
            headers,
        )
        if st_rt != 200 or not rts or not rts.get('values'):
            return None, None

        tipos = rts['values']
        preferencias = {
            'Incidente': ['report a system problem', 'report broken hardware', 'incident', 'incidente'],
            'Acceso': ['request admin access', 'request a new account', 'acceso'],
            'Servicio': ['get it help', 'request new software', 'request new hardware', 'service'],
            'Informacion': ['get it help', 'general'],
            'Cambio': ['request a change', 'change', 'cambio', 'get it help'],
        }.get(tipo_solicitud, ['get it help'])

        mapa = {(rt.get('name') or '').lower(): str(rt.get('id')) for rt in tipos}
        for candidato in preferencias:
            for nombre_rt, rt_id in mapa.items():
                if candidato in nombre_rt:
                    return sd_id, rt_id

        return sd_id, str(tipos[0]['id'])

    @classmethod
    def _resolver_issue_type(cls, cfg, headers, tipo_solicitud):
        """Detecta automaticamente un Issue Type valido en proyectos Jira Software."""
        if cfg['issue_type_env']:
            return cfg['issue_type_env']

        url = f"{cfg['base_url']}/rest/api/3/project/{urllib.parse.quote(cfg['project_key'])}"
        status, data, _ = cls._peticion_json('GET', url, headers)
        if status != 200 or not data:
            return 'Task'

        tipos = [t for t in data.get('issueTypes', []) if not t.get('subtask')]
        if not tipos:
            return 'Task'

        preferencias = {
            'Incidente': ['[system] incident', 'incident', 'incidente', 'bug', 'error', 'task', 'tarea'],
            'Servicio': ['[system] service request', 'service request', 'solicitud', 'task', 'tarea'],
            'Informacion': ['[system] service request', 'task', 'tarea', 'story', 'historia'],
            'Acceso': ['[system] service request', 'service request', 'task', 'tarea'],
            'Cambio': ['[system] change', 'change', 'cambio', 'task', 'tarea'],
        }.get(tipo_solicitud, ['task', 'tarea'])

        mapa_nombres = {t.get('name', '').lower(): t.get('name') for t in tipos}
        for candidato in preferencias:
            if candidato in mapa_nombres:
                return mapa_nombres[candidato]

        return tipos[0].get('name', 'Task')

    @classmethod
    def _texto_a_adf(cls, lineas):
        """Convierte lineas de texto al formato Atlassian Document Format (ADF) requerido por API v3."""
        contenido = []
        for linea in lineas:
            texto = str(linea).strip()
            if not texto:
                continue
            contenido.append({
                'type': 'paragraph',
                'content': [{'type': 'text', 'text': texto}],
            })
        if not contenido:
            contenido.append({'type': 'paragraph', 'content': [{'type': 'text', 'text': 'Sin detalle adicional.'}]})
        return {'type': 'doc', 'version': 1, 'content': contenido}

    @classmethod
    def crear_issue(cls, ticket_dto):
        """Crea el ticket en JSM (con Request Type para colas) o Jira Software y retorna clave y URL."""
        cfg = cls._obtener_config()
        if not cls.esta_configurado():
            return {'ok': False, 'key': None, 'url': None, 'error': 'Jira no configurado en variables de entorno.'}

        headers = cls._construir_headers(cfg)
        resumen = f"[{ticket_dto.codigo_ticket}] [{ticket_dto.tipo_solicitud}] {ticket_dto.titulo}"[:240]
        lineas = cls._construir_lineas_descripcion(ticket_dto)
        prioridad_jira = {
            'Critica': 'Highest',
            'Alta': 'High',
            'Media': 'Medium',
            'Baja': 'Low',
        }.get(ticket_dto.prioridad, 'Medium')

        # 1. Intentar via Jira Service Management API para que aparezca en Colas / Incidentes / Solicitudes
        sd_id, rt_id = cls._resolver_jsm_request_type(cfg, headers, ticket_dto.tipo_solicitud)
        if sd_id and rt_id:
            payload_jsm = {
                'serviceDeskId': sd_id,
                'requestTypeId': rt_id,
                'requestFieldValues': {
                    'summary': resumen,
                    'description': '\n'.join(lineas),
                },
            }
            st_jsm, data_jsm, _ = cls._peticion_json(
                'POST',
                f"{cfg['base_url']}/rest/servicedeskapi/request",
                headers,
                payload_jsm,
            )
            if st_jsm in (200, 201) and data_jsm and data_jsm.get('issueKey'):
                key = data_jsm['issueKey']
                # Asignar prioridad en Jira (si el esquema del proyecto la habilita)
                cls._peticion_json(
                    'PUT',
                    f"{cfg['base_url']}/rest/api/3/issue/{urllib.parse.quote(key)}",
                    headers,
                    {'fields': {'priority': {'name': prioridad_jira}}},
                )
                return {
                    'ok': True,
                    'key': key,
                    'url': f"{cfg['base_url']}/browse/{key}",
                    'error': None,
                }

        # 2. Fallback estandar Jira REST API v3 (proyectos Jira Software o si JSM no aplica)
        issue_type = cls._resolver_issue_type(cfg, headers, ticket_dto.tipo_solicitud)
        payload = {
            'fields': {
                'project': {'key': cfg['project_key']},
                'summary': resumen,
                'description': cls._texto_a_adf(lineas),
                'issuetype': {'name': issue_type},
                'priority': {'name': prioridad_jira},
            }
        }

        url = f"{cfg['base_url']}/rest/api/3/issue"
        status, data, err = cls._peticion_json('POST', url, headers, payload)

        if status == 400 and err and 'priority' in err.lower():
            payload['fields'].pop('priority', None)
            status, data, err = cls._peticion_json('POST', url, headers, payload)

        if status in (200, 201) and data and data.get('key'):
            key = data['key']
            return {
                'ok': True,
                'key': key,
                'url': f"{cfg['base_url']}/browse/{key}",
                'error': None,
            }

        return {'ok': False, 'key': None, 'url': None, 'error': err or 'Error al crear ticket en Jira.'}

    @classmethod
    def agregar_comentario(cls, issue_key, texto):
        """Agrega un comentario de trazabilidad en el issue de Jira."""
        if not issue_key or not cls.esta_configurado():
            return False
        cfg = cls._obtener_config()
        headers = cls._construir_headers(cfg)
        url = f"{cfg['base_url']}/rest/api/3/issue/{urllib.parse.quote(issue_key)}/comment"
        status, _, _ = cls._peticion_json('POST', url, headers, {'body': cls._texto_a_adf([texto])})
        return status in (200, 201)

    @classmethod
    def _buscar_transicion(cls, transiciones, sinonimos, categoria_fallback=None, excluir_palabras=()):
        """Selecciona la mejor transicion segun sinonimos o categoria de estado."""
        for t in transiciones:
            nombre_t = (t.get('name') or '').lower()
            nombre_to = ((t.get('to') or {}).get('name') or '').lower()
            if any(ex in nombre_t or ex in nombre_to for ex in excluir_palabras):
                continue
            if any(s in nombre_t or s in nombre_to for s in sinonimos):
                return t

        if categoria_fallback:
            for t in transiciones:
                cat = (((t.get('to') or {}).get('statusCategory') or {}).get('key') or '').lower()
                nombre_t = (t.get('name') or '').lower()
                nombre_to = ((t.get('to') or {}).get('name') or '').lower()
                if any(ex in nombre_t or ex in nombre_to for ex in excluir_palabras):
                    continue
                if cat == categoria_fallback:
                    return t
        return None

    @classmethod
    def _ejecutar_transicion(cls, cfg, headers, issue_key, transicion):
        """Ejecuta una transicion especifica manejando resolution obligatorio si aplica."""
        url_trans = f"{cfg['base_url']}/rest/api/3/issue/{urllib.parse.quote(issue_key)}/transitions"
        st_post, _, err_post = cls._peticion_json(
            'POST', url_trans, headers, {'transition': {'id': transicion.get('id')}}
        )
        if st_post in (200, 204):
            return True

        if st_post == 400 and err_post and 'resolution' in err_post.lower():
            res_field = (transicion.get('fields') or {}).get('resolution') or {}
            permitidos = res_field.get('allowedValues') or []
            nombre_res = permitidos[0].get('name') if permitidos else 'Done'
            st_retry, _, _ = cls._peticion_json(
                'POST',
                url_trans,
                headers,
                {'transition': {'id': transicion.get('id')}, 'fields': {'resolution': {'name': nombre_res}}},
            )
            return st_retry in (200, 204)
        return False

    @classmethod
    def transicionar_estado(cls, issue_key, estado_destino):
        """Mueve el estado del ticket en Jira respetando flujos JSM (ej. Pending -> Work in progress -> Completado)."""
        if not issue_key or not cls.esta_configurado():
            return False

        cfg = cls._obtener_config()
        headers = cls._construir_headers(cfg)

        # Consultar estado actual para evitar degradar Work in progress a Pending
        consulta_actual = cls.consultar_issue(issue_key)
        estado_actual_jira = (consulta_actual.get('estado_jira') or '').lower() if consulta_actual.get('ok') else ''
        en_progreso_ya = any(p in estado_actual_jira for p in ('work in progress', 'in progress', 'en curso', 'en progreso'))

        if estado_destino in ('En evaluacion', 'Aprobado', 'En atencion') and en_progreso_ya:
            return True

        url_trans = f"{cfg['base_url']}/rest/api/3/issue/{urllib.parse.quote(issue_key)}/transitions"
        status, data, _ = cls._peticion_json('GET', f"{url_trans}?expand=transitions.fields", headers)
        if status != 200 or not data:
            return False

        transiciones = data.get('transitions', [])
        sinonimos_por_estado = {
            'Solicitado': ['to do', 'por hacer', 'open', 'abierto', 'abierta'],
            'En evaluacion': ['in progress', 'en curso', 'en progreso', 'work in progress', 'investigar'],
            'Aprobado': ['in progress', 'approved', 'aprobado', 'en curso', 'work in progress', 'investigar'],
            'En atencion': ['in progress', 'en curso', 'en progreso', 'work in progress', 'investigar', 'working'],
            'Cerrado': ['resolver', 'completado', 'hecho', 'done', 'listo', 'finalizado', 'cerrado', 'resolved', 'resuelto', 'closed'],
            'Rechazado': ['cancelar', 'cancelado', 'cancelled', 'rechazado', 'declined'],
        }
        sinonimos = sinonimos_por_estado.get(estado_destino, [])

        if estado_destino in ('En evaluacion', 'Aprobado', 'En atencion'):
            elegida = cls._buscar_transicion(
                transiciones, sinonimos, categoria_fallback='indeterminate', excluir_palabras=('pendiente', 'pending')
            )
            return cls._ejecutar_transicion(cfg, headers, issue_key, elegida) if elegida else False

        if estado_destino == 'Cerrado':
            elegida = cls._buscar_transicion(
                transiciones, sinonimos, categoria_fallback='done', excluir_palabras=('cancel', 'rechaz')
            )
            if elegida:
                return cls._ejecutar_transicion(cfg, headers, issue_key, elegida)

            # Si esta en Pending u otro estado intermedio sin salida directa a Completado, pasar primero a Work in progress
            paso_intermedio = cls._buscar_transicion(
                transiciones,
                ['work in progress', 'in progress', 'en curso', 'investigar'],
                categoria_fallback='indeterminate',
                excluir_palabras=('pendiente', 'pending'),
            )
            if paso_intermedio and cls._ejecutar_transicion(cfg, headers, issue_key, paso_intermedio):
                st2, data2, _ = cls._peticion_json('GET', f"{url_trans}?expand=transitions.fields", headers)
                if st2 == 200 and data2:
                    final = cls._buscar_transicion(
                        data2.get('transitions', []),
                        sinonimos,
                        categoria_fallback='done',
                        excluir_palabras=('cancel', 'rechaz'),
                    )
                    if final:
                        return cls._ejecutar_transicion(cfg, headers, issue_key, final)
            return False

        elegida = cls._buscar_transicion(
            transiciones,
            sinonimos,
            categoria_fallback='done' if estado_destino == 'Rechazado' else None,
        )
        return cls._ejecutar_transicion(cfg, headers, issue_key, elegida) if elegida else False

    @classmethod
    def consultar_issue(cls, issue_key):
        """Consulta el estado actual del ticket directamente en Jira Cloud."""
        if not issue_key or not cls.esta_configurado():
            return {'ok': False, 'error': 'Jira no configurado o clave invalida.'}
        cfg = cls._obtener_config()
        headers = cls._construir_headers(cfg)
        url = f"{cfg['base_url']}/rest/api/3/issue/{urllib.parse.quote(issue_key)}?fields=status,summary,assignee"
        status, data, err = cls._peticion_json('GET', url, headers)
        if status != 200 or not data:
            return {'ok': False, 'error': err or 'No se pudo consultar Jira.'}
        fields = data.get('fields') or {}
        estado_jira = ((fields.get('status') or {}).get('name')) or 'Desconocido'
        asignado = ((fields.get('assignee') or {}).get('displayName')) or None
        return {
            'ok': True,
            'key': issue_key,
            'estado_jira': estado_jira,
            'asignado_jira': asignado,
            'url': f"{cfg['base_url']}/browse/{issue_key}",
        }
