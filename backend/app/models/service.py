from app.extensions import db
from datetime import datetime
import re
import unicodedata


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.String(200))
    icon = db.Column(db.String(50))  # FontAwesome class
    image_url = db.Column(db.String(200))
    price_from = db.Column(db.Numeric(10, 2))
    category = db.Column(db.String(50), index=True)
    features = db.Column(db.JSON)  # Lista de caracteristicas
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relaciones
    testimonials = db.relationship("Testimonial", backref="service", lazy=True)
    diagnostic_recommendations = db.relationship(
        "Diagnostic",
        foreign_keys="Diagnostic.recommended_service_id",
        viewonly=True,
        lazy=True,
    )

    def __init__(self, **kwargs):
        super(Service, self).__init__(**kwargs)
        if not self.slug and self.name:
            self.slug = self.generate_slug(self.name)

    @staticmethod
    def generate_slug(text):
        """Generar slug desde texto"""
        text = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        text = re.sub(r"[^\w\s-]", "", text.lower())
        return re.sub(r"[-\s]+", "-", text).strip("-")

    @property
    def feature_list(self):
        """Retornar lista de caracteristicas"""
        if isinstance(self.features, list):
            return self.features
        return []

    @property
    def category_label(self):
        """Retornar etiqueta legible de categoria"""
        labels = {
            "albanileria": "Albañilería",
            "plomeria": "Plomería",
            "electricidad": "Electricidad",
            "jardineria": "Jardinería",
            "ascensores": "Ascensores",
            "gestion": "Gestión de Mantenimiento",
        }
        return labels.get(self.category, (self.category or "").capitalize())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "short_description": self.short_description,
            "icon": self.icon,
            "image_url": self.image_url,
            "price_from": float(self.price_from) if self.price_from else None,
            "category": self.category,
            "features": self.feature_list,
            "is_active": self.is_active,
            "is_featured": self.is_featured,
            "order": self.order,
        }

    def __repr__(self):
        return f"<Service {self.name}>"
