# Guía Detallada de Implementación — Jira Service Management & Service Desk TI (SIG-Toyota)

Este documento explica cómo se diseñó, integró y conectó el módulo de **Área de TI (Mesa de Ayuda / Service Desk)** de **SIG-Toyota** con **Jira Service Management Cloud (Atlassian)**, qué archivos intervienen y cómo configurar el archivo `.env` en cada equipo o máquina virtual (MV).

---

## 1. Arquitectura General de la Integración

SIG-Toyota implementa un enfoque **híbrido resiliente (Local-First + Jira Cloud)**:

1. Todo ticket creado en el portal web se guarda primero en la base de datos relacional **MySQL Master (`toyota_db`)** dentro de las tablas `tickets_ti` y `ticket_historial`.
2. De forma automática, el backend invoca a **`JiraService`** (`backend/servicios/JiraService.py`) vía HTTPS usando **REST APIs de Atlassian (`Basic Auth` con Correo + API Token)**.
3. Primero intenta crear la solicitud por **Jira Service Management API (`/rest/servicedeskapi/request`)** asociando un `serviceDeskId` y un `requestTypeId` para que el ticket aparezca en las colas oficiales de **Incidentes** o **Solicitudes de servicio** de Jira. Si el proyecto fuera Jira Software estándar o no devolviera un Service Desk, hace fallback automático a **Jira REST API v3 (`/rest/api/3/issue`)**.
4. Cada cambio de estado en SIG-Toyota (por ejemplo, de `Solicitado` → `En atencion` → `Cerrado`) añade un comentario de trazabilidad y ejecuta las **transiciones de workflow** correspondientes en Jira, manejando incluso transiciones intermedias (`Pending` → `Work in progress` → `Completado`) y campos obligatorios como `resolution`.
5. Si en algún entorno faltan credenciales `.env` o no hay conexión a internet, SIG-Toyota **no se cae**: el ticket queda guardado en MySQL con `jira_sincronizado = FALSE` y puede re-sincronizarse luego con el botón **Sync Jira**.

---

## 2. Archivos del Proyecto Utilizados

### Base de Datos (`database/`)
* **`database/toyota_db.sql`**: Define las tablas que soportan el flujo ITIL y el vínculo con Jira:
  * `tickets_ti`: código correlativo (`TKT-2026-XXXX`), solicitante, `tipo_solicitud` (`Incidente`, `Servicio`, `Informacion`, `Acceso`, `Cambio`), `tipo_cambio` (`N/A`, `Estandar`, `Normal`, `Emergencia`), `prioridad`, `area_origen`, campos de control de cambios (`impacto_riesgo`, `plan_pruebas`, `plan_rollback`), `estado`, `resolucion_evidencia`, cálculo de SLA (`sla_horas`, `fecha_limite_sla`, `fecha_cierre`), además de los campos Jira (`jira_issue_key`, `jira_issue_url`, `jira_sincronizado`, `jira_ultimo_error`).
  * `ticket_historial`: bitácora cronológica de cada cambio de estado y actor responsable.

### Backend (`backend/`)
* **`backend/models/entidades.py`**: Clases DTO `TicketTIDTO` y `TicketHistorialDTO`.
* **`backend/dao/ServiceDeskDAO.py`**:
  * Reglas de negocio y SLA por prioridad (`Critica: 2h`, `Alta: 4h`, `Media: 24h`, `Baja: 48h`).
  * Cálculo de cumplimiento de SLA (`_calcular_sla_estado`: `A tiempo`, `Por vencer`, `Vencido`, `Cumplido`).
  * Regla de segregación de funciones: los tickets de tipo **`Acceso`** o **`Cambio`** (Normal/Emergencia) requieren aprobación previa (`Gerente` o `TI`) antes de pasar a `En atencion` o `Cerrado`.
  * Método `actualizar_vinculo_jira(...)` y fallback en memoria (`_TICKETS_MEMORIA` / `_HISTORIAL_MEMORIA`) si se ejecutan pruebas sin MySQL.
* **`backend/servicios/JiraService.py`**: Cliente HTTP nativo (`urllib.request`, timeout `8s`) con las siguientes capacidades:
  * `verificar_conexion()`: valida credenciales contra `GET /rest/api/3/myself`.
  * `_resolver_jsm_request_type()`: detecta `serviceDeskId` y asigna el `requestTypeId` adecuado según sea `Incidente`, `Acceso`, `Servicio`, `Informacion` o `Cambio`.
  * `crear_issue(ticket_dto)`: publica en `/rest/servicedeskapi/request` (o fallback `/rest/api/3/issue` en formato ADF) y asigna prioridad (`Highest`, `High`, `Medium`, `Low`).
  * `agregar_comentario(issue_key, texto)`: registra cada actualización del Service Desk como comentario en Atlassian.
  * `transicionar_estado(issue_key, estado_destino)`: mapea los estados de SIG-Toyota (`Solicitado`, `En evaluacion`, `Aprobado`, `En atencion`, `Cerrado`, `Rechazado`) a las transiciones reales disponibles del proyecto en Jira, evitando retroceder tickets en progreso a `Pending` y completando automáticamente saltos de dos pasos (`Pending` → `Work in progress` → `Completado`) o campo `resolution` si Jira lo solicita.
  * `consultar_issue(issue_key)`: obtiene el estado y responsable actual desde Jira.
* **`backend/app.py`**: Expone los endpoints REST del módulo:
  * `GET /api/tickets/jira-config`: diagnóstico en vivo de conectividad con Jira (sin exponer tokens).
  * `GET /api/tickets/metricas`: KPIs del Área de TI (abiertos, críticos, cerrados, sincronizados con Jira).
  * `GET /api/tickets`: lista tickets globales (para TI/Gerente) o filtrados al solicitante (para Operador).
  * `POST /api/tickets`: crea en MySQL Master y dispara `JiraService.crear_issue`.
  * `GET /api/tickets/<id_ticket>`: retorna detalle del ticket y su historial.
  * `PUT /api/tickets/<id_ticket>/estado`: actualiza etapa ITIL, añade comentario y mueve estado en Jira.
  * `POST /api/tickets/<id_ticket>/jira-sync`: crea el issue si quedó pendiente o consulta su estado actual en Jira.
* **`backend/tests/test_api.py`**: Incluye pruebas automatizadas (`test_login_soporte_ti_exitoso`, `test_crear_ticket_service_desk_y_jira`, `test_regla_aprobacion_acceso_service_desk`).

### Frontend (`frontend/`)
* **`frontend/src/servicios/api.js`**: Funciones HTTP hacia `/api/tickets*`.
* **`frontend/src/ServiceDeskFlotante.jsx`**: Botón flotante (`🎫 Service Desk TI`) disponible en toda la aplicación para que cualquier rol registre Incidentes, Solicitudes, Accesos o Cambios y revise sus propios tickets.
* **`frontend/src/AreaTI.jsx`**: Consola completa de Mesa de Ayuda TI (`Solicitado` → `En evaluacion` → `Aprobado` → `En atencion` → `Cerrado`), filtros, evidencia de resolución, historial de trazabilidad, estado de conexión Jira y botón **Sync Jira**.
* **`frontend/src/App.jsx`** y **`frontend/src/estilos.css`**: Registro del rol `TI`, vista del módulo y estilos del widget flotante y flujo visual.

### Infraestructura (`docker-compose.yml`, `.env.example`, `.gitignore`)
* **`docker-compose.yml`**: Pasa las variables `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY` y `JIRA_ISSUE_TYPE` al contenedor `backend`.
* **`.gitignore`**: Excluye `.env` y `.env.local` para que **nunca se suban credenciales privadas a GitHub**.

---

## 3. Funcionalidades Principales

1. **Registro multicanal desde la Web:** cualquier usuario autenticado reporta Incidentes, Solicitudes de Servicio, Accesos o Control de Cambios desde el botón flotante.
2. **Clasificación automática en Jira Service Management:**
   * Los tickets de tipo **`Incidente`** se enrutan al tipo de solicitud de incidente y aparecen en la cola **Open incidents / Incidentes** de Jira.
   * Los de **`Servicio` / `Acceso` / `Informacion`** se enrutan a **Solicitudes de servicio / Service requests**.
   * Todos se reflejan en el tablero **Actividad en varios espacios** con su clave (ej. `PROJ-1`).
3. **Sincronización de ciclo de vida y trazabilidad:** aprobar, atender o cerrar un ticket en SIG-Toyota actualiza los comentarios y mueve la tarjeta en Jira automáticamente hasta **Completado / Hecho**, registrando evidencia de solución y cumplimiento de SLA.
4. **Control de Cambios con validación:** los requerimientos de acceso y cambio normal/emergencia exigen aprobación antes de pasar a ejecución.

---

## 4. Configuración del Archivo `.env` (Para el Equipo / Compañeros)

Por seguridad, el archivo `.env` real **no se sube al repositorio**. Cada integrante que levante el proyecto en Docker (o en la Máquina Virtual) debe hacer lo siguiente:

1. En la raíz del proyecto (`ToyotaSIE/`, al mismo nivel que `docker-compose.yml`), crear o editar el archivo llamado **`.env`** (puedes copiar `.env.example` y renombrarlo a `.env`).
2. Pegar el siguiente contenido y **reemplazar los valores indicados (sobre todo el token enviado por WhatsApp)**:

```env
# URL base de la instancia Jira Cloud del proyecto SIG-Toyota
JIRA_BASE_URL=https://toyota-sie.atlassian.net

# Correo de la cuenta Atlassian asociada al API Token
JIRA_EMAIL=REEMPLAZAR_CON_EL_CORREO_DEL_TOKEN@gmail.com

# API Token generado en https://id.atlassian.com/manage-profile/security/api-tokens
# Reemplazar con el token privado compartido por WhatsApp
JIRA_API_TOKEN=REEMPLAZAR_CON_EL_TOKEN_ENVIADO_POR_WHATSAPP

# Clave del proyecto en Jira Service Management
JIRA_PROJECT_KEY=PROJ

# Opcional: dejar vacio para autodeteccion automatica de JSM (Incident / Service Request)
JIRA_ISSUE_TYPE=
```

### Cómo aplicar cambios después de crear o editar `.env`
Cada vez que modifiques el `.env`, reconstruye o recrea el contenedor `backend` para que cargue las nuevas variables de entorno:

```bash
docker compose up -d --force-recreate backend
```

Para comprobar que la conexión quedó activa sin errores:
* Desde navegador o `curl`: `http://localhost:8080/api/tickets/jira-config` → debe responder `"configurado": true` y `"conectado": true`.
* Desde la interfaz web: ingresar con rol **TI** o **Gerente** al módulo **Área de TI** y verificar la insignia verde **"Jira Cloud Conectado (PROJ)"**.
