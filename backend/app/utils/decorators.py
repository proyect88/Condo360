from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """Decorador para requerir rol de administrador"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("No tienes permisos para acceder a esta página", "danger")
            return redirect(url_for("admin.dashboard"))
        return f(*args, **kwargs)

    return decorated_function


def staff_required(f):
    """Decorador para requerir rol de staff o admin"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_staff:
            flash("No tienes permisos para acceder a esta página", "danger")
            return redirect(url_for("admin.dashboard"))
        return f(*args, **kwargs)

    return decorated_function


def rate_limit(limit_per_hour=100):
    """Decorador para limitar tasa de peticiones"""
    from flask import request, jsonify
    import time
    from collections import defaultdict

    requests = defaultdict(list)

    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            # Identificador único para el usuario
            user_id = request.remote_addr
            if current_user.is_authenticated:
                user_id = current_user.id

            now = time.time()
            hour_ago = now - 3600

            # Limpiar requests viejos
            requests[user_id] = [t for t in requests[user_id] if t > hour_ago]

            if len(requests[user_id]) >= limit_per_hour:
                return jsonify({"error": "Límite de peticiones excedido"}), 429

            requests[user_id].append(now)
            return func(*args, **kwargs)

        return decorated_function

    return decorator
