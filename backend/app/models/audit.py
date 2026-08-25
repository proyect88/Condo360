from app.extensions import db
from datetime import datetime


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)

    # Informacion del usuario
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user_email = db.Column(db.String(120))
    user_ip = db.Column(db.String(50))

    # Accion realizada
    action = db.Column(
        db.String(50), nullable=False
    )  # create, update, delete, login, etc.
    resource_type = db.Column(
        db.String(50), nullable=False
    )  # service, ticket, user, etc.
    resource_id = db.Column(db.Integer)
    resource_name = db.Column(db.String(200))

    # Detalles
    changes = db.Column(db.JSON)  # Cambios realizados
    metadata_extra = db.Column("metadata", db.JSON)  # Metadatos adicionales

    # Fechas
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AuditLog {self.action} {self.resource_type} by {self.user_email}>"
