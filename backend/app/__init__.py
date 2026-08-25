"""
Condo Services 360 - Application Factory
"""

import os
from logging.config import dictConfig

from flask import Flask, render_template, send_from_directory
from dotenv import load_dotenv

from app.extensions import db, migrate, login_manager, mail, csrf, cors

load_dotenv()

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)


def create_app(config_object="app.config.Config"):
    """Application factory pattern"""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="../../frontend/static",
        static_url_path="/static",
    )

    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    frontend_dir = os.path.join(project_root, "frontend")

    # Configuracion
    app.config.from_object(config_object)

    # Guardia de produccion: exigir SECRET_KEY real
    if os.getenv("FLASK_ENV") == "production":
        secreto = app.config.get("SECRET_KEY", "")
        if not secreto or "dev-secret" in secreto or "change-in-production" in secreto:
            raise RuntimeError(
                "SECRET_KEY segura obligatoria en produccion "
                "(define la variable de entorno SECRET_KEY)"
            )
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["REMEMBER_COOKIE_SECURE"] = True

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # CORS: por defecto solo mismo origen. Solo se habilita /api/* para los
    # origenes declarados en CORS_ORIGINS (separados por coma).
    origenes = [
        o.strip()
        for o in (app.config.get("CORS_ORIGINS") or "").split(",")
        if o.strip()
    ]
    if origenes:
        cors.init_app(app, resources={r"/api/*": {"origins": origenes}})
    else:
        cors.init_app(app, resources={})

    # Configurar login
    login_manager.login_view = "admin.login"
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"

    # Registrar blueprints
    # Se importa desde .routes porque el patron del proyecto redefine el
    # blueprint dentro del modulo de rutas (el que tiene los endpoints).
    from app.blueprints.public.routes import public_bp
    from app.blueprints.admin.routes import admin_bp
    from app.blueprints.api.routes import api_bp

    app.register_blueprint(public_bp, url_prefix="/")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    # PWA: manifest y service worker se sirven desde la raiz de frontend/
    @app.route("/manifest.json")
    def pwa_manifest():
        return send_from_directory(
            frontend_dir, "manifest.json", mimetype="application/manifest+json"
        )

    @app.route("/sw.js")
    def pwa_service_worker():
        return send_from_directory(
            frontend_dir, "sw.js", mimetype="application/javascript"
        )

    @app.route("/offline.html")
    def pwa_offline():
        return send_from_directory(frontend_dir, "offline.html")

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(frontend_dir, "favicon.ico", mimetype="image/x-icon")

    @app.route("/health")
    def health():
        """Healthcheck para monitoreo: sin informacion sensible."""
        try:
            db.session.execute(db.text("SELECT 1"))
            estado_db = "ok"
        except Exception:
            estado_db = "error"
        codigo = 200 if estado_db == "ok" else 503
        return {
            "status": "ok" if codigo == 200 else "degraded",
            "database": estado_db,
        }, codigo

    # Filtros de Jinja2
    from app.utils.helpers import format_currency, format_date

    app.jinja_env.filters["format_currency"] = format_currency
    app.jinja_env.filters["format_date"] = format_date

    # Context processors
    @app.context_processor
    def inject_globals():
        try:
            from app.models.service import Service

            all_services = (
                Service.query.filter_by(is_active=True).order_by(Service.order).all()
            )
        except Exception:
            all_services = []
        return {
            "all_services": all_services,
            "app_name": app.config.get("PWA_NAME", "Condo Services 360"),
            "year": 2026,
            # Version de assets: al subirla, las URLs cambian y el navegador
            # descarga el CSS/JS fresco sin depender de la cache
            "asset_v": os.getenv("ASSET_VERSION", "32"),
        }

    # Cabeceras de seguridad en cada respuesta
    POLITICA_CSP = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )

    @app.after_request
    def aplicar_cabeceras_seguridad(respuesta):
        respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
        respuesta.headers.setdefault("X-Frame-Options", "DENY")
        respuesta.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        respuesta.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        respuesta.headers.setdefault("Content-Security-Policy", POLITICA_CSP)
        return respuesta

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app


# User loader para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User

    return User.query.get(int(user_id))
