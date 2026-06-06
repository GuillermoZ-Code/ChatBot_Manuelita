"""Utilidades para cargar variables de entorno desde .env."""

from pathlib import Path
import os

from dotenv import load_dotenv


def load_environment() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path, override=False)


def read_env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def read_env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}