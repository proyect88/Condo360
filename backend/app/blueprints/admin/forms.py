from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    DecimalField,
    SelectField,
    BooleanField,
    IntegerField,
    PasswordField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    Optional,
    NumberRange,
    ValidationError,
)
from app.models.user import User


class ServiceForm(FlaskForm):
    name = StringField(
        "Nombre del Servicio", validators=[DataRequired(), Length(max=100)]
    )
    description = TextAreaField("Descripción Completa", validators=[DataRequired()])
    short_description = StringField("Descripción Corta", validators=[Length(max=200)])
    icon = StringField("Icono (FontAwesome)", validators=[Optional()])
    category = SelectField(
        "Categoría",
        choices=[
            ("albanileria", "Albañilería"),
            ("plomeria", "Plomería"),
            ("electricidad", "Electricidad"),
            ("jardineria", "Jardinería"),
            ("ascensores", "Ascensores"),
            ("gestion", "Gestión de Mantenimiento"),
        ],
        validators=[DataRequired()],
    )
    price_from = DecimalField("Precio Desde", validators=[Optional()], places=2)
    features = TextAreaField("Características (separadas por coma)")
    is_active = BooleanField("Activo")
    is_featured = BooleanField("Destacado")
    order = IntegerField(
        "Orden", validators=[Optional(), NumberRange(min=0)], default=0
    )


class TicketForm(FlaskForm):
    client_name = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    client_email = StringField("Email", validators=[DataRequired(), Email()])
    client_phone = StringField("Teléfono", validators=[Optional()])
    condominium_name = StringField("Condominio", validators=[Optional()])
    service_type = SelectField(
        "Tipo de Servicio",
        choices=[
            ("general", "General"),
            ("albanileria", "Albañilería"),
            ("plomeria", "Plomería"),
            ("electricidad", "Electricidad"),
            ("jardineria", "Jardinería"),
            ("ascensores", "Ascensores"),
            ("diagnostico_integral", "Diagnóstico Integral"),
        ],
        validators=[DataRequired()],
    )
    description = TextAreaField("Descripción", validators=[DataRequired()])
    urgency = SelectField(
        "Urgencia",
        choices=[
            ("low", "Baja"),
            ("medium", "Media"),
            ("high", "Alta"),
            ("critical", "Crítica"),
        ],
        validators=[DataRequired()],
    )
    address = StringField("Dirección", validators=[Optional()])


class TestimonialForm(FlaskForm):
    client_name = StringField(
        "Nombre del Cliente", validators=[DataRequired(), Length(max=100)]
    )
    client_position = StringField("Cargo", validators=[Optional(), Length(max=100)])
    condominium_name = StringField(
        "Nombre del Condominio", validators=[Optional(), Length(max=200)]
    )
    content = TextAreaField("Testimonio", validators=[DataRequired()])
    rating = SelectField(
        "Calificación",
        choices=[(str(i), f"{i} Estrellas") for i in range(1, 6)],
        validators=[DataRequired()],
    )
    service_id = SelectField(
        "Servicio Relacionado", choices=[], validators=[Optional()], coerce=str
    )
    is_approved = BooleanField("Aprobado")
    is_featured = BooleanField("Destacado")


class UserForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    full_name = StringField(
        "Nombre Completo", validators=[DataRequired(), Length(max=100)]
    )
    password = PasswordField("Contraseña", validators=[Length(min=8)])
    role = SelectField(
        "Rol",
        choices=[
            ("admin", "Administrador"),
            ("staff", "Staff"),
            ("viewer", "Solo Lectura"),
        ],
        validators=[DataRequired()],
    )
    is_active = BooleanField("Activo")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Este email ya está registrado.")
