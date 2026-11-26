from prometheus_client import Counter, Histogram


# Metricas de rendimiento, cache y enrutamiento Master-Slave para Prometheus/Grafana
HTTP_REQUESTS_TOTAL = Counter(
    'toyota_http_requests_total',
    'Total de peticiones HTTP atendidas por la API SIG-Toyota',
    ['method', 'endpoint', 'status'],
)

HTTP_REQUEST_LATENCY = Histogram(
    'toyota_http_request_duration_seconds',
    'Tiempo de respuesta de la API en segundos',
    ['method', 'endpoint'],
    buckets=(0.001, 0.003, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

CACHE_HITS_TOTAL = Counter(
    'toyota_cache_hits_total',
    'Total de aciertos en cache Redis',
    ['clave'],
)

CACHE_MISSES_TOTAL = Counter(
    'toyota_cache_misses_total',
    'Total de fallos en cache Redis',
    ['clave'],
)

DB_QUERIES_TOTAL = Counter(
    'toyota_db_queries_total',
    'Conexiones/consultas dirigidas a cada nodo MySQL',
    ['nodo'],
)
