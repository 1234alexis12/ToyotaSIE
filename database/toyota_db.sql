-- Script de creacion y poblado de la base de datos relacional SIG-Toyota
-- Motor: MySQL 8.0 / InnoDB con cotejamiento UTF-8 Multilingue
DROP DATABASE IF EXISTS toyota_db;
CREATE DATABASE toyota_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE toyota_db;

-- 1. Tabla de usuarios del sistema con control de acceso por roles (RBAC)
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(120) NOT NULL,
    rol ENUM('Gerente', 'Operador', 'TI') NOT NULL DEFAULT 'Operador',
    estado ENUM('Activo', 'Inactivo') NOT NULL DEFAULT 'Activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Tabla de auditoria inmutable para trazabilidad de eventos (Norma ISO/IEC 27001)
CREATE TABLE auditoria (
    id_log INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NULL,
    modulo VARCHAR(40) NOT NULL,
    accion VARCHAR(50) NOT NULL,
    detalle TEXT NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_auditoria_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 3. Tabla de clientes particulares y corporativos (Marketing y Ventas)
CREATE TABLE clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    dni_ruc VARCHAR(20) NOT NULL UNIQUE,
    nombre_razon VARCHAR(150) NOT NULL,
    telefono VARCHAR(30) NULL,
    email VARCHAR(100) NULL,
    tipo_cliente ENUM('Particular', 'Corporativo') NOT NULL DEFAULT 'Particular',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 4. Tabla de inventario unificado de vehiculos y repuestos (Logistica y Almacen)
CREATE TABLE inventario (
    id_item INT AUTO_INCREMENT PRIMARY KEY,
    codigo_vin_sku VARCHAR(60) NOT NULL UNIQUE,
    tipo ENUM('Vehiculo', 'Repuesto') NOT NULL,
    nombre_modelo VARCHAR(150) NOT NULL,
    stock_actual INT NOT NULL DEFAULT 0,
    stock_minimo INT NOT NULL DEFAULT 1,
    precio_usd DECIMAL(10, 2) NOT NULL,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_stock_positivo CHECK (stock_actual >= 0)
) ENGINE=InnoDB;

-- 5. Tabla de cotizaciones y transacciones comerciales de vehiculos (Ventas)
CREATE TABLE ventas (
    id_venta INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_item INT NOT NULL,
    id_usuario INT NOT NULL,
    precio_total DECIMAL(10, 2) NOT NULL,
    estado ENUM('Prospecto', 'Cotizado', 'Vendido') NOT NULL DEFAULT 'Cotizado',
    fecha DATE NOT NULL,
    CONSTRAINT fk_ventas_cliente FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_ventas_item FOREIGN KEY (id_item)
        REFERENCES inventario(id_item) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_ventas_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 6. Tabla de ordenes de trabajo de taller mecanico y posventa (Operaciones)
CREATE TABLE ordenes_taller (
    id_orden INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_item_repuesto INT NULL,
    placa_vin VARCHAR(30) NOT NULL,
    tipo_servicio VARCHAR(100) NOT NULL,
    tecnico VARCHAR(100) NOT NULL,
    costo_usd DECIMAL(10, 2) NOT NULL,
    estado ENUM('Pendiente', 'En proceso', 'Entregado') NOT NULL DEFAULT 'Pendiente',
    fecha_ingreso DATE NOT NULL,
    CONSTRAINT fk_taller_cliente FOREIGN KEY (id_cliente)
        REFERENCES clientes(id_cliente) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_taller_repuesto FOREIGN KEY (id_item_repuesto)
        REFERENCES inventario(id_item) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 7. Tabla de tickets del Service Desk TI y Control de Cambios (ITIL / ISO 20000-1)
CREATE TABLE tickets_ti (
    id_ticket INT AUTO_INCREMENT PRIMARY KEY,
    codigo_ticket VARCHAR(25) NOT NULL UNIQUE,
    id_usuario_solicitante INT NOT NULL,
    tipo_solicitud ENUM('Incidente', 'Servicio', 'Informacion', 'Acceso', 'Cambio') NOT NULL DEFAULT 'Incidente',
    tipo_cambio ENUM('N/A', 'Estandar', 'Normal', 'Emergencia') NOT NULL DEFAULT 'N/A',
    prioridad ENUM('Baja', 'Media', 'Alta', 'Critica') NOT NULL DEFAULT 'Media',
    area_origen VARCHAR(60) NOT NULL DEFAULT 'Operaciones',
    titulo VARCHAR(160) NOT NULL,
    descripcion TEXT NOT NULL,
    impacto_riesgo VARCHAR(255) NULL,
    plan_pruebas VARCHAR(255) NULL,
    plan_rollback VARCHAR(255) NULL,
    estado ENUM('Solicitado', 'En evaluacion', 'Aprobado', 'En atencion', 'Cerrado', 'Rechazado') NOT NULL DEFAULT 'Solicitado',
    aprobado_por INT NULL,
    tecnico_ti_asignado VARCHAR(120) NULL,
    resolucion_evidencia TEXT NULL,
    sla_horas INT NOT NULL DEFAULT 24,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_limite_sla DATETIME NOT NULL,
    fecha_cierre DATETIME NULL,
    jira_issue_key VARCHAR(30) NULL,
    jira_url VARCHAR(255) NULL,
    jira_sincronizado TINYINT(1) NOT NULL DEFAULT 0,
    jira_ultimo_error VARCHAR(255) NULL,
    CONSTRAINT fk_ticket_solicitante FOREIGN KEY (id_usuario_solicitante)
        REFERENCES usuarios(id_usuario) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_ticket_aprobador FOREIGN KEY (aprobado_por)
        REFERENCES usuarios(id_usuario) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 8. Tabla de trazabilidad cronologica por ticket de Service Desk
CREATE TABLE ticket_historial (
    id_evento INT AUTO_INCREMENT PRIMARY KEY,
    id_ticket INT NOT NULL,
    id_usuario INT NULL,
    estado_anterior VARCHAR(30) NULL,
    estado_nuevo VARCHAR(30) NOT NULL,
    comentario TEXT NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_historial_ticket FOREIGN KEY (id_ticket)
        REFERENCES tickets_ti(id_ticket) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_historial_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Indice 1: Optimizacion de busqueda rapida en almacen por VIN o SKU (Tuning BD)
CREATE INDEX idx_inventario_codigo ON inventario(codigo_vin_sku);

-- Indice 2: Optimizacion de busqueda de clientes por documento de identidad
CREATE INDEX idx_clientes_dni ON clientes(dni_ruc);

-- Indice 3: Optimizacion de consultas de ventas por fecha para metricas de gerencia
CREATE INDEX idx_ventas_fecha ON ventas(fecha);

-- Indice 4: Optimizacion de filtrado de ordenes de taller por estado operativo
CREATE INDEX idx_taller_estado ON ordenes_taller(estado);

-- Indices 5-7: Optimizacion de consultas del Service Desk TI y Jira
CREATE INDEX idx_tickets_estado ON tickets_ti(estado);
CREATE INDEX idx_tickets_prioridad ON tickets_ti(prioridad);
CREATE INDEX idx_tickets_jira ON tickets_ti(jira_issue_key);

-- Insercion de usuarios semilla con clave encriptada mediante bcrypt (Password: Toyota2026!)
INSERT INTO usuarios (username, password_hash, nombre_completo, rol, estado) VALUES
('admin_gerente', '$2b$12$MEILq34sUNDmMZV3GHPX/ePZT4.r0tbPlTYaWLuP0VsY8MwFYQaZS', 'Ing. Carlos Mendoza (Gerente)', 'Gerente', 'Activo'),
('operador_taller', '$2b$12$MEILq34sUNDmMZV3GHPX/ePZT4.r0tbPlTYaWLuP0VsY8MwFYQaZS', 'Marcos Quispe (Asesor de Servicio)', 'Operador', 'Activo'),
('soporte_ti', '$2b$12$MEILq34sUNDmMZV3GHPX/ePZT4.r0tbPlTYaWLuP0VsY8MwFYQaZS', 'Ing. Luis Mamani (Soporte TI)', 'TI', 'Activo');

-- Insercion de clientes representativos del concesionario Toyota Arequipa
INSERT INTO clientes (dni_ruc, nombre_razon, telefono, email, tipo_cliente) VALUES
('20601234567', 'Minera Cerro Verde S.A.A.', '958123456', 'logistica@cerroverde.pe', 'Corporativo'),
('45678912', 'Juan Perez Delgado', '959987654', 'jperez@gmail.com', 'Particular'),
('20456789012', 'Transportes Arequipa Express S.A.C.', '954332211', 'flota@arequipaexpress.pe', 'Corporativo');

-- Insercion de existencias iniciales: vehiculos con codigo VIN y repuestos OEM con codigo SKU
INSERT INTO inventario (codigo_vin_sku, tipo, nombre_modelo, stock_actual, stock_minimo, precio_usd) VALUES
('8AJBA3CD4P123456', 'Vehiculo', 'Toyota Hilux 4x4 Doble Cabina SRX', 4, 2, 48500.00),
('93XBA3CD4P789012', 'Vehiculo', 'Toyota Corolla Sedan 1.8 XEI', 2, 2, 24200.00),
('8AJBA3CD4P345678', 'Vehiculo', 'Toyota RAV4 Hibrida 2.5 AWD', 3, 1, 39900.00),
('93XBA3CD4P901234', 'Vehiculo', 'Toyota Yaris Sedan 1.5 GLI', 1, 2, 18900.00),
('SKU-04152-YZZA6', 'Repuesto', 'Filtro de Aceite Original Toyota (Hilux/Fortuner)', 18, 10, 22.50),
('SKU-04465-0K340', 'Repuesto', 'Pastillas de Freno Delanteras OEM Toyota Hilux', 3, 5, 95.00),
('SKU-08880-80845', 'Repuesto', 'Aceite Motor Sintetico Toyota 5W-30 (Galon)', 2, 6, 45.00),
('SKU-17801-0L040', 'Repuesto', 'Filtro de Aire Original Hilux/Prado', 12, 5, 38.00);

-- Insercion de ventas y cotizaciones historicas
INSERT INTO ventas (id_cliente, id_item, id_usuario, precio_total, estado, fecha) VALUES
(1, 1, 1, 48500.00, 'Vendido', '2026-11-18'),
(2, 2, 1, 24200.00, 'Cotizado', '2026-11-20'),
(3, 4, 2, 18900.00, 'Prospecto', '2026-11-21');

-- Insercion de ordenes de taller con consumo de repuestos originales
INSERT INTO ordenes_taller (id_cliente, id_item_repuesto, placa_vin, tipo_servicio, tecnico, costo_usd, estado, fecha_ingreso) VALUES
(1, 5, 'V9A-782', 'Mantenimiento Preventivo (10,000 km)', 'Tec. Manuel Salinas', 120.00, 'Entregado', '2026-11-19'),
(2, NULL, 'V4B-119', 'PDI (Inspeccion Pre-Entrega)', 'Tec. David Paredes', 80.00, 'En proceso', '2026-11-21'),
(3, 6, 'V7C-554', 'Reparacion de Frenos', 'Tec. Manuel Salinas', 210.00, 'Pendiente', '2026-11-21');

-- Insercion de registros iniciales en la bitacora de auditoria (ISO 27001)
INSERT INTO auditoria (id_usuario, modulo, accion, detalle, fecha_hora) VALUES
(1, 'SEGURIDAD', 'LOGIN', 'Inicio de sesion exitoso de Gerente General', '2026-11-21 08:30:15'),
(2, 'VENTAS', 'INSERT', 'Registro de cotizacion #3 para cliente Transportes Arequipa', '2026-11-21 09:15:22'),
(1, 'VENTAS', 'UPDATE_ESTADO', 'Cierre de venta #1 y descuento automatico de stock de Toyota Hilux', '2026-11-21 10:45:04'),
(2, 'TALLER', 'INSERT_ORDEN', 'Apertura de orden de servicio #3 con cargo de pastillas de freno', '2026-11-21 11:20:10');


-- Insercion de tickets iniciales de Service Desk TI y Control de Cambios
INSERT INTO tickets_ti (
    codigo_ticket, id_usuario_solicitante, tipo_solicitud, tipo_cambio, prioridad, area_origen,
    titulo, descripcion, impacto_riesgo, plan_pruebas, plan_rollback, estado, aprobado_por,
    tecnico_ti_asignado, sla_horas, fecha_creacion, fecha_limite_sla, jira_sincronizado, jira_ultimo_error
) VALUES
(
    'TKT-2026-0001', 2, 'Incidente', 'N/A', 'Alta', 'Taller',
    'Error al imprimir orden de taller en impresora de bahia 2',
    'La impresora termica de red en bahia 2 muestra cola atascada al generar OT de mantenimiento.',
    NULL, NULL, NULL, 'En atencion', NULL,
    'Ing. Luis Mamani (Soporte TI)', 4, NOW(), DATE_ADD(NOW(), INTERVAL 4 HOUR), 0, 'Pendiente de credenciales Jira en .env'
),
(
    'TKT-2026-0002', 2, 'Acceso', 'N/A', 'Media', 'Ventas',
    'Solicitud de acceso temporal a reportes ejecutivos de ventas',
    'Requiero permiso de lectura para emitir cierre comercial mensual por ausencia del supervisor.',
    'Acceso de solo lectura sujeto a principio de minimo privilegio.', NULL, NULL, 'Solicitado', NULL,
    NULL, 24, NOW(), DATE_ADD(NOW(), INTERVAL 24 HOUR), 0, 'Pendiente de credenciales Jira en .env'
),
(
    'TKT-2026-0003', 1, 'Cambio', 'Normal', 'Alta', 'Infraestructura TI',
    'Despliegue de replicacion Master-Slave MySQL 8.0 en Docker',
    'Separar transacciones de escritura en nodo Master (3310) y lecturas del Dashboard en Slave (3311).',
    'Posible latencia minima durante arranque inicial de contenedores.',
    'Validar healthcheck /api/health y bloqueo super_read_only en Slave.',
    'Revertir docker-compose.yml al servicio unico db manteniendo volumen toyota_master_data.',
    'Aprobado', 1, 'Ing. Luis Mamani (Soporte TI)', 4, NOW(), DATE_ADD(NOW(), INTERVAL 4 HOUR), 0, 'Pendiente de credenciales Jira en .env'
);

INSERT INTO ticket_historial (id_ticket, id_usuario, estado_anterior, estado_nuevo, comentario, fecha_hora) VALUES
(1, 2, NULL, 'Solicitado', 'Ticket registrado desde Service Desk.', NOW()),
(1, 3, 'Solicitado', 'En atencion', 'Revisando driver de impresion en red local.', NOW()),
(2, 2, NULL, 'Solicitado', 'Solicitud de acceso pendiente de aprobacion gerencial.', NOW()),
(3, 1, NULL, 'Solicitado', 'Control de cambio Normal registrado.', NOW()),
(3, 1, 'Solicitado', 'Aprobado', 'Cambio aprobado con plan de pruebas y rollback validado.', NOW());

INSERT INTO auditoria (id_usuario, modulo, accion, detalle, fecha_hora) VALUES
(3, 'TI_SERVICEDESK', 'UPDATE_TICKET', 'TKT-2026-0001 asignado a Soporte TI para atencion prioritaria (SLA 4h)', NOW());
