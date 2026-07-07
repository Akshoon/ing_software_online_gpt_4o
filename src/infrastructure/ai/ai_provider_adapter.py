"""
Adaptador de infraestructura: AIProviderAdapter
Implementa AIProviderPort usando el AIProviderFactory existente.
"""
from typing import Tuple

from src.domain.ports.ai_port import AIProviderPort
from src.services.ai_providers import AIProviderFactory


class AIProviderAdapter(AIProviderPort):
    """
    Adaptador que envuelve el AIProviderFactory existente e implementa
    el puerto de dominio AIProviderPort.
    """

    def __init__(self, factory: AIProviderFactory = None):
        if factory is None:
            factory = AIProviderFactory(load_balance=True)
        self._factory = factory

    def generate(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Genera texto usando el proveedor con balanceo de carga."""
        provider = self._factory.get_provider()
        return provider.generate_completion(prompt, max_tokens, temperature)

    def generate_with_fallback(self, prompt: str, max_tokens: int = 2000,
                               temperature: float = 0.7) -> Tuple[str, str]:
        """Genera con fallback automático entre proveedores."""
        return self._factory.generate_with_fallback(prompt, max_tokens, temperature)

    def generate_with_provider(self, provider_name: str, prompt: str,
                               max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Genera usando un proveedor específico por nombre."""
        provider = self._factory.get_provider(provider_name)
        return provider.generate_completion(prompt, max_tokens, temperature)
