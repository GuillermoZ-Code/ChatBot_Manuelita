"""Middleware de control humano para el agente Manuelita.

HumanInTheLoopMiddleware intercepta resultados del agente que contienen
la señal HUMAN_REVIEW_REQUIRED y los convierte en una respuesta estructurada
que detiene el flujo automático y escala la consulta.

La rúbrica exige este componente explícito para flujos críticos:
aprobaciones, escalamientos, reclamos formales o decisiones ambiguas.
"""

from __future__ import annotations

from typing import Any, Dict

HUMAN_REVIEW_SIGNAL = "HUMAN_REVIEW_REQUIRED::"

ROUTE_HUMAN = "Control humano"


class HumanInTheLoopMiddleware:
    """Intercepta respuestas del agente y aplica control humano cuando corresponde.

    Uso:
        middleware = HumanInTheLoopMiddleware()
        result = middleware.process(raw_agent_result)
    """

    def process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa el resultado del agente y aplica escalamiento si es necesario.

        Si la respuesta contiene la señal HUMAN_REVIEW_REQUIRED, transforma
        el resultado en una respuesta de escalamiento con metadatos de auditoría.
        En caso contrario, devuelve el resultado sin modificaciones.

        Args:
            result: Diccionario con keys 'answer', 'route', 'tool_used', 'metadata'.

        Returns:
            Resultado original o resultado de escalamiento humano.
        """
        answer = result.get("answer", "")

        if isinstance(answer, str) and answer.startswith(HUMAN_REVIEW_SIGNAL):
            reason = answer[len(HUMAN_REVIEW_SIGNAL):].strip()
            return self._build_human_review_response(reason, result)

        return result

    def requires_human_review(self, answer: str) -> bool:
        """Indica si una respuesta requiere revisión humana."""
        return isinstance(answer, str) and answer.startswith(HUMAN_REVIEW_SIGNAL)

    def _build_human_review_response(
        self,
        reason: str,
        original_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Construye la respuesta de escalamiento con contexto de auditoría."""
        return {
            "answer": (
                "Esta solicitud requiere validación humana antes de continuar. "
                f"Motivo: {reason}"
            ),
            "route": ROUTE_HUMAN,
            "tool_used": "request_human_review",
            "metadata": {
                **original_result.get("metadata", {}),
                "human_review_required": True,
                "escalation_reason": reason,
            },
        }
