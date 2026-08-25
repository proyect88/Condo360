import os
import uuid
from datetime import datetime

from app import db


class ServiceImage(db.Model):
    """Imagen de la galeria de trabajos realizados de un servicio."""

    __tablename__ = "service_images"

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(
        db.Integer, db.ForeignKey("services.id"), nullable=False, index=True
    )
    # Ruta relativa a frontend/static (ej: uploads/servicios/abc123.jpg)
    image_path = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(200))
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    service = db.relationship(
        "Service", backref=db.backref("gallery_images", lazy="dynamic")
    )

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    MAX_IMAGES_PER_SERVICE = 10

    @property
    def url(self):
        return f"/static/{self.image_path}"

    @staticmethod
    def allowed_file(filename):
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in ServiceImage.ALLOWED_EXTENSIONS
        )

    @staticmethod
    def generate_filename(original_filename):
        ext = original_filename.rsplit(".", 1)[1].lower()
        return f"{uuid.uuid4().hex[:12]}.{ext}"

    def delete_file(self, uploads_root):
        filepath = os.path.join(uploads_root, os.path.basename(self.image_path))
        if os.path.exists(filepath):
            os.remove(filepath)

    def to_dict(self):
        return {
            "id": self.id,
            "service_id": self.service_id,
            "url": self.url,
            "caption": self.caption,
            "order": self.order,
            "is_active": self.is_active,
        }
