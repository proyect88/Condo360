from app.extensions import db
from datetime import datetime
import random
import string


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # Cliente
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(120), nullable=False)
    client_phone = db.Column(db.String(20))
    condominium_name = db.Column(db.String(200))

    # Detalles del servicio
    service_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(20), default="medium")
    status = db.Column(db.String(20), default="new")

    # Ubicacion
    address = db.Column(db.String(200))
    building = db.Column(db.String(50))
    floor = db.Column(db.String(20))

    # Admin
    admin_notes = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"))

    # Fechas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    resolved_at = db.Column(db.DateTime)

    # Relaciones
    assigned_user = db.relationship("User", foreign_keys=[assigned_to], lazy=True)

    def __init__(self, **kwargs):
        super(Ticket, self).__init__(**kwargs)
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()

    def generate_ticket_number(self):
        """Generar numero de ticket unico"""
        prefix = "CS"
        random_chars = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=8)
        )
        return f"{prefix}-{random_chars}"

    @property
    def urgency_label(self):
        labels = {
            "low": "Baja",
            "medium": "Media",
            "high": "Alta",
            "critical": "Crítica",
        }
        return labels.get(self.urgency, self.urgency)

    @property
    def urgency_color(self):
        colors = {
            "low": "success",
            "medium": "warning",
            "high": "danger",
            "critical": "danger",
        }
        return colors.get(self.urgency, "secondary")

    @property
    def status_label(self):
        labels = {
            "new": "Nuevo",
            "in_progress": "En Progreso",
            "resolved": "Resuelto",
            "closed": "Cerrado",
            "cancelled": "Cancelado",
        }
        return labels.get(self.status, self.status)

    @property
    def status_color(self):
        colors = {
            "new": "primary",
            "in_progress": "warning",
            "resolved": "success",
            "closed": "secondary",
            "cancelled": "danger",
        }
        return colors.get(self.status, "secondary")

    def resolve(self):
        self.status = "resolved"
        self.resolved_at = datetime.utcnow()

    def close(self):
        self.status = "closed"

    def can_edit(self):
        return self.status not in ["closed", "cancelled"]

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_number": self.ticket_number,
            "client_name": self.client_name,
            "client_email": self.client_email,
            "client_phone": self.client_phone,
            "condominium_name": self.condominium_name,
            "service_type": self.service_type,
            "description": self.description,
            "urgency": self.urgency,
            "urgency_label": self.urgency_label,
            "status": self.status,
            "status_label": self.status_label,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

    def __repr__(self):
        return f"<Ticket {self.ticket_number}>"
