import json
import os
import redis
from servicios.MetricsService import CACHE_HITS_TOTAL, CACHE_MISSES_TOTAL


class CacheService:
    """Servicio de cache distribuido en Redis con degradacion segura si no esta activo."""

    _cliente = None
    _host_cache = None

    @classmethod
    def _obtener_config(cls):
        host = os.getenv('REDIS_HOST', '').strip()
        port = int(os.getenv('REDIS_PORT', 6379))
        return host, port

    @classmethod
    def _obtener_cliente(cls):
        host, port = cls._obtener_config()
        if not host:
            return None

        if cls._cliente is None or cls._host_cache != (host, port):
            cls._host_cache = (host, port)
            cls._cliente = redis.Redis(
                host=host,
                port=port,
                db=0,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
            )
        return cls._cliente

    @classmethod
    def obtener_json(cls, clave):
        """Lee un objeto JSON desde Redis; retorna None si hay miss o Redis no responde."""
        cliente = cls._obtener_cliente()
        if not cliente:
            return None
        try:
            raw = cliente.get(f"toyota:{clave}")
            if raw is not None:
                CACHE_HITS_TOTAL.labels(clave=clave).inc()
                return json.loads(raw)
            CACHE_MISSES_TOTAL.labels(clave=clave).inc()
        except Exception:
            return None
        return None

    @classmethod
    def guardar_json(cls, clave, valor, ttl_segundos=30):
        """Almacena un objeto JSON en Redis con tiempo de expiracion TTL."""
        cliente = cls._obtener_cliente()
        if not cliente:
            return False
        try:
            cliente.setex(f"toyota:{clave}", ttl_segundos, json.dumps(valor))
            return True
        except Exception:
            return False

    @classmethod
    def invalidar(cls, *claves):
        """Elimina claves en cache tras una escritura para evitar datos obsoletos."""
        cliente = cls._obtener_cliente()
        if not cliente or not claves:
            return False
        try:
            keys = [f"toyota:{c}" for c in claves]
            cliente.delete(*keys)
            return True
        except Exception:
            return False

    @classmethod
    def estado(cls):
        """Diagnostica conectividad actual con Redis."""
        host, port = cls._obtener_config()
        if not host:
            return {'configurado': False, 'conectado': False, 'host': None, 'puerto': None}
        cliente = cls._obtener_cliente()
        try:
            if cliente and cliente.ping():
                return {'configurado': True, 'conectado': True, 'host': host, 'puerto': port}
        except Exception:
            pass
        return {'configurado': True, 'conectado': False, 'host': host, 'puerto': port}
