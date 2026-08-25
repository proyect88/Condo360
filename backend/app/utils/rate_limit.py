"""
Limitador de intentos para proteger el login contra fuerza bruta.

Backend:
- Si REDIS_URL esta definida y Redis responde, el contador vive en Redis
  (compartido entre todos los workers de Gunicorn).
- En caso contrario se usa un contador en memoria (solo valido para un
  proceso unico) con degradacion automatica si Redis deja de responder.

API: segundos_de_bloqueo(clave), registrar_fallo(clave), resetear(clave).
"""

import logging
import os
import threading
import time

logger = logging.getLogger(__name__)

MAX_INTENTOS = 5
VENTANA_SEGUNDOS = 15 * 60  # 15 minutos de conteo
BLOQUEO_SEGUNDOS = 15 * 60  # 15 minutos de bloqueo

# ---------- Backend en memoria (fallback / proceso unico) ----------

_intentos = {}
_lock = threading.Lock()


def _limpiar_viejos(ahora):
    """Elimina registros vencidos para que el diccionario no crezca."""
    for clave in list(_intentos.keys()):
        datos = _intentos[clave]
        datos["marcas"] = [t for t in datos["marcas"] if ahora - t < VENTANA_SEGUNDOS]
        if not datos["marcas"] and datos.get("bloqueado_hasta", 0) < ahora:
            del _intentos[clave]


def _mem_segundos(clave):
    ahora = time.time()
    with _lock:
        _limpiar_viejos(ahora)
        datos = _intentos.get(clave)
        if not datos:
            return 0
        hasta = datos.get("bloqueado_hasta", 0)
        return int(hasta - ahora) + 1 if hasta > ahora else 0


def _mem_fallo(clave):
    ahora = time.time()
    with _lock:
        _limpiar_viejos(ahora)
        datos = _intentos.setdefault(clave, {"marcas": [], "bloqueado_hasta": 0})
        datos["marcas"].append(ahora)
        if len(datos["marcas"]) >= MAX_INTENTOS:
            datos["bloqueado_hasta"] = ahora + BLOQUEO_SEGUNDOS
            datos["marcas"] = []


def _mem_resetear(clave):
    with _lock:
        _intentos.pop(clave, None)


# ---------- Backend Redis (multi-worker) ----------

_redis = None
_redis_intentado = False


def _obtener_redis():
    global _redis, _redis_intentado
    url = os.getenv("REDIS_URL", "")
    if not url:
        return None
    if not _redis_intentado:
        _redis_intentado = True
        try:
            import redis

            _redis = redis.Redis.from_url(
                url, socket_connect_timeout=1, decode_responses=True
            )
            _redis.ping()
            logger.info("Rate limit usando Redis (%s)", url.split("@")[-1])
        except Exception as e:
            logger.warning("Redis no disponible (%s), rate limit en memoria", e)
            _redis = None
    return _redis


def _redis_clave(clave):
    # Prefijo de aplicacion para evitar colisiones en una Redis compartida
    return f"condo360:rl:{clave}"


# ---------- API publica ----------


def segundos_de_bloqueo(clave):
    """Segundos restantes de bloqueo para la clave; 0 si no esta bloqueada."""
    r = _obtener_redis()
    if r is not None:
        try:
            restante = r.ttl(_redis_clave(clave) + ":lock")
            return max(1, restante) if restante and restante > 0 else 0
        except Exception:
            pass  # degradar a memoria
    return _mem_segundos(clave)


def registrar_fallo(clave):
    """Registra un intento fallido y activa el bloqueo al superar el maximo."""
    r = _obtener_redis()
    nombre = _redis_clave(clave)
    if r is not None:
        try:
            total = r.incr(nombre)
            if total == 1:
                r.expire(nombre, VENTANA_SEGUNDOS)
            if total >= MAX_INTENTOS:
                r.expire(nombre, BLOQUEO_SEGUNDOS)
                # Marca explicita de bloqueo para distinguirla del conteo
                r.set(nombre + ":lock", "1", ex=BLOQUEO_SEGUNDOS)
            return
        except Exception:
            pass  # degradar a memoria
    _mem_fallo(clave)


def resetear(clave):
    """Limpia el historial de la clave tras un login exitoso."""
    r = _obtener_redis()
    if r is not None:
        try:
            r.delete(_redis_clave(clave), _redis_clave(clave) + ":lock")
        except Exception:
            pass
    _mem_resetear(clave)
