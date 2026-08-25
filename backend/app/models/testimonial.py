from app.extensions import db
from datetime import datetime


class Testimonial(db.Model):
    __tablename__ = "testimonials"

    id = db.Column(db.Integer, primary_key=True)

    # Datos del cliente
    client_name = db.Column(db.String(100), nullable=False)
    client_position = db.Column(db.String(100))
    client_avatar = db.Column(db.String(200))
    condominium_name = db.Column(db.String(200))

    # Contenido
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)

    # Imagen de referencia
    image_before = db.Column(db.String(200))
    image_after = db.Column(db.String(200))

    # Servicio relacionado
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=True)
    service_name = db.Column(db.String(100))  # Denormalizado para evitar joins

    # Estado
    is_approved = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)

    # Metadatos
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    approved_at = db.Column(db.DateTime)

    @property
    def rating_stars(self):
        """Retornar estrellas como texto"""
        return "\u2605" * self.rating + "\u2606" * (5 - self.rating)

    @property
    def client_initials(self):
        """Iniciales del cliente"""
        if not self.client_name:
            return "??"
        parts = self.client_name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        return self.client_name[:2].upper()

    def approve(self):
        self.is_approved = True
        self.approved_at = datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "client_name": self.client_name,
            "client_position": self.client_position,
            "condominium_name": self.condominium_name,
            "content": self.content,
            "rating": self.rating,
            "rating_stars": self.rating_stars,
            "service_name": self.service_name,
            "is_approved": self.is_approved,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Testimonial {self.client_name} - {self.rating} stars>"
