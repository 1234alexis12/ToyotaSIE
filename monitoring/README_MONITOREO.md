# Guía de Monitoreo, Caché Redis, Capacidad VM y Pruebas de Carga — SIG-Toyota

## 1. Accesos y Puertos (compatibles sin chocar con otros proyectos)
* **Frontend SIG-Toyota:** `http://localhost:8080`
* **Grafana (Dashboards interactivos):** `http://localhost:3001` *(Usuario: `admin` / Clave: `admin`, o vista directa en modo lectura)*
* **Prometheus (Métricas y Targets):** `http://localhost:9091`
* **Redis (Caché en memoria):** `127.0.0.1:6380`
* **Métricas crudas de Flask:** `http://localhost:5000/metrics`
* **Exporters internos (solo red Docker):** `node-exporter:9100`, `cadvisor:8080`, `mysql-master-exporter:9104`, `mysql-slave-exporter:9104`, `redis-exporter:9121`

## 2. Qué mide el Dashboard de Grafana
1. **Resumen Ejecutivo & SLA:** Throughput API (`req/s`), Latencia `p95` (`ms`), Disponibilidad API (`%`), Cache Hit Rate Redis (`%`), CPU VM Usado (`%`) y RAM VM Usada (`%`).
2. **Capacidad de la Máquina Virtual (`node-exporter`):** Núcleos/vCPUs, RAM Total vs Usada/Disponible, Uso de Disco (`%`), Load Average (`1m`), CPU detallado (`Total / User / System / I/O Wait`), Tráfico de Red RX/TX, Lag de Replicación Slave y Estado del Nodo Slave (`3311`).
3. **Consumo por Contenedor (`cAdvisor`):** CPU (`%`), Memoria RAM (`Working Set`) y Tráfico de Red por cada servicio (`toyota_backend`, `toyota_mysql_master`, `toyota_mysql_slave`, `toyota_redis`, `toyota_frontend`, etc.).
4. **Rendimiento API, MySQL Master-Slave y Redis:** Latencia `p95` vs promedio, Throughput por endpoint y código HTTP, SQL/s Master vs Slave, Enrutamiento Backend, Conexiones/Hilos MySQL, Hits vs Misses y memoria RAM de Redis.

## 3. Cómo correr la prueba de carga con Apache JMeter
1. Abrir **Apache JMeter** en tu PC (`jmeter.bat` en Windows o `jmeter` en Linux).
2. Ir a **File → Open** y seleccionar `monitoring/jmeter/sig_toyota_prueba_carga.jmx`.
3. Ejecutar el grupo **1. Prueba de Carga Normal (50 Usuarios Concurrentes)** (botón verde Play ▶). *(En la MV nueva, cambia `localhost` por la IP de la MV si ejecutas JMeter desde otra máquina).*
4. Para **Prueba de Estrés**, clic derecho en el grupo **2. Prueba de Estres (200 Usuarios Concurrentes)** → **Enable** y ejecutar.
5. Abrir `http://<IP_MV>:3001` en paralelo para observar CPU, RAM, Red, Throughput, Cache Hit Rate y replicación MySQL en tiempo real.
