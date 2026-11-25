-- Usuario dedicado de replicacion en el nodo Maestro (Seccion 3.1.8)
-- Se desactiva el binlog de sesion para que el usuario tecnico sea local del Master
SET @@SESSION.SQL_LOG_BIN = 0;
CREATE USER IF NOT EXISTS 'repl_toyota'@'%' IDENTIFIED BY 'ReplicaPass2026!';
GRANT REPLICATION SLAVE ON *.* TO 'repl_toyota'@'%';
FLUSH PRIVILEGES;
