from app.models.ticket import Ticket
from app.models.client import Client
from app import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TicketManager:
    """Gestor de tickets"""

    @staticmethod
    def create_ticket(data):
        """Crear un nuevo ticket"""
        try:
            ticket = Ticket(**data)

            # Verificar si el cliente existe
            client = Client.query.filter_by(email=data.get("client_email")).first()
            if not client and data.get("client_email"):
                client = Client(
                    name=data.get("client_name"),
                    email=data.get("client_email"),
                    phone=data.get("client_phone"),
                    condominium_name=data.get("condominium_name"),
                )
                db.session.add(client)

            db.session.add(ticket)
            db.session.commit()
            logger.info(f"Ticket creado: {ticket.ticket_number}")
            return ticket

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear ticket: {str(e)}")
            raise

    @staticmethod
    def get_ticket(ticket_number):
        """Obtener ticket por número"""
        return Ticket.query.filter_by(ticket_number=ticket_number).first()

    @staticmethod
    def update_status(ticket_id, status, notes=None):
        """Actualizar estado de un ticket"""
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            raise ValueError("Ticket no encontrado")

        try:
            ticket.status = status
            if status == "resolved" and not ticket.resolved_at:
                ticket.resolved_at = datetime.utcnow()
            if notes:
                ticket.admin_notes = notes
            ticket.updated_at = datetime.utcnow()

            db.session.commit()
            logger.info(f"Ticket {ticket.ticket_number} actualizado a {status}")
            return ticket

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al actualizar ticket: {str(e)}")
            raise

    @staticmethod
    def get_pending_count():
        """Obtener cantidad de tickets pendientes"""
        return Ticket.query.filter(Ticket.status.in_(["new", "in_progress"])).count()

    @staticmethod
    def get_tickets_by_status(status):
        """Obtener tickets por estado"""
        return (
            Ticket.query.filter_by(status=status)
            .order_by(db.desc(Ticket.created_at))
            .all()
        )

    @staticmethod
    def get_recent_tickets(limit=10):
        """Obtener tickets recientes"""
        return Ticket.query.order_by(db.desc(Ticket.created_at)).limit(limit).all()

    @staticmethod
    def get_stats():
        """Obtener estadísticas de tickets"""
        return {
            "total": Ticket.query.count(),
            "new": Ticket.query.filter_by(status="new").count(),
            "in_progress": Ticket.query.filter_by(status="in_progress").count(),
            "resolved": Ticket.query.filter_by(status="resolved").count(),
            "closed": Ticket.query.filter_by(status="closed").count(),
            "critical": Ticket.query.filter_by(
                urgency="critical", status="new"
            ).count(),
        }
