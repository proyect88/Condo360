from app.extensions import db
from datetime import datetime


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)

    # Datos de contacto
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    alternative_phone = db.Column(db.String(20))

    # Datos del condominio
    condominium_name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    region = db.Column(db.String(100))
    country = db.Column(db.String(50), default="Chile")

    # Posicion en el condominio
    position = db.Column(db.String(50))  # Presidente, Administrador, etc.

    # Detalles adicionales
    units_count = db.Column(db.Integer)
    construction_year = db.Column(db.Integer)
    notes = db.Column(db.Text)

    # Preferencias
    preferred_contact = db.Column(
        db.String(20), default="email"
    )  # email, phone, whatsapp
    preferred_visit_time = db.Column(db.String(50))

    # Estado
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    email_verified_at = db.Column(db.DateTime)

    # Relaciones
    tickets = db.relationship(
        "Ticket",
        backref="client",
        lazy=True,
        foreign_keys="Ticket.client_email",
        primaryjoin="Client.email == Ticket.client_email",
        viewonly=True,
    )

    # Fechas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_contact = db.Column(db.DateTime)

    @property
    def total_tickets(self):
        return len(self.tickets) if self.tickets else 0

    @property
    def open_tickets(self):
        return len([t for t in self.tickets if t.status in ["new", "in_progress"]])

    def get_full_address(self):
        parts = [self.address, self.city, self.region, self.country]
        return ", ".join([p for p in parts if p])

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "condominium_name": self.condominium_name,
            "address": self.address,
            "city": self.city,
            "position": self.position,
            "units_count": self.units_count,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Client {self.name} - {self.condominium_name}>"
