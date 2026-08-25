import re
import secrets
import string
from datetime import datetime


def slugify(text):
    """Convertir texto a slug"""
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text.strip("-")


def generate_random_string(length=16):
    """Generar cadena aleatoria"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_secure_token(length=32):
    """Generar token seguro"""
    return secrets.token_urlsafe(length)


def format_currency(amount, currency="CLP"):
    """Formatear cantidad como moneda"""
    if amount is None:
        return "$0"

    if currency == "CLP":
        return f"${int(amount):,}".replace(",", ".")
    elif currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "EUR":
        return f"{amount:,.2f} €"
    else:
        return f"{amount:,.2f}"


def format_date(date, format="%d/%m/%Y %H:%M"):
    """Formatear fecha"""
    if not date:
        return "N/A"
    if isinstance(date, str):
        date = datetime.fromisoformat(date)
    return date.strftime(format)


def truncate_text(text, length=100, suffix="..."):
    """Truncar texto"""
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[:length].strip() + suffix


def sanitize_html(text):
    """Sanitizar HTML básico"""
    import html

    if not text:
        return ""
    return html.escape(text)


def json_serialize(obj):
    """Serializar objeto para JSON"""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return str(obj)
