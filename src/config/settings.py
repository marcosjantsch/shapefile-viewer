from __future__ import annotations

import os
from pathlib import Path

PLATFORM_ADMIN = "platform_admin"
COMPANY_ADMIN = "company_admin"
EMPLOYEE = "employee"

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "src" / "assets"
APP_DATA_PATH = DATA_DIR / "app_data.json"
APP_LOGO_PATH = ASSETS_DIR / "logo.png" if (ASSETS_DIR / "logo.png").exists() else ASSETS_DIR / "seg365_logo.svg"
LOCAL_VIDEO_DIR_CANDIDATES = (
    BASE_DIR / "Videos",
    BASE_DIR / "videos",
)
SUPPORTED_VIDEO_EXTENSIONS = (
    ".mp4",
    ".mov",
    ".m4v",
    ".webm",
    ".avi",
    ".mkv",
)

APP_TITLE = "SEG365 | Videos Diarios de Seguranca"
APP_VERSION = "MVP 1.0"
APP_ICON = "🛡️"
APP_SUBTITLE = "Treinamentos obrigatorios, rastreabilidade e administracao por perfil."

LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

DEFAULT_STORAGE_MODE = os.getenv("SEG_APP_STORAGE_MODE", "local_json")
GOOGLE_PROJECT_ID = os.getenv("SEG_GOOGLE_PROJECT_ID", "")
GOOGLE_STORAGE_BUCKET = os.getenv("SEG_GOOGLE_STORAGE_BUCKET", "segurancastorege")
GOOGLE_VIDEO_BUCKET = os.getenv("SEG_GOOGLE_VIDEO_BUCKET", GOOGLE_STORAGE_BUCKET)
VIDEO_LIBRARY_SOURCE = os.getenv("SEG_VIDEO_LIBRARY_SOURCE", "both").strip().casefold()
FIREBASE_CREDENTIALS_PATH = os.getenv("SEG_FIREBASE_CREDENTIALS_PATH", "")
DEFAULT_SUPPORT_PASSWORD = os.getenv("SEG_DEFAULT_SUPPORT_PASSWORD", "Seg365@123")

DATE_FORMAT = "%d/%m/%Y"
DATETIME_FORMAT = "%d/%m/%Y %H:%M"

COLLECTIONS = (
    "users",
    "companies",
    "employees",
    "platform_videos",
    "company_videos",
    "video_assignments",
    "billing_records",
    "safety_images",
    "image_assignments",
)

PROFILE_LABELS = {
    PLATFORM_ADMIN: "Administrador da plataforma",
    COMPANY_ADMIN: "Administrador de videos",
    EMPLOYEE: "Colaborador",
}

ASSIGNMENT_STATUS_LABELS = {
    "pending": "Pendente",
    "completed": "Concluido",
}

BILLING_STATUS_LABELS = {
    "pending": "Pendente",
    "paid": "Pago",
}

VIDEO_ORIGIN_LABELS = {
    "platform": "Biblioteca da plataforma",
    "company": "Biblioteca da empresa",
}

DEMO_LOGIN_HINTS = {
    PLATFORM_ADMIN: {"username": "plataforma.master", "password": "Seg365@123"},
    COMPANY_ADMIN: {"username": "admin.videos", "password": "Video365@123"},
    EMPLOYEE: {"username": "carlos.silva", "password": "Seg365@123"},
}
