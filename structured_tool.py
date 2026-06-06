"""Acceso determinista a datos estructurados de Manuelita."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from settings import STRUCTURED_DATA_FILE


def load_structured_data() -> Dict[str, Any]:
    path = Path(STRUCTURED_DATA_FILE)
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _contains_any(text: str, terms: List[str]) -> bool:
    return any(term in text for term in terms)


def _format_value(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{k}: {v}" for k, v in value.items())
    return str(value)


def classify_structured_intent(query: str) -> Optional[str]:
    q = _normalize(query)

    rules = {
        "todos_los_contactos": [
            "contacto", "contactos", "como contactar", "informacion de contacto",
            "datos de contacto", "medios de contacto", "formas de contactar"
        ],
        "telefono_centro_corporativo": [
            "telefono", "pbx", "numero", "llamar", "linea telefonica", "contacto telefonico"
        ],
        "correo_servicio_cliente": [
            "correo", "email", "mail", "correo electronico", "servicio al cliente"
        ],
        "horarios_contacto": [
            "horario", "horarios", "atencion", "atienden", "hora laboral", "horas de atencion"
        ],
        "direccion_centro_corporativo": [
            "direccion", "ubicacion", "oficina", "centro corporativo", "donde quedan", "donde estan"
        ],
        "sedes_colombia": [
            "sedes", "oficinas", "sedes colombia", "presencia en colombia", "donde tienen sedes"
        ],
        "productos_o_plataformas": [
            "productos", "que productos", "cuales productos", "que ofrece", "que venden",
            "portafolio", "lineas de negocio", "plataformas de negocio", "que comercializan"
        ],
        "contacto_productos_pqrs": [
            "pqrs", "pqr", "reclamo", "queja", "peticion", "solicitud",
            "inconveniente con producto", "problema con producto"
        ],
        "NIT": [
            "nit", "registro tributario", "identificacion tributaria", "ruc"
        ],
        "canal_contacto": [
            "formulario de contacto", "contactarlos", "canal de contacto", "pagina de contacto"
        ],
        "mision": [
            "mision", "cual es la mision", "proposito de la empresa", "para que existe"
        ],
        "vision": [
            "vision", "cual es la vision", "hacia donde va", "futuro de la empresa"
        ],
        "valores": [
            "valores", "cuales son los valores", "principios", "cultura organizacional"
        ],
        "proposito_superior": [
            "proposito", "proposito superior", "razon de ser", "para que existe manuelita"
        ],
        "año_fundacion": [
            "cuando fue fundada", "año de fundacion", "cuando se fundo", "en que año nacio"
        ],
        "fundador": [
            "quien fundo", "fundador", "quien creo", "quien inicio", "quien establecio"
        ],
        "años_trayectoria": [
            "cuantos anos tiene", "trayectoria", "anos de historia", "cuanto tiempo lleva"
        ],
        "sector": [
            "a que sector pertenece", "sector", "industria", "tipo de empresa"
        ],
        "presencia_geografica": [
            "donde opera", "presencia", "paises", "en que paises", "operaciones internacionales"
        ],
        "mercados_exportacion": [
            "exporta", "exportacion", "mercados internacionales", "a cuantos paises", "vende en el mundo"
        ],
        "presidente": [
            "presidente", "quien dirige", "quien es el ceo", "lider", "director general"
        ],
        "sostenibilidad": [
            "sostenibilidad", "informe de sostenibilidad", "esg", "medio ambiente", "equidad de genero"
        ],
        "empleabilidad": [
            "empleo", "empleabilidad", "emprendimiento", "ruta emprendedora", "oportunidades laborales"
        ],
        "pagina_empleo": [
            "trabaja con nosotros", "convocatoria", "vacante", "como aplicar", "ofertas de empleo"
        ],
        "sitio_web": [
            "pagina web", "sitio web", "pagina oficial", "web", "url"
        ],
    }

    for key, keywords in rules.items():
        if _contains_any(q, keywords):
            return key

    return None


def get_structured_answer(query: str, data: Dict[str, Any]) -> Optional[str]:
    if not data:
        return None

    key = classify_structured_intent(query)
    if not key:
        return None

    value = data.get(key)
    if value in (None, "", [], {}):
        return None

    return _format_value(value)
