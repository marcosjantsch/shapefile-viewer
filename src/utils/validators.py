from __future__ import annotations

from src.utils.formatters import only_digits


def validate_required(value: str | None, label: str) -> str | None:
    if str(value or "").strip():
        return None
    return f"O campo '{label}' e obrigatorio."


def validate_email(value: str | None, label: str = "E-mail") -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if "@" in text and "." in text.split("@")[-1]:
        return None
    return f"{label} invalido."


def validate_cnpj(value: str | None) -> str | None:
    digits = only_digits(value)
    if not digits:
        return None
    if len(digits) != 14:
        return "CNPJ deve conter 14 digitos."
    return None


def validate_document(value: str | None, label: str) -> str | None:
    if not value:
        return None
    digits = only_digits(value)
    if len(digits) < 5:
        return f"{label} precisa ter ao menos 5 digitos ou caracteres uteis."
    return None


def validate_password_for_creation(value: str | None) -> str | None:
    if not value:
        return "Defina uma senha inicial para o acesso."
    if len(str(value)) < 8:
        return "A senha deve ter pelo menos 8 caracteres."
    return None
