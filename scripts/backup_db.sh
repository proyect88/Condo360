#!/usr/bin/env bash
# ============================================
# Backup diario de la base de datos de Condo Services 360
#
# Soporta:
#   - PostgreSQL (usa DATABASE_URL, ideal en produccion/Docker)
#   - SQLite     (fallback para desarrollo)
#
# Retencion: borra respaldos con mas de RETENCION_DIAS dias (7 por defecto).
#
# Uso manual:
#   ./scripts/backup_db.sh
#
# Cron recomendado (todos los dias 03:00):
#   0 3 * * * /ruta/al/proyecto/scripts/backup_db.sh >> /var/log/condo_backup.log 2>&1
#
# En Docker:
#   docker exec condo_services_web /app/scripts/backup_db.sh
# ============================================
set -euo pipefail

RETENCION_DIAS="${RETENCION_DIAS:-7}"
DESTINO="${DESTINO:-./backups}"
FECHA="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$DESTINO"

if [ -n "${DATABASE_URL:-}" ] && [[ "$DATABASE_URL" == postgres* ]]; then
    # PostgreSQL: pg_dump con el formato comprimido propio
    ARCHIVO="$DESTINO/condo_services_$FECHA.dump"
    pg_dump "$DATABASE_URL" --format=custom --file="$ARCHIVO"
else
    # SQLite: copia consistente con la API de backup de sqlite3
    DB_SQLITE="${DB_SQLITE:-backend/instance/condo_services.db}"
    ARCHIVO="$DESTINO/condo_services_$FECHA.db.gz"
    if [ ! -f "$DB_SQLITE" ]; then
        echo "ERROR: no se encontro la base SQLite en $DB_SQLITE" >&2
        exit 1
    fi
    python3 - "$DB_SQLITE" "$ARCHIVO" <<'PYEOF'
import gzip, sqlite3, sys, shutil

origen, destino = sys.argv[1], sys.argv[2]
con = sqlite3.connect(origen)
with gzip.open(destino, "wb", compresslevel=6) as salida:
    con.backup(salida)  # type: ignore[arg-type]
con.close()
PYEOF
fi

echo "Backup creado: $ARCHIVO ($(du -h "$ARCHIVO" | cut -f1))"

# Retencion: eliminar respaldos antiguos
BORRADOS=$(find "$DESTINO" -name "condo_services_*" -mtime "+$RETENCION_DIAS" -print -delete | wc -l)
echo "Respaldos eliminados por retencion (${RETENCION_DIAS} dias): $BORRADOS"
