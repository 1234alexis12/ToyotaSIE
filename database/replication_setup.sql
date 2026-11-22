-- Configuracion de Replicacion Asincrona Master-Slave en MySQL 8.0
-- Seccion 3.1.8 del Informe: Gestion de Replicacion de Base de Datos
-- Objetivo: Separar transacciones de escritura (Ventas/Taller) de consultas analiticas del Dashboard

-- =========================================================================
-- PARTE 1: CONFIGURACION EN EL NODO MAESTRO (MASTER - ESCRITURA TRANSACCIONAL)
-- =========================================================================

-- Paso 1.1: Habilitar el log binario en el archivo my.cnf / my.ini del servidor Maestro
-- server-id = 1
-- log_bin = /var/log/mysql/mysql-bin.log
-- binlog_do_db = toyota_db
-- binlog_format = ROW

-- Paso 1.2: Creacion del usuario dedicado para replicacion con privilegios minimos
CREATE USER IF NOT EXISTS 'repl_toyota'@'%' IDENTIFIED BY 'ReplicaPass2026!';

-- Paso 1.3: Asignacion exclusiva del privilegio REPLICATION SLAVE
GRANT REPLICATION SLAVE ON *.* TO 'repl_toyota'@'%';
FLUSH PRIVILEGES;

-- Paso 1.4: Consulta de la posicion actual del log binario para sincronizacion
SHOW MASTER STATUS;
-- Nota: Tomar nota de los valores retornados (File y Position) para configurar el esclavo.


-- =========================================================================
-- PARTE 2: CONFIGURACION EN EL NODO ESCLAVO (SLAVE / READ REPLICA - DASHBOARD)
-- =========================================================================

-- Paso 2.1: Asignar identificador unico en my.cnf / my.ini del servidor Esclavo
-- server-id = 2
-- relay_log = /var/log/mysql/mysql-relay-bin.log
-- read_only = 1

-- Paso 2.2: Detener temporalmente los hilos de replicacion para parametrizar
STOP REPLICA;

-- Paso 2.3: Parametrizar conexion hacia el servidor Maestro (reemplazar IP y coordenadas)
CHANGE REPLICATION SOURCE TO
    SOURCE_HOST = '192.168.1.100',
    SOURCE_PORT = 3306,
    SOURCE_USER = 'repl_toyota',
    SOURCE_PASSWORD = 'ReplicaPass2026!',
    SOURCE_LOG_FILE = 'mysql-bin.000001',
    SOURCE_LOG_POS = 157,
    SOURCE_CONNECT_RETRY = 10;

-- Paso 2.4: Iniciar los hilos de recepcion I/O y ejecucion SQL
START REPLICA;

-- Paso 2.5: Verificacion del estado activo de la replicacion
SHOW REPLICA STATUS\G;
-- Evidencia esperada en el informe:
-- Replica_IO_Running: Yes
-- Replica_SQL_Running: Yes
-- Seconds_Behind_Source: 0
