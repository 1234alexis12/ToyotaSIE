# Guía Detallada de Implementación — Monitoreo, Capacidad VM, Redis, Prometheus, Grafana y JMeter (SIG-Toyota)

Este documento explica a detalle la arquitectura de observabilidad, aceleración con caché **Redis**, monitoreo de infraestructura de la **Máquina Virtual (VM) y contenedores**, visualización interactiva en **Grafana**, recolección de métricas con **Prometheus** y pruebas de carga con **Apache JMeter** implementada para **SIG-Toyota**.

---

## 1. Arquitectura de Observabilidad (Cómo Fluyen los Datos)

Prometheus utiliza un modelo **Pull (extracción por HTTP cada `5s`)**: no espera a que las aplicaciones le envíen archivos, sino que consulta periódicamente los endpoints `/metrics` de cada servicio dentro de la red privada de Docker y almacena las series temporales para que **Grafana** las consulte en vivo mediante **PromQL**.

```text
  [ Usuarios / JMeter (Carga) ]
               │  HTTP :8080
               ▼
  [ Frontend Nginx (:8080 -> :80) ] ──(/api/)──▶ [ Backend Flask (:5000) ] ──▶ /metrics (HTTP)
                                                       │          │
                                    Lecturas KPI (30s) │          ├── Escrituras ─▶ MySQL Master (:3310)
                                                       ▼          └── Lecturas   ─▶ MySQL Slave  (:3311)
                                                 [ Redis (:6380) ]
                                                       ▲
  ── Recolección Prometheus (:9091, cada 5s) ──────────┴───────────────────────────
     ├── job: sig-toyota-backend  -> backend:5000/metrics
     ├── job: mysql-master        -> mysql-master-exporter:9104/metrics
     ├── job: mysql-slave         -> mysql-slave-exporter:9104/metrics
     ├── job: redis-cache         -> redis-exporter:9121/metrics
     ├── job: vm-host             -> node-exporter:9100/metrics     (CPU, RAM, Disco, Load, Red de la VM)
     └── job: docker-containers   -> cadvisor:8080/metrics          (CPU, RAM, Red por contenedor)
                                                       │
                                                       ▼
                                            [ Grafana (:3001) ]
                                     24 paneles en tiempo real (refresh 5s)
```

> **Importante para despliegue en MV nueva:** Ningún valor en Grafana está hardcodeado. `node-exporter` lee directamente `/proc`, `/sys` y `/` del sistema operativo anfitrión donde corre Docker, y `cAdvisor` lee los cgroups reales de cada contenedor `toyota_*`. Al levantar el proyecto en otra máquina o MV con distintas características (por ejemplo 4 vCPUs y 8 GB de RAM), Grafana mostrará automáticamente la capacidad y consumo reales de esa MV.

---

## 2. De Dónde Saca los Datos Cada Componente ("Cómo Escucha")

| Origen / Exporter | Qué lee internamente | Qué datos entrega a Prometheus |
| :--- | :--- | :--- |
| **Backend Flask (`/metrics`)** (`MetricsService.py` + `app.py`) | Hooks `@app.before_request` / `@app.after_request`, `CacheService` y `MySQLConexion`. | `toyota_http_requests_total` (tráfico por endpoint y status HTTP `200`/`4xx`/`5xx`), `toyota_http_request_duration_seconds` (histograma de latencia para calcular `p95` y promedio), `toyota_cache_hits_total`, `toyota_cache_misses_total` y `toyota_db_queries_total` (`master` vs `slave`). |
| **MySQL Exporters** (`prom/mysqld-exporter:v0.15.1`) | Consultan `SHOW GLOBAL STATUS` y `SHOW REPLICA STATUS` contra `db-master:3306` y `db-slave:3306` usando credenciales de `master.my.cnf` / `slave.my.cnf`. | Consultas SQL por segundo (`mysql_global_status_queries`), conexiones abiertas (`threads_connected`), hilos ejecutándose (`threads_running`), salud de nodo (`up{job="mysql-slave"}`) y lag de replicación (`mysql_slave_status_seconds_behind_master`). |
| **Redis Exporter** (`oliver006/redis_exporter:latest`) | Ejecuta comandos `INFO` sobre `redis://redis:6379`. | Memoria RAM utilizada por Redis (`redis_memory_used_bytes`), comandos procesados y clientes conectados. |
| **Node Exporter** (`prom/node-exporter:v1.8.1`) | Lee los directorios montados en solo lectura de la MV (`/proc` -> `/host/proc`, `/sys` -> `/host/sys`, `/` -> `/rootfs`). | CPU total/usuario/sistema/iowait (`node_cpu_seconds_total`), cantidad de núcleos/vCPUs, RAM total y disponible (`node_memory_MemTotal_bytes`, `MemAvailable_bytes`), uso de disco (`node_filesystem_*`), carga (`node_load1`) y red RX/TX (`node_network_*`). |
| **cAdvisor** (`ghcr.io/google/cadvisor:v0.61.1`) | Inspecciona `/var/run/docker.sock`, `/sys` y `/var/lib/docker` en modo privilegiado para medir recursos por contenedor. | CPU por servicio (`container_cpu_usage_seconds_total{name=~"toyota_.*"}`), RAM real (`container_memory_working_set_bytes`) y tráfico de red por contenedor (`container_network_receive/transmit_bytes_total`). |

---

## 3. Archivos Creados y Modificados

### A. Backend Python / Caché Redis / Métricas
* **`backend/requirements.txt`**: Se agregaron `redis>=5.0.0` y `prometheus-client>=0.20.0`.
* **`backend/servicios/MetricsService.py`** *(nuevo)*: Define los contadores e histograma de Prometheus (`HTTP_REQUESTS_TOTAL`, `HTTP_REQUEST_LATENCY`, `CACHE_HITS_TOTAL`, `CACHE_MISSES_TOTAL`, `DB_QUERIES_TOTAL`).
* **`backend/servicios/CacheService.py`** *(nuevo)*: Cliente Redis con prefijo `toyota:`, TTL configurable (`30s`), métodos `obtener_json`, `guardar_json`, `invalidar` y `estado()`. Si `REDIS_HOST` no está configurado o Redis falla, degrada de forma segura sin interrumpir las peticiones hacia MySQL.
* **`backend/config/MySQLConexion.py`**: Instrumenta `obtener_conexion()` (`nodo='master'`) y `obtener_conexion_lectura()` (`nodo='slave'`) incrementando `DB_QUERIES_TOTAL`.
* **`backend/app.py`**:
  * Expone `GET /metrics` (`generate_latest()`).
  * Mide duración y código HTTP de todas las rutas API.
  * Aplica `_respuesta_cacheada(..., ttl=30)` (cabecera `X-Cache: HIT | MISS`) en `/api/dashboard`, `/api/inventario`, `/api/ventas`, `/api/taller` y `/api/tickets/metricas`.
  * Invalida claves de caché automáticamente al ejecutar escrituras (`POST`/`PUT`).
  * Incluye el diagnóstico de Redis en `GET /api/health`.
* **`backend/tests/test_api.py`**: Se agregaron `test_endpoint_metricas_prometheus_y_health` y `test_cache_redis_hit_miss_e_invalidacion` (11 pruebas pasando).

### B. Frontend React
* **`frontend/src/AreaTI.jsx`**: Se añadió el botón **"📈 Abrir Grafana (Rendimiento)"** en la cabecera de la consola de Área de TI, apuntando al puerto `3001` del host actual (`http://${window.location.hostname}:3001`).

### C. Orquestación Docker (`docker-compose.yml`) y Configuración de Monitoreo (`monitoring/`)
* **`docker-compose.yml`**: Se incorporaron 6 servicios adicionales con puertos elegidos para convivir con otros proyectos sin conflictos:
  * `redis` (`redis:7-alpine`) → puerto host `6380:6379`.
  * `mysql-master-exporter` y `mysql-slave-exporter` (`prom/mysqld-exporter:v0.15.1`) → red interna Docker (`9104`).
  * `redis-exporter` (`oliver006/redis_exporter:latest`) → red interna Docker (`9121`).
  * `node-exporter` (`prom/node-exporter:v1.8.1`) → red interna Docker (`9100`), montando `/proc`, `/sys` y `/` en solo lectura.
  * `cadvisor` (`ghcr.io/google/cadvisor:v0.61.1`) → red interna Docker (`8080`), montando Docker socket/cgroups.
  * `prometheus` (`prom/prometheus:v2.51.0`) → puerto host `9091:9090` + volumen persistente `toyota_prometheus_data`.
  * `grafana` (`grafana/grafana:10.4.1`) → puerto host `3001:3000` + volumen persistente `toyota_grafana_data` + provisioning automático (`admin`/`admin` y lector anónimo habilitado).
  * `backend` recibe `REDIS_HOST=redis` y `REDIS_PORT=6379` y espera el healthcheck de `redis`.
* **`monitoring/mysql/master.my.cnf` y `monitoring/mysql/slave.my.cnf`** *(nuevos)*: Archivos `[client]` para autenticación de los exporters hacia MySQL 8.0.
* **`monitoring/prometheus/prometheus.yml`** *(nuevo)*: Configura `scrape_interval: 5s` y los 7 jobs (`prometheus`, `sig-toyota-backend`, `mysql-master`, `mysql-slave`, `redis-cache`, `vm-host`, `docker-containers`).
* **`monitoring/grafana/provisioning/datasources/prometheus.yml`** *(nuevo)*: Conecta automáticamente Grafana con `http://prometheus:9090` (`uid: prometheus`).
* **`monitoring/grafana/provisioning/dashboards/provider.yml`** *(nuevo)*: Carga automática de dashboards desde JSON al arrancar Grafana.
* **`monitoring/grafana/provisioning/dashboards/sig_toyota_observabilidad.json`** *(nuevo)*: Dashboard con **24 paneles** divididos en 4 secciones:
  1. **Resumen Ejecutivo — Rendimiento, SLA y Recursos de la VM:** Throughput (`req/s`), Latencia `p95`, Disponibilidad API (`%`), Cache Hit Rate Redis (`%`), CPU VM Usado (`%`), RAM VM Usada (`%`).
  2. **Capacidad de la Máquina Virtual:** vCPUs, RAM Total, Disco Usado (`%`), Load Average (`1m`), Lag de Replicación Slave, Estado Nodo Slave (`3311`), CPU desglosado (`Total / User / System / I/O Wait`) y RAM (`Usada vs Disponible`).
  3. **Consumo por Contenedor SIG-Toyota (`cAdvisor`):** CPU (`%`), Memoria RAM (`Working Set`) y Tráfico de Red (`RX/TX`) filtrado a `name=~"toyota_.*"`.
  4. **Rendimiento API Flask, MySQL Master-Slave y Caché Redis:** Latencia `p95` vs promedio, Throughput por endpoint y código HTTP, SQL/s y Enrutamiento Master/Slave, Hits vs Misses Redis, Conexiones/Hilos MySQL y Memoria RAM usada en Redis.
* **`monitoring/jmeter/sig_toyota_prueba_carga.jmx`** *(nuevo)*: Plan de pruebas Apache JMeter con escenario normal (**50 usuarios concurrentes**) y escenario de estrés (**200 usuarios concurrentes**) contra `/api/dashboard`, `/api/inventario`, `/api/tickets/metricas` y `/api/ventas`.
* **`monitoring/README_MONITOREO.md`** *(nuevo)*: Instructivo rápido de puertos, métricas y ejecución de JMeter.

---

## 4. Cómo Levantar y Probar en la Máquina Virtual (MV)

1. Copiar/clonar el proyecto y crear el archivo `.env` con las credenciales de Jira.
2. Ejecutar en la MV:
   ```bash
   docker compose up -d --build
   ```
3. Verificar estado de los servicios y puertos:
   * **SIG-Toyota Web:** `http://<IP_DE_LA_MV>:8080`
   * **Grafana (Dashboard interactivo):** `http://<IP_DE_LA_MV>:3001` *(Usuario `admin` / Clave `admin`, o acceso directo en modo visor)*
   * **Prometheus (Targets `/targets`):** `http://<IP_DE_LA_MV>:9091`
   * **Salud Backend + Redis + Master/Slave:** `http://<IP_DE_LA_MV>:8080/api/health`
4. Abrir `monitoring/jmeter/sig_toyota_prueba_carga.jmx` en **Apache JMeter**, ajustar la variable `HOST` si se ejecuta desde otra PC apuntando a la IP de la MV, lanzar la prueba y observar en tiempo real en Grafana cómo responden CPU, RAM, Redis (`HIT Rate`) y la réplica MySQL Slave.
