# Diccionario de Datos del Sistema SIG-Toyota
**Base de Datos:** `toyota_db` | **Motor:** MySQL 8.0 (InnoDB) | **Cotejamiento:** `utf8mb4_unicode_ci`  
**Referencia Template:** Sección 2.2.1.5.3 del Informe Final

---

### 1. Entidad: `usuarios`
Almacena las credenciales y perfiles de los operadores y personal directivo del sistema.

| Key | Nombre | Campo | Tipo de Dato | Tamaño | Nulo | Descripción |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PK** | Identificador de Usuario | `id_usuario` | INT | - | NO | Identificador único autoincremental del usuario. |
| **UQ** | Nombre de Usuario | `username` | VARCHAR | 50 | NO | Alias único de acceso al sistema (ej. `admin_gerente`). |
| - | Hash de Contraseña | `password_hash` | VARCHAR | 255 | NO | Clave encriptada con algoritmo seguro `bcrypt`. |
| - | Nombre Completo | `nombre_completo` | VARCHAR | 120 | NO | Nombres y apellidos del colaborador. |
| - | Rol de Acceso | `rol` | ENUM | 10 | NO | Perfil RBAC asignado (`Gerente` o `Operador`). |
| - | Estado de Cuenta | `estado` | ENUM | 10 | NO | Estado operativo (`Activo` o `Inactivo`). |
| - | Fecha de Creación | `fecha_creacion` | TIMESTAMP | - | NO | Marca temporal de registro del usuario. |

---

### 2. Entidad: `auditoria`
Bitácora histórica inmutable para trazabilidad y cumplimiento de la norma **ISO/IEC 27001 (Control A.12.4)**.

| Key | Nombre | Campo | Tipo de Dato | Tamaño | Nulo | Descripción |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PK** | Identificador de Log | `id_log` | INT | - | NO | Clave primaria autoincremental de la auditoría. |
| **FK** | Usuario Responsable | `id_usuario` | INT | - | SÍ | Referencia al usuario ejecutor (`usuarios.id_usuario`). |
| - | Módulo Afectado | `modulo` | VARCHAR | 40 | NO | Módulo donde ocurrió el evento (`SEGURIDAD`, `VENTAS`, `LOGISTICA`, `TALLER`). |
| - | Acción Realizada | `accion` | VARCHAR | 50 | NO | Operación ejecutada (`LOGIN`, `INSERT`, `UPDATE_ESTADO`). |
| - | Detalle Técnico | `detalle` | TEXT | - | NO | Descripción puntual de los valores o cambios realizados. |
| - | Fecha y Hora | `fecha_hora` | DATETIME | - | NO | Estampa de tiempo exacta del suceso. |

---

### 3. Entidad: `clientes`
Directorio de clientes particulares y corporativos atendidos por el concesionario.

| Key | Nombre | Campo | Tipo de Dato | Tamaño | Nulo | Descripción |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PK** | Identificador de Cliente | `id_cliente` | INT | - | NO | Clave primaria autoincremental del cliente. |
| **UQ / IDX** | Documento de Identidad | `dni_ruc` | VARCHAR | 20 | NO | DNI (8 dígitos) o RUC (11 dígitos). Con índice `idx_clientes_dni`. |
| - | Nombre o Razón Social | `nombre_razon` | VARCHAR | 150 | NO | Nombre del titular o razón social de la empresa. |
| - | Teléfono | `telefono` | VARCHAR | 30 | SÍ | Número celular o de contacto comercial. |
| - | Correo Electrónico | `email` | VARCHAR | 100 | SÍ | Dirección de correo para cotizaciones y facturas. |
| - | Tipo de Cliente | `tipo_cliente` | ENUM | 15 | NO | Clasificación del cliente (`Particular` o `Corporativo`). |
| - | Fecha de Registro | `fecha_registro` | TIMESTAMP | - | NO | Fecha y hora en que se ingresó al cliente. |

---

### 4. Entidad: `inventario`
Control físico y contable de vehículos nuevos y repuestos OEM de Toyota.

| Key | Nombre | Campo | Tipo de Dato | Tamaño | Nulo | Descripción |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PK** | Identificador de Ítem | `id_item` | INT | - | NO | Clave primaria autoincremental del ítem. |
| **UQ / IDX** | Código Identificador | `codigo_vin_sku` | VARCHAR | 60 | NO | Número de Chasis VIN (17 caracteres) o código SKU de repuesto OEM. Con índice `idx_inventario_codigo`. |
| - | Tipo de Ítem | `tipo` | ENUM | 10 | NO | Categoría del ítem (`Vehiculo` o `Repuesto`). |
| - | Nombre o Modelo | `nombre_modelo` | VARCHAR | 150 | NO | Denominación comercial (ej. `Toyota Hilux 4x4 Doble Cabina SRX`). |
| - | Stock Físico Actual | `stock_actual` | INT | - | NO | Cantidad disponible en patio o almacén (Validación $\ge 0$). |
| - | Stock Mínimo de Seguridad | `stock_minimo` | INT | - | NO | Umbral crítico que dispara alerta visual de reposición. |
| - | Precio de Venta (USD) | `precio_usd` | DECIMAL | 10,2 | NO | Valor unitario en dólares americanos. |
| - | Última Actualización | `ultima_actualizacion`| TIMESTAMP | - | NO | Marca de tiempo del último movimiento o ajuste. |

---

### 5. Entidad: `ventas`
Registro de cotizaciones formales y ventas concluidas de vehículos.

| Key | Nombre | Campo | Tipo de Dato | Tamaño | Nulo | Descripción |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PK** | Identificador de Venta | `id_venta` | INT | - | NO | Clave primaria autoincremental de la transacción. |
| **FK** | Cliente Comprador | `id_cliente` | INT | - | NO | Clave foránea referenciando a `clientes(id_cliente)`. |
| **FK** | Vehículo Asignado | `id_item` | INT | - | NO | Clave foránea referenciando al vehículo en `inventario(id_item)`. |
| **FK** | Asesor Comercial | `id_usuario` | INT | - | NO | Clave foránea del colaborador en `usuarios(id_usuario)`. |
| - | Monto Total (USD) | `precio_total` | DECIMAL | 10,2 | NO | Importe facturado en dólares americanos. |
| - | Estado de la Operación | `estado` | ENUM | 15 | NO | Flujo comercial (`Prospecto`, `Cotizado`, `Vendido`). |
| **IDX** | Fecha de Emisión | `fecha` | DATE | - | NO | Fecha de la operación. Con índice `idx_ventas_fecha`. |

---

### 6. Entidad: `ordenes_taller`
Seguimiento de órdenes de trabajo técnico (OT) en el área de posventa.

| Key | Nombre | Campo | Tipo de Dato | Tamaño | Nulo | Descripción |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PK** | Identificador de Orden | `id_orden` | INT | - | NO | Clave primaria autoincremental de la orden de taller. |
| **FK** | Propietario / Cliente | `id_cliente` | INT | - | NO | Clave foránea referenciando a `clientes(id_cliente)`. |
| **FK** | Repuesto Utilizado | `id_item_repuesto`| INT | - | SÍ | Clave foránea referenciando a `inventario(id_item)` o NULL. |
| - | Placa o Chasis | `placa_vin` | VARCHAR | 30 | NO | Placa vehicular o VIN de la unidad en servicio. |
| - | Tipo de Servicio | `tipo_servicio` | VARCHAR | 100 | NO | Modalidad (`Mantenimiento Preventivo`, `PDI`, `Reparación`). |
| - | Técnico Asignado | `tecnico` | VARCHAR | 100 | NO | Nombre del mecánico especialista responsable. |
| - | Costo del Servicio (USD) | `costo_usd` | DECIMAL | 10,2 | NO | Total facturado por mano de obra e insumos. |
| **IDX** | Estado Operativo | `estado` | ENUM | 15 | NO | Estado del servicio (`Pendiente`, `En proceso`, `Entregado`). Con índice `idx_taller_estado`. |
| - | Fecha de Ingreso | `fecha_ingreso` | DATE | - | NO | Fecha de recepción del vehículo en el taller. |


---

### 7. Entidad: `tickets_ti`
Registro centralizado de incidentes, solicitudes de servicio/información/acceso y control de cambios del Área de TI (ITIL / ISO/IEC 20000-1), con vinculación a Jira Cloud.

| Key | Nombre | Campo | Tipo de Dato | Tamaño | Nulo | Descripción |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PK** | Identificador de Ticket | `id_ticket` | INT | - | NO | Clave primaria autoincremental del ticket TI. |
| **UQ** | Código del Ticket | `codigo_ticket` | VARCHAR | 25 | NO | Código visible único (ej. `TKT-2026-0001`). |
| **FK** | Solicitante | `id_usuario_solicitante` | INT | - | NO | Usuario que reporta (`usuarios.id_usuario`). |
| - | Tipo de Solicitud | `tipo_solicitud` | ENUM | 15 | NO | `Incidente`, `Servicio`, `Informacion`, `Acceso`, `Cambio`. |
| - | Tipo de Cambio | `tipo_cambio` | ENUM | 15 | NO | `N/A`, `Estandar`, `Normal`, `Emergencia`. |
| **IDX** | Prioridad | `prioridad` | ENUM | 10 | NO | `Baja`, `Media`, `Alta`, `Critica`. |
| - | Área de Origen | `area_origen` | VARCHAR | 60 | NO | Área solicitante (Ventas, Almacén, Taller, Gerencia, TI). |
| - | Título | `titulo` | VARCHAR | 160 | NO | Resumen corto del incidente o solicitud. |
| - | Descripción | `descripcion` | TEXT | - | NO | Detalle funcional o técnico completo. |
| - | Impacto / Riesgo | `impacto_riesgo` | VARCHAR | 255 | SÍ | Evaluación de impacto operativo (Cambios/Accesos). |
| - | Plan de Pruebas | `plan_pruebas` | VARCHAR | 255 | SÍ | Validaciones previas para Control de Cambios. |
| - | Plan de Rollback | `plan_rollback` | VARCHAR | 255 | SÍ | Plan de reversión en caso de falla del cambio. |
| **IDX** | Estado | `estado` | ENUM | 15 | NO | `Solicitado`, `En evaluacion`, `Aprobado`, `En atencion`, `Cerrado`, `Rechazado`. |
| **FK** | Aprobador | `aprobado_por` | INT | - | SÍ | Usuario responsable que aprobó Acceso o Cambio. |
| - | Técnico TI Asignado | `tecnico_ti_asignado` | VARCHAR | 120 | SÍ | Especialista TI a cargo de la atención. |
| - | Resolución / Evidencia | `resolucion_evidencia` | TEXT | - | SÍ | Detalle de cierre y evidencia técnica. |
| - | SLA (Horas) | `sla_horas` | INT | - | NO | Tiempo máximo pactado según prioridad (`2`, `4`, `24`, `48`). |
| - | Fecha de Creación | `fecha_creacion` | DATETIME | - | NO | Marca de tiempo de recepción del ticket. |
| - | Límite SLA | `fecha_limite_sla` | DATETIME | - | NO | Fecha máxima de resolución antes de vencimiento SLA. |
| - | Fecha de Cierre | `fecha_cierre` | DATETIME | - | SÍ | Marca de tiempo de finalización o rechazo. |
| **IDX** | Clave Jira | `jira_issue_key` | VARCHAR | 30 | SÍ | Identificador del ticket en Jira Cloud (ej. `TSIE-14`). |
| - | URL Jira | `jira_url` | VARCHAR | 255 | SÍ | Enlace directo al issue en Jira Cloud. |
| - | Sincronizado Jira | `jira_sincronizado` | TINYINT | 1 | NO | Indica si el ticket ya fue creado en Jira (`1` o `0`). |
| - | Error Jira | `jira_ultimo_error` | VARCHAR | 255 | SÍ | Último mensaje de diagnóstico si Jira estuvo inaccesible. |

---

### 8. Entidad: `ticket_historial`
Bitácora cronológica de transiciones de estado y comentarios por cada ticket de TI.

| Key | Nombre | Campo | Tipo de Dato | Tamaño | Nulo | Descripción |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PK** | Identificador de Evento | `id_evento` | INT | - | NO | Clave primaria autoincremental del historial. |
| **FK** | Ticket Asociado | `id_ticket` | INT | - | NO | Referencia a `tickets_ti(id_ticket)`. |
| **FK** | Actor Responsable | `id_usuario` | INT | - | SÍ | Usuario que ejecutó la acción (`usuarios.id_usuario`). |
| - | Estado Anterior | `estado_anterior` | VARCHAR | 30 | SÍ | Etapa previa del ticket (NULL al crearse). |
| - | Estado Nuevo | `estado_nuevo` | VARCHAR | 30 | NO | Etapa a la que transitó el ticket. |
| - | Comentario | `comentario` | TEXT | - | NO | Motivo, aprobación o evidencia técnica registrada. |
| - | Fecha y Hora | `fecha_hora` | DATETIME | - | NO | Marca temporal exacta del evento. |
