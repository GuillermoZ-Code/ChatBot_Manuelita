"""Utilidades para cargar variables de entorno desde .env."""

from pathlib import Path
import os

from dotenv import load_dotenv


def load_environment() -> None:
    """Carga variables de entorno desde un archivo .env si existe."""
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path, override=False)


def read_env(name: str, default: str = "") -> str:
    """Obtiene una variable de entorno de forma segura."""
    return os.getenv(name, default)
