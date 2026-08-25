from flask import current_app, render_template
from flask_mail import Message
from app import mail
import logging
import re
from threading import Thread

logger = logging.getLogger(__name__)


def _asunto_seguro(texto):
    """Elimina saltos de linea para prevenir inyeccion de cabeceras SMTP."""
    return re.sub(r"[\r\n]+", " ", str(texto)).strip()


class NotificationService:
    """Servicio de notificaciones"""

    @staticmethod
    def send_async_email(app, msg):
        """Enviar email de forma asíncrona"""
        with app.app_context():
            try:
                mail.send(msg)
                logger.info(f"Email enviado a {msg.recipients}")
            except Exception as e:
                logger.error(f"Error al enviar email: {str(e)}")

    @staticmethod
    def send_email(to, subject, template, **kwargs):
        """Enviar email usando plantilla"""
        app = current_app._get_current_object()
        msg = Message(
            subject=_asunto_seguro(subject),
            sender=app.config["MAIL_DEFAULT_SENDER"],
            recipients=[to],
        )
        msg.html = render_template(template, **kwargs)

        # Enviar en thread separado
        Thread(target=NotificationService.send_async_email, args=(app, msg)).start()

        return True

    @staticmethod
    def send_ticket_notification(ticket):
        """Enviar notificación de ticket nuevo"""
        try:
            admin_email = current_app.config.get("ADMIN_EMAIL")
            if admin_email:
                NotificationService.send_email(
                    to=admin_email,
                    subject=f"Nuevo Ticket: {ticket.ticket_number}",
                    template="emails/ticket_notification.html",
                    ticket=ticket,
                )
                logger.info(f"Notificación de ticket enviada a {admin_email}")
        except Exception as e:
            logger.error(f"Error al enviar notificación de ticket: {str(e)}")

    @staticmethod
    def send_confirmation_client(ticket):
        """Enviar confirmación al cliente"""
        try:
            if ticket.client_email:
                NotificationService.send_email(
                    to=ticket.client_email,
                    subject=f"Confirmación de solicitud - Ticket {ticket.ticket_number}",
                    template="emails/client_confirmation.html",
                    ticket=ticket,
                )
                logger.info(f"Confirmación enviada a {ticket.client_email}")
        except Exception as e:
            logger.error(f"Error al enviar confirmación al cliente: {str(e)}")

    @staticmethod
    def send_diagnostic_notification(diagnostic):
        """Enviar notificación de diagnóstico"""
        try:
            admin_email = current_app.config.get("ADMIN_EMAIL")
            if admin_email:
                NotificationService.send_email(
                    to=admin_email,
                    subject=f"Nuevo Diagnóstico - {diagnostic.condominium_name}",
                    template="emails/diagnostic_notification.html",
                    diagnostic=diagnostic,
                )
                logger.info(f"Notificación de diagnóstico enviada a {admin_email}")
        except Exception as e:
            logger.error(f"Error al enviar notificación de diagnóstico: {str(e)}")

    @staticmethod
    def send_status_update(ticket):
        """Enviar actualización de estado al cliente"""
        try:
            if ticket.client_email and ticket.status in ["resolved", "in_progress"]:
                NotificationService.send_email(
                    to=ticket.client_email,
                    subject=f"Actualización de tu Ticket {ticket.ticket_number}",
                    template="emails/status_update.html",
                    ticket=ticket,
                )
                logger.info(f"Actualización enviada a {ticket.client_email}")
        except Exception as e:
            logger.error(f"Error al enviar actualización de estado: {str(e)}")

    @staticmethod
    def send_welcome_email(user):
        """Enviar email de bienvenida"""
        try:
            if user.email:
                NotificationService.send_email(
                    to=user.email,
                    subject="Bienvenido a Condo Services 360",
                    template="emails/welcome.html",
                    user=user,
                )
                logger.info(f"Email de bienvenida enviado a {user.email}")
        except Exception as e:
            logger.error(f"Error al enviar email de bienvenida: {str(e)}")
