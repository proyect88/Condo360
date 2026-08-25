from app.extensions import db
from datetime import datetime


class Diagnostic(db.Model):
    __tablename__ = "diagnostics"

    id = db.Column(db.Integer, primary_key=True)
    diagnostic_token = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # Datos del condominio
    condominium_name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(200))
    units_count = db.Column(db.Integer)
    building_age = db.Column(db.Integer)
    construction_type = db.Column(db.String(50))  # hormigon, albanileria, etc.

    # Diagnostico
    issues = db.Column(db.JSON)  # Lista de problemas detectados
    urgency_score = db.Column(db.Integer, default=0)
    priority_areas = db.Column(db.JSON)  # Areas prioritarias

    # Servicio recomendado
    recommended_service_id = db.Column(
        db.Integer, db.ForeignKey("services.id"), nullable=True
    )

    # Datos de contacto
    client_name = db.Column(db.String(100))
    client_email = db.Column(db.String(120))
    client_phone = db.Column(db.String(20))
    contact_preference = db.Column(db.String(20), default="email")

    # Estatus
    status = db.Column(
        db.String(20), default="draft"
    )  # draft, pending, reviewed, contacted

    # Metadatos
    completed_steps = db.Column(db.JSON)  # Steps completados
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(50))

    # Fechas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    reviewed_at = db.Column(db.DateTime)
    contacted_at = db.Column(db.DateTime)

    # Relaciones
    recommended_service = db.relationship(
        "Service", foreign_keys=[recommended_service_id], lazy=True
    )

    def __init__(self, **kwargs):
        super(Diagnostic, self).__init__(**kwargs)
        if not self.diagnostic_token:
            self.diagnostic_token = self.generate_token()

    def generate_token(self):
        import secrets

        return secrets.token_hex(16)

    @property
    def urgency_label(self):
        if self.urgency_score >= 8:
            return "Crítica"
        elif self.urgency_score >= 6:
            return "Alta"
        elif self.urgency_score >= 4:
            return "Media"
        else:
            return "Baja"

    @property
    def issue_count(self):
        return len(self.issues) if self.issues else 0

    def add_issue(self, issue):
        if not self.issues:
            self.issues = []
        self.issues.append(issue)
        self.updated_at = datetime.utcnow()

    def calculate_urgency(self):
        """Calcular puntaje de urgencia basado en los issues"""
        if not self.issues:
            return 0

        scores = {
            "fugas_agua": 8,
            "problemas_electricos": 7,
            "estructural": 9,
            "ascensor": 7,
            "humedad": 5,
            "jardineria": 3,
            "cosmetico": 2,
        }

        total_score = sum(scores.get(issue.get("type", ""), 3) for issue in self.issues)
        self.urgency_score = min(total_score // len(self.issues), 10)
        return self.urgency_score

    def to_dict(self):
        return {
            "id": self.id,
            "diagnostic_token": self.diagnostic_token,
            "condominium_name": self.condominium_name,
            "building_age": self.building_age,
            "issues": self.issues,
            "urgency_score": self.urgency_score,
            "urgency_label": self.urgency_label,
            "recommended_service_id": self.recommended_service_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<Diagnostic {self.diagnostic_token} - {self.condominium_name}>"
