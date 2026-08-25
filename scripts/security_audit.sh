#!/usr/bin/env bash
# ============================================
# Auditoria de dependencias contra la base de vulnerabilidades de PyPI.
#
# Uso manual:
#   ./scripts/security_audit.sh
#
# Cron semanal (lunes 08:00):
#   0 8 * * 1 /ruta/al/proyecto/scripts/security_audit.sh >> /var/log/condo_audit.log 2>&1
# ============================================
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v pip-audit >/dev/null 2>&1; then
    echo "pip-audit no esta instalado. Instalando..."
    pip install pip-audit
fi

echo "== Auditoria de requirements.txt =="
pip-audit -r requirements.txt --strict
echo "== Auditoria del entorno virtual activo =="
pip-audit --skip-editable
echo "Auditoria completada sin vulnerabilidades conocidas."
