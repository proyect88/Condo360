import re


def validate_email(email):
    """Validar formato de email"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """Validar número de teléfono chileno"""
    # Eliminar espacios, guiones y paréntesis
    phone = re.sub(r"[\s\-\(\)]", "", phone)
    # Validar formato +569XXXXXXXX o 9XXXXXXXX
    pattern = r"^(\+56)?9\d{8}$"
    return re.match(pattern, phone) is not None


def validate_url(url):
    """Validar URL"""
    pattern = r"^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$"
    return re.match(pattern, url) is not None


def validate_rut(rut):
    """Validar RUT chileno"""
    rut = rut.replace(".", "").replace("-", "")
    if not rut[:-1].isdigit():
        return False

    dv = rut[-1]
    rut = rut[:-1]
    reversed_rut = rut[::-1]
    total = 0
    multiplier = 2

    for digit in reversed_rut:
        total += int(digit) * multiplier
        multiplier += 1
        if multiplier == 8:
            multiplier = 2

    digit_sum = 11 - (total % 11)
    expected_dv = str(digit_sum)

    if digit_sum == 10:
        expected_dv = "K"
    elif digit_sum == 11:
        expected_dv = "0"

    return dv.upper() == expected_dv


def validate_password_strength(password):
    """Validar fortaleza de contraseña"""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if not re.search(r"[A-Z]", password):
        return False, "Debe contener al menos una mayúscula"
    if not re.search(r"[a-z]", password):
        return False, "Debe contener al menos una minúscula"
    if not re.search(r"\d", password):
        return False, "Debe contener al menos un número"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Debe contener al menos un carácter especial"
    return True, "Contraseña segura"
