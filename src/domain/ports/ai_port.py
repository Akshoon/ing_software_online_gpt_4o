"""
Puerto de salida: AIProviderPort
Define la interfaz que el dominio usa para comunicarse con cualquier proveedor de IA.
"""
from abc import ABC, abstractmethod
from typing import Tuple


class AIProviderPort(ABC):
    """Puerto de salida para generación de completions de IA."""

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Genera texto dado un prompt. Retorna el string de respuesta."""
        ...

    @abstractmethod
    def generate_with_fallback(self, prompt: str, max_tokens: int = 2000,
                               temperature: float = 0.7) -> Tuple[str, str]:
        """Genera con fallback automático. Retorna (respuesta, nombre_proveedor)."""
        ...

    @abstractmethod
    def generate_with_provider(self, provider_name: str, prompt: str,
                               max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Genera usando un proveedor específico por nombre."""
        ...
