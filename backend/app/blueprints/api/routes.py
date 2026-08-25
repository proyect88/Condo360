from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models.service import Service
from app.models.ticket import Ticket
from app.models.testimonial import Testimonial
from app.models.diagnostic import Diagnostic
from app.services.diagnostic_engine import DiagnosticEngine
from app import db
from datetime import datetime
import logging

api_bp = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

ESTADOS_TICKET_VALIDOS = ["new", "in_progress", "resolved", "closed", "cancelled"]

LONGITUD_MAXIMA = {
    "client_name": 120,
    "client_email": 120,
    "client_phone": 30,
    "condominium_name": 150,
    "description": 2000,
    "address": 250,
}


def _datos_json():
    """Lee el cuerpo JSON de forma segura; None si no es un objeto valido."""
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else None


def _texto(datos, campo, defecto=None):
    """Extrae un campo de texto recortado y limitado en longitud."""
    valor = datos.get(campo, defecto)
    if not isinstance(valor, str):
        return defecto
    return valor.strip()[: LONGITUD_MAXIMA.get(campo, 500)] or defecto


# ==================== SERVICIOS API ====================


@api_bp.route("/services")
def get_services():
    """Obtener lista de servicios"""
    category = request.args.get("category")
    query = Service.query.filter_by(is_active=True)

    if category:
        query = query.filter_by(category=category)

    services = query.order_by(Service.order).all()
    return jsonify([s.to_dict() for s in services])


@api_bp.route("/services/<int:id>")
def get_service(id):
    """Obtener un servicio por ID"""
    service = Service.query.get_or_404(id)
    return jsonify(service.to_dict())


@api_bp.route("/services/slug/<slug>")
def get_service_by_slug(slug):
    """Obtener un servicio por slug"""
    service = Service.query.filter_by(slug=slug, is_active=True).first_or_404()
    return jsonify(service.to_dict())


# ==================== TICKETS API ====================


@api_bp.route("/tickets", methods=["POST"])
def create_ticket():
    """Crear un nuevo ticket vía API"""
    data = _datos_json()
    if data is None:
        return jsonify({"success": False, "error": "Cuerpo JSON invalido"}), 400

    nombre = _texto(data, "client_name")
    email = _texto(data, "client_email")
    descripcion = _texto(data, "description")

    if not nombre or not email or "@" not in email:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "client_name y client_email validos son obligatorios",
                }
            ),
            400,
        )

    try:
        ticket = Ticket(
            client_name=nombre,
            client_email=email,
            client_phone=_texto(data, "client_phone"),
            condominium_name=_texto(data, "condominium_name"),
            service_type=_texto(data, "service_type", "general"),
            description=descripcion,
            urgency=(
                data.get("urgency")
                if data.get("urgency")
                in [
                    "low",
                    "medium",
                    "high",
                    "critical",
                ]
                else "medium"
            ),
            address=_texto(data, "address"),
        )

        db.session.add(ticket)
        db.session.commit()

        return jsonify({"success": True, "ticket": ticket.to_dict()}), 201

    except Exception:
        logger.exception("Error API create_ticket")
        db.session.rollback()
        return jsonify({"success": False, "error": "No se pudo crear el ticket"}), 400


@api_bp.route("/tickets/<string:ticket_number>")
def get_ticket(ticket_number):
    """Obtener estado de un ticket.

    Requiere el email del solicitante para evitar que terceros consulten
    datos de contacto adivinando el numero de ticket.
    """
    email = (request.args.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "Parametro email obligatorio"}), 401

    ticket = Ticket.query.filter_by(ticket_number=ticket_number).first()
    if not ticket or not ticket.client_email:
        return jsonify({"error": "Ticket no encontrado"}), 404

    if ticket.client_email.strip().lower() != email:
        # Mismo mensaje para no revelar si el ticket existe
        return jsonify({"error": "Ticket no encontrado"}), 404

    return jsonify(ticket.to_dict())


# ==================== DIAGNÓSTICO API ====================


@api_bp.route("/diagnostic", methods=["POST"])
def run_diagnostic():
    """Ejecutar diagnóstico vía API"""
    data = _datos_json()
    if data is None:
        return jsonify({"success": False, "error": "Cuerpo JSON invalido"}), 400

    try:
        engine = DiagnosticEngine()
        result = engine.analyze(data)

        return jsonify({"success": True, "result": result})

    except Exception:
        logger.exception("Error API diagnostic")
        return jsonify({"success": False, "error": "No se pudo procesar"}), 400


@api_bp.route("/diagnostic/<token>")
def get_diagnostic(token):
    """Obtener diagnóstico por token"""
    diagnostic = Diagnostic.query.filter_by(diagnostic_token=token).first()
    if not diagnostic:
        return jsonify({"error": "Diagnóstico no encontrado"}), 404

    return jsonify(diagnostic.to_dict())


# ==================== TESTIMONIOS API ====================


@api_bp.route("/testimonials")
def get_testimonials():
    """Obtener testimonios aprobados"""
    limit = min(request.args.get("limit", 10, type=int) or 10, 50)
    testimonials = (
        Testimonial.query.filter_by(is_approved=True)
        .order_by(db.desc(Testimonial.created_at))
        .limit(limit)
        .all()
    )
    return jsonify([t.to_dict() for t in testimonials])


# ==================== CONTACTO API ====================


@api_bp.route("/contact", methods=["POST"])
def contact_form():
    """Formulario de contacto vía API"""
    data = _datos_json()
    if data is None:
        return jsonify({"success": False, "error": "Cuerpo JSON invalido"}), 400

    nombre = _texto(data, "name")
    email = _texto(data, "email")
    mensaje = _texto(data, "message")

    if not nombre or not email or "@" not in email or not mensaje:
        return (
            jsonify(
                {"success": False, "error": "name, email y message son obligatorios"}
            ),
            400,
        )

    try:
        ticket = Ticket(
            client_name=nombre,
            client_email=email,
            client_phone=_texto(data, "phone"),
            condominium_name=_texto(data, "condominium"),
            service_type=_texto(data, "service_type", "general"),
            description=mensaje,
            urgency=(
                data.get("urgency")
                if data.get("urgency")
                in [
                    "low",
                    "medium",
                    "high",
                    "critical",
                ]
                else "medium"
            ),
        )

        db.session.add(ticket)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Mensaje enviado correctamente",
                    "ticket_number": ticket.ticket_number,
                }
            ),
            201,
        )

    except Exception:
        logger.exception("Error API contact")
        db.session.rollback()
        return jsonify({"success": False, "error": "No se pudo enviar"}), 400


# ==================== WEBHOOKS ====================


@api_bp.route("/webhook/ticket-status", methods=["POST"])
@login_required
def webhook_ticket_status():
    """Webhook para actualizar estado de tickets"""
    data = _datos_json()
    if data is None:
        return jsonify({"error": "Cuerpo JSON invalido"}), 400

    ticket_number = data.get("ticket_number")
    status = data.get("status")

    if not ticket_number or status not in ESTADOS_TICKET_VALIDOS:
        return jsonify({"error": "Datos invalidos"}), 400

    ticket = Ticket.query.filter_by(ticket_number=ticket_number).first()
    if not ticket:
        return jsonify({"error": "Ticket no encontrado"}), 404

    ticket.status = status
    if status == "resolved":
        ticket.resolved_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"success": True})
