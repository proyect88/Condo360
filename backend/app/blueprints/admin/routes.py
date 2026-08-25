from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify,
    current_app,
)
from flask_login import login_required, login_user, logout_user, current_user
from app.models.user import User
from app.models.service import Service
from app.models.service_image import ServiceImage
from app.models.ticket import Ticket
from app.models.testimonial import Testimonial
from app.models.diagnostic import Diagnostic
from app.blueprints.admin.forms import (
    ServiceForm,
    TestimonialForm,
    UserForm,
)

from app import db
from app.utils import rate_limit
from datetime import datetime, timedelta
from urllib.parse import urlparse
import json
import logging
import os
from sqlalchemy import func

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
logger = logging.getLogger(__name__)


def _destino_seguro(destino):
    """Evita redirecciones abiertas: solo rutas internas de la aplicacion."""
    if not destino:
        return False
    parseado = urlparse(destino)
    return (
        destino.startswith("/")
        and not destino.startswith("//")
        and parseado.scheme in ("", "http", "https")
        and parseado.netloc == ""
    )


def _int_form(nombre, defecto=0):
    """Lee un entero del formulario sin lanzar excepciones."""
    valor = request.form.get(nombre, "")
    try:
        return int(valor)
    except (TypeError, ValueError):
        return defecto


# ==================== AUTENTICACIÓN ====================


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = request.form.get("remember") == "on"

        # Proteccion contra fuerza bruta por IP + email
        clave_throttle = f"{request.remote_addr}|{(email or '').strip().lower()}"
        espera = rate_limit.segundos_de_bloqueo(clave_throttle)
        if espera > 0:
            flash(
                "Demasiados intentos fallidos. Espera %d minutos e intenta "
                "nuevamente." % max(1, espera // 60),
                "danger",
            )
            return render_template("admin/login.html"), 429

        user = User.query.filter_by(email=email, is_active=True).first()

        if user and user.check_password(password):
            rate_limit.resetear(clave_throttle)
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash("¡Bienvenido de vuelta!", "success")

            next_page = request.args.get("next")
            if next_page and _destino_seguro(next_page):
                return redirect(next_page)
            return redirect(url_for("admin.dashboard"))
        else:
            rate_limit.registrar_fallo(clave_throttle)
            flash("Credenciales incorrectas o usuario inactivo", "danger")

    return render_template("admin/login.html")


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión", "info")
    return redirect(url_for("admin.login"))


# ==================== DASHBOARD ====================


@admin_bp.route("/")
@login_required
def dashboard():
    """Panel de administración principal"""
    # Estadísticas de tickets
    total_tickets = Ticket.query.count()
    pending_tickets = Ticket.query.filter(
        Ticket.status.in_(["new", "in_progress"])
    ).count()
    resolved_tickets = Ticket.query.filter_by(status="resolved").count()

    # Tickets por urgencia
    critical_tickets = Ticket.query.filter_by(urgency="critical", status="new").count()
    high_tickets = Ticket.query.filter_by(urgency="high", status="new").count()

    # Estadísticas de servicios
    total_services = Service.query.count()
    active_services = Service.query.filter_by(is_active=True).count()

    # Testimonios pendientes
    pending_testimonials = Testimonial.query.filter_by(is_approved=False).count()

    # Diagnósticos pendientes
    pending_diagnostics = Diagnostic.query.filter_by(status="pending").count()

    # Tickets recientes
    recent_tickets = Ticket.query.order_by(db.desc(Ticket.created_at)).limit(10).all()

    # Tickets por día (últimos 30 días)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    tickets_by_day = (
        db.session.query(
            func.date(Ticket.created_at).label("day"),
            func.count(Ticket.id).label("count"),
        )
        .filter(Ticket.created_at >= thirty_days_ago)
        .group_by(func.date(Ticket.created_at))
        .all()
    )

    # Tickets por status
    tickets_by_status = (
        db.session.query(Ticket.status, func.count(Ticket.id))
        .group_by(Ticket.status)
        .all()
    )

    # Servicios más solicitados
    top_services = (
        db.session.query(Service.name, func.count(Ticket.id).label("count"))
        .join(Service, Ticket.service_type == Service.slug)
        .filter(Ticket.status != "cancelled")
        .group_by(Service.name)
        .order_by(func.count(Ticket.id).desc())
        .limit(5)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        total_tickets=total_tickets,
        pending_tickets=pending_tickets,
        resolved_tickets=resolved_tickets,
        critical_tickets=critical_tickets,
        high_tickets=high_tickets,
        total_services=total_services,
        active_services=active_services,
        pending_testimonials=pending_testimonials,
        pending_diagnostics=pending_diagnostics,
        recent_tickets=recent_tickets,
        tickets_by_day=json.dumps(
            [{"day": str(d.day), "count": d.count} for d in tickets_by_day]
        ),
        tickets_by_status=json.dumps(
            [{"status": s[0], "count": s[1]} for s in tickets_by_status]
        ),
        top_services=top_services,
    )


# ==================== GESTIÓN DE SERVICIOS ====================


@admin_bp.route("/servicios")
@login_required
def list_services():
    services = Service.query.order_by(Service.order).all()
    return render_template("admin/services/list.html", services=services)


@admin_bp.route("/servicios/nuevo", methods=["GET", "POST"])
@login_required
def create_service():
    form = ServiceForm()
    if form.validate_on_submit():
        try:
            service = Service(
                name=form.name.data,
                slug=Service.generate_slug(form.name.data),
                description=form.description.data,
                short_description=form.short_description.data,
                icon=form.icon.data,
                category=form.category.data,
                price_from=form.price_from.data,
                features=[
                    f.strip() for f in form.features.data.split(",") if f.strip()
                ],
                is_active=form.is_active.data,
                is_featured=form.is_featured.data,
                order=form.order.data,
            )
            db.session.add(service)
            db.session.commit()
            flash("Servicio creado exitosamente", "success")
            return redirect(url_for("admin.list_services"))
        except Exception as e:
            logger.error(f"Error al crear servicio: {str(e)}")
            flash("Error al crear el servicio", "danger")

    return render_template("admin/services/create.html", form=form)


@admin_bp.route("/servicios/editar/<int:id>", methods=["GET", "POST"])
@login_required
def edit_service(id):
    service = Service.query.get_or_404(id)
    form = ServiceForm(obj=service)

    if form.validate_on_submit():
        try:
            service.name = form.name.data
            service.slug = Service.generate_slug(form.name.data)
            service.description = form.description.data
            service.short_description = form.short_description.data
            service.icon = form.icon.data
            service.category = form.category.data
            service.price_from = form.price_from.data
            service.features = [
                f.strip() for f in form.features.data.split(",") if f.strip()
            ]
            service.is_active = form.is_active.data
            service.is_featured = form.is_featured.data
            service.order = form.order.data
            service.updated_at = datetime.utcnow()

            db.session.commit()
            flash("Servicio actualizado exitosamente", "success")
            return redirect(url_for("admin.list_services"))
        except Exception as e:
            logger.error(f"Error al actualizar servicio: {str(e)}")
            flash("Error al actualizar el servicio", "danger")

    form.features.data = ", ".join(service.features) if service.features else ""
    return render_template("admin/services/edit.html", form=form, service=service)


@admin_bp.route("/servicios/eliminar/<int:id>", methods=["POST"])
@login_required
def delete_service(id):
    service = Service.query.get_or_404(id)
    try:
        db.session.delete(service)
        db.session.commit()
        flash("Servicio eliminado exitosamente", "success")
    except Exception as e:
        logger.error(f"Error al eliminar servicio: {str(e)}")
        flash("Error al eliminar el servicio", "danger")

    return redirect(url_for("admin.list_services"))


# ==================== GALERIA DE IMAGENES DE SERVICIO ====================


@admin_bp.route("/servicios/<int:id>/imagenes", methods=["GET", "POST"])
@login_required
def manage_service_images(id):
    service = Service.query.get_or_404(id)
    uploads_dir = current_app.config.get(
        "SERVICE_IMAGES_DIR",
        os.path.join(current_app.static_folder, "uploads", "servicios"),
    )
    os.makedirs(uploads_dir, exist_ok=True)

    if request.method == "POST":
        action = request.form.get("action")

        if action == "subir":
            files = request.files.getlist("photos")
            activas = service.gallery_images.filter_by(is_active=True).count()
            subidas, errores = 0, 0
            avisos = []
            for f in files:
                if not f or not f.filename:
                    continue
                if activas + subidas >= ServiceImage.MAX_IMAGES_PER_SERVICE:
                    flash(
                        f"Maximo {ServiceImage.MAX_IMAGES_PER_SERVICE} imagenes "
                        "activas por servicio. Elimina alguna primero.",
                        "warning",
                    )
                    break
                if not ServiceImage.allowed_file(f.filename):
                    errores += 1
                    continue

                # Validar que sea una imagen real y normalizarla:
                # max 1920px de ancho, proporcion original intacta,
                # JPEG optimizado para el cintillo sin perder nitidez.
                try:
                    from PIL import Image

                    img = Image.open(f.stream)
                    img.load()
                    ancho, alto = img.size
                    if ancho < 640 or alto < 360:
                        avisos.append(
                            f"{f.filename}: muy pequena ({ancho}x{alto}), "
                            "minimo recomendado 640x360"
                        )
                        errores += 1
                        continue
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    if ancho > 1920:
                        nuevo_alto = int(alto * 1920 / ancho)
                        img = img.resize((1920, nuevo_alto), Image.Resampling.LANCZOS)
                    filename = ServiceImage.generate_filename("x.jpg")
                    img.save(
                        os.path.join(uploads_dir, filename),
                        format="JPEG",
                        quality=88,
                        optimize=True,
                        progressive=True,
                    )
                except Exception:
                    logger.warning(
                        f"Archivo rechazado por no ser imagen valida: {f.filename}"
                    )
                    errores += 1
                    continue

                imagen = ServiceImage(
                    service_id=service.id,
                    image_path=f"uploads/servicios/{filename}",
                    caption=request.form.get("caption", "").strip() or None,
                    order=service.gallery_images.count() + 1,
                )
                db.session.add(imagen)
                subidas += 1
            if subidas:
                db.session.commit()
                flash(
                    f"{subidas} imagen(es) procesada(s) y subida(s) "
                    "(recortadas a maximo 1920px de ancho, sin deformar)",
                    "success",
                )
            if errores:
                flash(
                    f"{errores} archivo(s) ignorados: deben ser imagenes "
                    "png/jpg/webp de al menos 640x360",
                    "danger",
                )
            for aviso in avisos:
                flash(aviso, "warning")
            return redirect(url_for("admin.manage_service_images", id=service.id))

        elif action == "eliminar":
            imagen = ServiceImage.query.get_or_404(_int_form("image_id"))
            try:
                imagen.delete_file(uploads_dir)
                db.session.delete(imagen)
                db.session.commit()
                flash("Imagen eliminada", "success")
            except Exception as e:
                logger.error(f"Error al eliminar imagen: {str(e)}")
                flash("Error al eliminar la imagen", "danger")
            return redirect(url_for("admin.manage_service_images", id=service.id))

        elif action == "alternar":
            imagen = ServiceImage.query.get_or_404(_int_form("image_id"))
            if not imagen.is_active:
                activas = service.gallery_images.filter_by(is_active=True).count()
                if activas >= ServiceImage.MAX_IMAGES_PER_SERVICE:
                    flash(
                        f"Maximo {ServiceImage.MAX_IMAGES_PER_SERVICE} imagenes "
                        "activas por servicio.",
                        "warning",
                    )
                    return redirect(
                        url_for("admin.manage_service_images", id=service.id)
                    )
            imagen.is_active = not imagen.is_active
            db.session.commit()
            estado = "activada" if imagen.is_active else "desactivada"
            flash(f"Imagen {estado}", "success")
            return redirect(url_for("admin.manage_service_images", id=service.id))

    imagenes = service.gallery_images.order_by(
        ServiceImage.order, ServiceImage.id
    ).all()
    return render_template(
        "admin/services/images.html", service=service, imagenes=imagenes
    )


# ==================== GESTION DE TICKETS ====================


@admin_bp.route("/tickets")
@login_required
def list_tickets():
    status_filter = request.args.get("status")
    urgency_filter = request.args.get("urgency")

    query = Ticket.query

    if status_filter:
        query = query.filter_by(status=status_filter)
    if urgency_filter:
        query = query.filter_by(urgency=urgency_filter)

    tickets = query.order_by(db.desc(Ticket.created_at)).all()
    statuses = ["new", "in_progress", "resolved", "closed", "cancelled"]
    urgencies = ["low", "medium", "high", "critical"]

    return render_template(
        "admin/tickets/list.html",
        tickets=tickets,
        statuses=statuses,
        urgencies=urgencies,
        current_status=status_filter,
        current_urgency=urgency_filter,
    )


@admin_bp.route("/tickets/<int:id>")
@login_required
def view_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    users = User.query.filter_by(is_active=True).order_by(User.full_name).all()
    return render_template("admin/tickets/detail.html", ticket=ticket, users=users)


@admin_bp.route("/tickets/<int:id>/actualizar", methods=["POST"])
@login_required
def update_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    status = request.form.get("status")
    notes = request.form.get("notes")
    assigned_to = request.form.get("assigned_to")

    try:
        if status:
            ticket.status = status
            if status == "resolved" and not ticket.resolved_at:
                ticket.resolved_at = datetime.utcnow()

        if notes:
            ticket.admin_notes = notes

        if assigned_to:
            ticket.assigned_to = int(assigned_to) if assigned_to.isdigit() else None

        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        flash("Ticket actualizado exitosamente", "success")
    except Exception as e:
        logger.error(f"Error al actualizar ticket: {str(e)}")
        flash("Error al actualizar el ticket", "danger")

    return redirect(url_for("admin.view_ticket", id=id))


# ==================== GESTIÓN DE TESTIMONIOS ====================


@admin_bp.route("/testimonios")
@login_required
def list_testimonials():
    testimonials = Testimonial.query.order_by(db.desc(Testimonial.created_at)).all()
    return render_template("admin/testimonials/list.html", testimonials=testimonials)


@admin_bp.route("/testimonios/crear", methods=["GET", "POST"])
@login_required
def create_testimonial():
    form = TestimonialForm()
    form.service_id.choices = [(s.id, s.name) for s in Service.query.all()]

    if form.validate_on_submit():
        try:
            testimonial = Testimonial(
                client_name=form.client_name.data,
                client_position=form.client_position.data,
                condominium_name=form.condominium_name.data,
                content=form.content.data,
                rating=int(form.rating.data),
                service_id=int(form.service_id.data) if form.service_id.data else None,
                is_approved=form.is_approved.data,
                is_featured=form.is_featured.data,
            )
            if testimonial.is_approved:
                testimonial.approved_at = datetime.utcnow()

            db.session.add(testimonial)
            db.session.commit()
            flash("Testimonio creado exitosamente", "success")
            return redirect(url_for("admin.list_testimonials"))
        except Exception as e:
            logger.error(f"Error al crear testimonio: {str(e)}")
            flash("Error al crear el testimonio", "danger")

    return render_template("admin/testimonials/create.html", form=form)


@admin_bp.route("/testimonios/aprobar/<int:id>", methods=["POST"])
@login_required
def approve_testimonial(id):
    testimonial = Testimonial.query.get_or_404(id)
    testimonial.is_approved = True
    testimonial.approved_at = datetime.utcnow()
    db.session.commit()
    flash("Testimonio aprobado", "success")
    return redirect(url_for("admin.list_testimonials"))


@admin_bp.route("/testimonios/eliminar/<int:id>", methods=["POST"])
@login_required
def delete_testimonial(id):
    testimonial = Testimonial.query.get_or_404(id)
    try:
        db.session.delete(testimonial)
        db.session.commit()
        flash("Testimonio eliminado", "success")
    except Exception as e:
        logger.error(f"Error al eliminar testimonio: {str(e)}")
        flash("Error al eliminar el testimonio", "danger")

    return redirect(url_for("admin.list_testimonials"))


# ==================== GESTIÓN DE DIAGNÓSTICOS ====================


@admin_bp.route("/diagnosticos")
@login_required
def list_diagnostics():
    diagnostics = Diagnostic.query.order_by(db.desc(Diagnostic.created_at)).all()
    return render_template("admin/diagnostics/list.html", diagnostics=diagnostics)


@admin_bp.route("/diagnosticos/<int:id>")
@login_required
def view_diagnostic(id):
    diagnostic = Diagnostic.query.get_or_404(id)
    return render_template("admin/diagnostics/detail.html", diagnostic=diagnostic)


# ==================== GESTIÓN DE USUARIOS ====================


@admin_bp.route("/usuarios")
@login_required
def list_users():
    if not current_user.is_admin:
        flash("No tienes permisos para ver esta página", "danger")
        return redirect(url_for("admin.dashboard"))

    users = User.query.all()
    return render_template("admin/users/list.html", users=users)


@admin_bp.route("/usuarios/crear", methods=["GET", "POST"])
@login_required
def create_user():
    if not current_user.is_admin:
        flash("No tienes permisos para realizar esta acción", "danger")
        return redirect(url_for("admin.dashboard"))

    form = UserForm()
    if form.validate_on_submit():
        try:
            user = User(
                email=form.email.data,
                full_name=form.full_name.data,
                role=form.role.data,
                is_active=form.is_active.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Usuario creado exitosamente", "success")
            return redirect(url_for("admin.list_users"))
        except Exception as e:
            logger.error(f"Error al crear usuario: {str(e)}")
            flash("Error al crear el usuario", "danger")

    return render_template("admin/users/create.html", form=form)


# ==================== AJAX ENDPOINTS ====================


@admin_bp.route("/api/tickets/stats")
@login_required
def ticket_stats():
    """Endpoint AJAX para estadísticas de tickets"""
    total = Ticket.query.count()
    pending = Ticket.query.filter(Ticket.status.in_(["new", "in_progress"])).count()
    resolved = Ticket.query.filter_by(status="resolved").count()

    return jsonify(
        {
            "total": total,
            "pending": pending,
            "resolved": resolved,
            "critical": Ticket.query.filter_by(
                urgency="critical", status="new"
            ).count(),
        }
    )


@admin_bp.route("/api/dashboard/widgets")
@login_required
def dashboard_widgets():
    """Widgets para el dashboard"""
    return jsonify(
        {
            "tickets_30d": Ticket.query.filter(
                Ticket.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count(),
            "tickets_today": Ticket.query.filter(
                func.date(Ticket.created_at) == func.date(datetime.utcnow())
            ).count(),
            "avg_response_time": "4.5h",
            "satisfaction_rate": "96%",
        }
    )
