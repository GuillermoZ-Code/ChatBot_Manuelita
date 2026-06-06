"""Prompt dinámico para el agente avanzado."""

from __future__ import annotations

from typing import Any, Dict

from settings import SYSTEM_PROMPT_TEMPLATE


def dynamic_prompt(
    history: str,
    user_profile: Dict[str, Any],
    extra: str = "",
    critical_mode: bool = False,
) -> str:
    profile_text = (
        "\n".join(f"- {k}: {v}" for k, v in user_profile.items())
        if user_profile
        else "Sin perfil persistente guardado."
    )

    extra_block = extra or "Sin instrucciones extra."
    if critical_mode:
        extra_block += (
            "\nModo crítico: si la consulta implica aprobación, escalamiento, "
            "acciones sensibles, reclamos formales o decisiones ambiguas, "
            "solicita revisión humana antes de dar una instrucción definitiva."
        )

    return SYSTEM_PROMPT_TEMPLATE.format(
        history=f"{history}\n\nPerfil persistente del usuario:\n{profile_text}",
        extra=extra_block,
    )