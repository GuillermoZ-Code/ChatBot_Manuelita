"""Acceso determinista a datos estructurados de Manuelita."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from settings import STRUCTURED_DATA_FILE


def load_structured_data() -> Dict[str, Any]:
    """Carga el archivo de datos estructurados desde disco."""
    path = Path(STRUCTURED_DATA_FILE)
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def get_structured_answer(query: str, data: Dict[str, Any]) -> Optional[str]:
    """Busca una respuesta exacta o semánticamente guiada en datos fijos."""
    q = query.lower().strip()
    rules = {
        "telefono_centro_corporativo": [
            "telefono", "teléfono", "pbx", "número", "numero", "llamar", "contacto",
        ],
        "correo_servicio_cliente": [
            "correo", "email", "e-mail", "mail", "servicio al cliente",
        ],
        "horarios_contacto": [
            "horario", "horarios", "atención", "atienden", "hora laboral",
        ],
        "direccion_centro_corporativo": [
            "direccion", "dirección", "ubicacion", "ubicación", "oficina", "centro corporativo",
        ],
        "sedes_colombia": ["sedes", "oficinas", "sedes en colombia"],
        "linea_productos_contacto": ["productos", "reclamo", "pqrs", "pqr"],
        "NIT": ["nit", "ruc", "registro tributario"],
    }

    for key, keywords in rules.items():
        if any(keyword in q for keyword in keywords):
            value = data.get(key)
            if value:
                if isinstance(value, list):
                    return "\n".join(f"- {item}" for item in value)
                return str(value)
    return None
