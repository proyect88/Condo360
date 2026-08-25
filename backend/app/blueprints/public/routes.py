from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    session,
)
from app.models.service import Service
from app.models.service_image import ServiceImage
from app.models.testimonial import Testimonial
from app.models.ticket import Ticket
from app.models.diagnostic import Diagnostic
from app.services.diagnostic_engine import DiagnosticEngine
from app.services.notification_service import NotificationService
from app import db
import html
import logging
import re

public_bp = Blueprint("public", __name__)
logger = logging.getLogger(__name__)


@public_bp.route("/")
def index():
    """Página principal - Landing"""
    try:
        services = (
            Service.query.filter_by(is_active=True, is_featured=True)
            .order_by(Service.order)
            .limit(6)
            .all()
        )
        if not services:
            services = (
                Service.query.filter_by(is_active=True)
                .order_by(Service.order)
                .limit(6)
                .all()
            )

        testimonials = (
            Testimonial.query.filter_by(is_approved=True)
            .order_by(db.desc(Testimonial.created_at))
            .limit(6)
            .all()
        )

        # Estadísticas
        stats = {
            "services_count": Service.query.filter_by(is_active=True).count(),
            "clients_satisfied": Testimonial.query.filter_by(is_approved=True).count()
            * 25
            + 100,
            "projects_completed": Ticket.query.filter_by(status="resolved").count() * 3
            + 200,
            "response_time": "< 24 horas",
        }

        return render_template(
            "public/index.html",
            services=services,
            testimonials=testimonials,
            stats=stats,
        )
    except Exception as e:
        logger.error(f"Error en index: {str(e)}")
        return render_template(
            "public/index.html", services=[], testimonials=[], stats={}
        )


@public_bp.route("/servicios")
def services():
    """Página de servicios"""
    category = request.args.get("categoria")
    query = Service.query.filter_by(is_active=True)

    if category:
        query = query.filter_by(category=category)

    services = query.order_by(Service.order).all()
    categories = db.session.query(Service.category).distinct().all()

    # Diccionario de iconos por categoría
    category_icons = {
        "albanileria": "fa-helmet-safety",
        "plomeria": "fa-wrench",
        "electricidad": "fa-bolt",
        "jardineria": "fa-leaf",
        "ascensores": "fa-elevator",
        "gestion": "fa-clipboard-check",
    }

    return render_template(
        "public/services.html",
        services=services,
        categories=categories,
        selected_category=category,
        category_icons=category_icons,
    )


@public_bp.route("/servicios/<slug>")
def service_detail(slug):
    """Detalle de un servicio específico"""
    service = Service.query.filter_by(slug=slug, is_active=True).first_or_404()
    testimonials = (
        Testimonial.query.filter_by(service_id=service.id, is_approved=True)
        .limit(5)
        .all()
    )
    galeria = (
        ServiceImage.query.filter_by(service_id=service.id, is_active=True)
        .order_by(ServiceImage.order, ServiceImage.id)
        .all()
    )

    return render_template(
        "public/service_detail.html",
        service=service,
        testimonials=testimonials,
        galeria=galeria,
    )


@public_bp.route("/testimonios")
def testimonials():
    """Página de testimonios"""
    testimonials = (
        Testimonial.query.filter_by(is_approved=True)
        .order_by(db.desc(Testimonial.created_at))
        .all()
    )
    return render_template("public/testimonials.html", testimonials=testimonials)


@public_bp.route("/diagnostico", methods=["GET", "POST"])
def diagnostic():
    """Diagnóstico interactivo"""
    if request.method == "POST":
        try:
            # Seguridad 1: rechazar cualquier intento de subida de archivos
            if request.files:
                flash("Este formulario no acepta archivos adjuntos.", "danger")
                return redirect(url_for("public.diagnostic"))

            # Seguridad 2: sanitizar todo texto (sin HTML, sin caracteres de
            # control, largo acotado). Solo texto plano.
            def limpiar(valor, max_len):
                if not valor:
                    return None
                v = re.sub(r"<[^>]*>", "", str(valor))
                v = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", v)
                v = html.escape(v, quote=False)
                v = " ".join(v.split())
                return v[:max_len] or None

            # Seguridad 3: valores solo desde listas blancas cerradas
            PROBLEMAS_VALIDOS = {
                "fugas_agua",
                "problemas_electricos",
                "estructural",
                "ascensor",
                "humedad",
                "jardineria",
                "seguridad",
                "saneamiento",
            }
            URGENCIAS_VALIDAS = {"low", "medium", "high", "critical"}
            CONTACTOS_VALIDOS = {"email", "phone", "whatsapp"}
            PRESUPUESTOS_VALIDOS = {
                "0-200000",
                "200000-500000",
                "500000-1000000",
                "1000000+",
            }
            EDAD_MAP = {"5": 5, "15": 15, "25": 25, "35": 35, "45": 45}
            UNIDADES_MAP = {"10": 10, "30": 30, "80": 80, "150": 150}

            issue_types = [
                p for p in request.form.getlist("issue_types") if p in PROBLEMAS_VALIDOS
            ]
            urgency = (
                request.form.get("urgency")
                if request.form.get("urgency") in URGENCIAS_VALIDAS
                else None
            )
            contact_preference = (
                request.form.get("contact_preference")
                if request.form.get("contact_preference") in CONTACTOS_VALIDOS
                else "email"
            )
            budget = (
                request.form.get("budget")
                if request.form.get("budget") in PRESUPUESTOS_VALIDOS
                else None
            )
            building_age = EDAD_MAP.get(request.form.get("building_age", ""))
            units_count = UNIDADES_MAP.get(request.form.get("units_count", ""))

            client_email_raw = (request.form.get("client_email") or "").strip()[:120]
            if not re.fullmatch(
                r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
                client_email_raw,
            ):
                flash("Ingresa un email valido (ej: nombre@dominio.cl).", "danger")
                return redirect(url_for("public.diagnostic"))

            client_phone_raw = (request.form.get("client_phone") or "").strip()
            if client_phone_raw and not re.fullmatch(
                r"\+?[0-9\s\-]{7,20}", client_phone_raw
            ):
                flash(
                    "El telefono solo admite numeros, espacios y el signo +.",
                    "danger",
                )
                return redirect(url_for("public.diagnostic"))

            condominium_name = limpiar(request.form.get("condominium_name"), 120)
            client_name = limpiar(request.form.get("client_name"), 100)
            if not condominium_name or not client_name:
                flash("Completa el nombre del condominio y tu nombre.", "danger")
                return redirect(url_for("public.diagnostic"))
            if not issue_types or not urgency:
                flash(
                    "Selecciona al menos un problema y el nivel de urgencia.",
                    "danger",
                )
                return redirect(url_for("public.diagnostic"))

            # Recopilar datos ya validados para el motor
            diagnostic_data = {
                "condominium_name": condominium_name,
                "address": limpiar(request.form.get("address"), 200),
                "units_count": units_count,
                "building_age": building_age,
                "construction_type": None,
                "issue_types": issue_types,
                "issue_descriptions": limpiar(
                    request.form.get("issue_description"), 600
                ),
                "urgency": urgency,
                "budget": budget,
                "client_name": client_name,
                "client_email": client_email_raw,
                "client_phone": client_phone_raw or None,
                "contact_preference": contact_preference,
            }

            # Procesar diagnóstico
            engine = DiagnosticEngine()
            result = engine.analyze(diagnostic_data)

            # Guardar en base de datos
            diagnostic = Diagnostic(
                condominium_name=diagnostic_data.get("condominium_name"),
                address=diagnostic_data.get("address"),
                units_count=diagnostic_data.get("units_count"),
                building_age=diagnostic_data.get("building_age"),
                construction_type=None,
                issues=diagnostic_data.get("issue_types", []),
                urgency_score=result.get("urgency_score", 0),
                recommended_service_id=result.get("recommended_service_id"),
                client_name=diagnostic_data.get("client_name"),
                client_email=diagnostic_data.get("client_email"),
                client_phone=diagnostic_data.get("client_phone"),
                contact_preference=diagnostic_data.get("contact_preference"),
                status="pending",
                user_agent=request.headers.get("User-Agent"),
                ip_address=request.remote_addr,
            )
            db.session.add(diagnostic)
            db.session.commit()

            # Crear ticket automático si es urgente
            if result.get("urgency_score", 0) >= 7:
                ticket = Ticket(
                    client_name=diagnostic.client_name or "Diagnóstico automático",
                    client_email=diagnostic.client_email or "no-reply@diagnostico.com",
                    client_phone=diagnostic.client_phone,
                    condominium_name=diagnostic.condominium_name,
                    service_type="diagnostico_integral",
                    description=(
                        f"Diagnóstico automático:\n\nCondominio: {diagnostic.condominium_name}\n"
                        f"Problemas: {', '.join(diagnostic.issues or [])}\n"
                        f"Urgencia: {diagnostic.urgency_label}\n\n"
                        f"{diagnostic_data.get('issue_descriptions', '')}"
                    ),
                    urgency="high" if result.get("urgency_score", 0) >= 8 else "medium",
                )
                db.session.add(ticket)
                db.session.commit()

                # Enviar notificación
                NotificationService.send_diagnostic_notification(diagnostic)
                NotificationService.send_ticket_notification(ticket)

            # Guardar solo el id en sesion para la confirmacion.
            # El detalle del diagnostico lo ve el admin y se contacta
            # con el solicitante por su via preferida.
            session.pop("diagnostic_result", None)
            session["diagnostic_id"] = diagnostic.id
            session["diagnostic_contact"] = contact_preference

            flash("¡Diagnóstico enviado con éxito!", "success")
            return redirect(url_for("public.diagnostic_recibido"))

        except Exception as e:
            logger.error(f"Error en diagnóstico: {str(e)}")
            flash(
                "Hubo un error al procesar el diagnóstico. Por favor, intenta de nuevo.",
                "danger",
            )
            return redirect(url_for("public.diagnostic"))

    services = Service.query.filter_by(is_active=True).all()
    return render_template("public/diagnostic.html", services=services)


@public_bp.route("/diagnostico/recibido")
def diagnostic_recibido():
    """Confirmacion de diagnostico recibido.

    No muestra puntajes ni recomendaciones: el equipo del condominio
    revisa el caso en el panel admin y se comunica con el solicitante
    por la via de contacto que este eligio.
    """
    diagnostic_id = session.get("diagnostic_id")
    if not diagnostic_id:
        return redirect(url_for("public.diagnostic"))

    contact_preference = session.get("diagnostic_contact", "email")
    vias = {
        "email": {
            "icono": "fa-envelope",
            "texto": "tu email",
            "detalle": "Te enviaremos el presupuesto detallado por correo.",
        },
        "phone": {
            "icono": "fa-phone",
            "texto": "tu teléfono",
            "detalle": "Un ejecutivo te llamará para coordinar la visita.",
        },
        "whatsapp": {
            "icono": "fa-whatsapp",
            "texto": "tu WhatsApp",
            "detalle": "Te escribiremos por WhatsApp para coordinar la visita.",
        },
    }
    via = vias.get(contact_preference, vias["email"])

    return render_template(
        "public/diagnostic_recibido.html",
        via=via,
    )


@public_bp.route("/contacto", methods=["GET", "POST"])
def contact():
    """Página de contacto y solicitud de presupuesto"""
    if request.method == "POST":
        try:
            # Crear ticket desde contacto
            ticket = Ticket(
                client_name=request.form.get("name"),
                client_email=request.form.get("email"),
                client_phone=request.form.get("phone"),
                condominium_name=request.form.get("condominium"),
                service_type=request.form.get("service_type", "general"),
                description=request.form.get("message"),
                urgency=request.form.get("urgency", "medium"),
                address=request.form.get("address"),
            )
            ticket.generate_ticket_number()

            db.session.add(ticket)
            db.session.commit()

            # Enviar notificaciones
            NotificationService.send_ticket_notification(ticket)
            NotificationService.send_confirmation_client(ticket)

            flash("¡Hemos recibido tu solicitud! Pronto te contactaremos.", "success")
            return redirect(url_for("public.thank_you"))

        except Exception as e:
            logger.error(f"Error en contacto: {str(e)}")
            flash(
                "Hubo un error al enviar el mensaje. Por favor, intenta de nuevo.",
                "danger",
            )

    services = Service.query.filter_by(is_active=True).all()
    return render_template("public/contact.html", services=services)


@public_bp.route("/gracias")
def thank_you():
    return render_template("public/thank_you.html")


@public_bp.route("/faq")
def faq():
    """Página de preguntas frecuentes"""
    return render_template("public/faq.html")
