"""
Estrategias de Proveedores de IA con Patrón Strategy

PATRÓN DE DISEÑO IMPLEMENTADO:
================================

STRATEGY PATTERN (Patrón Estrategia)
-------------------------------------
Propósito: Permitir cambiar entre diferentes proveedores de IA (OpenAI, Gemini)
de manera transparente, facilitando balanceo de carga y fallback.

Beneficios:
- Distribuye carga entre múltiples APIs
- Fallback automático si una API falla
- Fácil agregar nuevos proveedores
- Reduce costos al usar múltiples proveedores

PRINCIPIOS SOLID APLICADOS:
============================

S - Single Responsibility Principle (Principio de Responsabilidad Única)
    - Cada estrategia maneja un proveedor específico

O - Open/Closed Principle (Principio Abierto/Cerrado)
    - Fácil agregar nuevos proveedores sin modificar código existente

D - Dependency Inversion Principle (Principio de Inversión de Dependencias)
    - Código depende de abstracción (AIProviderStrategy)

Autor: Sistema de Procesamiento de Bibliografía
Versión: 2.1 (con soporte multi-proveedor)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import openai
import google.generativeai as genai
from src.config import OpenAIConfig
import random


class AIProviderStrategy(ABC):
    """
    Interfaz abstracta para proveedores de IA.
    
    PATRÓN: Strategy
    PRINCIPIO: Interface Segregation Principle (Principio de Segregación de Interfaces)
    
    Define el contrato que todos los proveedores deben implementar.
    """
    
    @abstractmethod
    def generate_completion(self, prompt: str, max_tokens: int = 2000, 
                          temperature: float = 0.7) -> str:
        """
        Genera una respuesta usando el proveedor de IA.
        
        Args:
            prompt: Texto del prompt
            max_tokens: Número máximo de tokens
            temperature: Temperatura (0.0 - 1.0)
            
        Returns:
            str: Respuesta generada
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Retorna el nombre del proveedor."""
        pass


class OpenAIStrategy(AIProviderStrategy):
    """
    Estrategia para OpenAI API.
    
    PATRÓN: Strategy (Estrategia Concreta)
    PRINCIPIO: Single Responsibility (Responsabilidad Única)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: API key de OpenAI (opcional, usa config si no se provee)
        """
        if api_key:
            self.api_key = api_key
        else:
            config = OpenAIConfig()
            self.api_key = config.get_api_key()
        
        openai.api_key = self.api_key
    
    def generate_completion(self, prompt: str, max_tokens: int = 2000,
                          temperature: float = 0.7) -> str:
        """
        Genera respuesta usando OpenAI.
        
        Args:
            prompt: Texto del prompt
            max_tokens: Número máximo de tokens
            temperature: Temperatura
            
        Returns:
            str: Respuesta de OpenAI
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            raise Exception(f"Error en OpenAI: {str(e)}")
    
    def get_provider_name(self) -> str:
        return "OpenAI"


class GeminiStrategy(AIProviderStrategy):
    """
    Estrategia para Google Gemini API.
    
    PATRÓN: Strategy (Estrategia Concreta)
    PRINCIPIO: Single Responsibility
    
    Usa Gemini 1.5 Flash para respuestas rápidas y eficientes.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: API key de Gemini (opcional, usa config si no se provee)
        """
        if api_key:
            self.api_key = api_key
        else:
            config = OpenAIConfig()
            # Intentar obtener de variable de entorno
            import os
            self.api_key = os.getenv('GEMINI_API_KEY')
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY no está configurada")
        
        genai.configure(api_key=self.api_key)
        
        # Usar modelo específico solicitado
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    def generate_completion(self, prompt: str, max_tokens: int = 2000,
                          temperature: float = 0.7) -> str:
        """
        Genera respuesta usando Gemini con reintentos para rate limits.
        """
        import time
        
        max_retries = 3
        base_delay = 2  # Reduced base delay for retries
        
        # Rate Limiter proactivo eliminado a petición del usuario
        # print("⏳ Esperando 8s para respetar cuota de Gemini (8 RPM)...")
        # time.sleep(8)
        
        for attempt in range(max_retries):
            try:
                generation_config = {
                    'temperature': temperature,
                    'max_output_tokens': max_tokens,
                }
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                # Verificar si la respuesta está bloqueada o vacía
                if not response.parts:
                    feedback = "N/A"
                    if hasattr(response, 'prompt_feedback'):
                        feedback = str(response.prompt_feedback)
                    raise Exception(f"Respuesta bloqueada o vacía. Feedback: {feedback}")
                
                # Intentar acceder al texto
                try:
                    return response.text
                except ValueError as e:
                    if hasattr(response, 'prompt_feedback'):
                        raise Exception(f"Contenido bloqueado: {response.prompt_feedback}")
                    raise Exception(f"No se pudo obtener texto: {str(e)}")
                    
            except Exception as e:
                error_str = str(e)
                # Verificar si es un error de cuota o rate limit (429)
                if "429" in error_str or "TooManyRequests" in error_str or "quota" in error_str.lower():
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff: 2, 4, 8...
                        print(f"[WARN] Rate limit en Gemini. Reintentando en {delay}s... (Intento {attempt+1}/{max_retries})")
                        time.sleep(delay)
                        continue
                
                # Si no es rate limit o se acabaron los intentos, propagar error
                raise Exception(f"Error en Gemini: {str(e)}")
    
    def get_provider_name(self) -> str:
        return "Gemini"


class AIProviderFactory:
    """
    Factory para crear y gestionar proveedores de IA.
    
    PATRÓN: Factory + Strategy
    PRINCIPIO: Single Responsibility
    
    Características:
    - Balanceo de carga entre proveedores
    - Fallback automático si un proveedor falla
    - Configuración flexible
    """
    
    def __init__(self, providers: Optional[Dict[str, AIProviderStrategy]] = None,
                 load_balance: bool = True):
        """
        Args:
            providers: Diccionario de proveedores disponibles
            load_balance: Si True, alterna entre proveedores
        """
        if providers is None:
            # Inicializar proveedores por defecto
            self.providers = {}
            
            # Intentar inicializar OpenAI
            try:
                self.providers['openai'] = OpenAIStrategy()
                print("[OK] OpenAI configurado")
            except Exception as e:
                print(f"[WARN] OpenAI no disponible: {e}")
            
            # Intentar inicializar Gemini
            try:
                self.providers['gemini'] = GeminiStrategy()
                print("[OK] Gemini configurado")
            except Exception as e:
                print(f"[WARN] Gemini no disponible: {e}")
        else:
            self.providers = providers
        
        if not self.providers:
            raise ValueError("No hay proveedores de IA disponibles")
        
        self.load_balance = load_balance
        self.current_provider_index = 0
        self.provider_keys = list(self.providers.keys())
    
    def get_provider(self, provider_name: Optional[str] = None) -> AIProviderStrategy:
        """
        Obtiene un proveedor específico o uno balanceado.
        
        Args:
            provider_name: Nombre del proveedor ('openai', 'gemini')
                          Si es None, usa balanceo de carga
        
        Returns:
            AIProviderStrategy: Proveedor seleccionado
        """
        if provider_name:
            if provider_name not in self.providers:
                raise ValueError(f"Proveedor '{provider_name}' no disponible")
            return self.providers[provider_name]
        
        # Balanceo de carga round-robin
        if self.load_balance and len(self.providers) > 1:
            provider_key = self.provider_keys[self.current_provider_index]
            self.current_provider_index = (self.current_provider_index + 1) % len(self.provider_keys)
            print(f"[INFO] Usando proveedor: {provider_key}")
            return self.providers[provider_key]
        
        # Usar el primer proveedor disponible
        return list(self.providers.values())[0]
    
    def generate_with_fallback(self, prompt: str, max_tokens: int = 2000,
                               temperature: float = 0.7,
                               preferred_provider: Optional[str] = None) -> tuple[str, str]:
        """
        Genera respuesta con fallback automático.
        
        Intenta con el proveedor preferido, si falla prueba con otros.
        
        Args:
            prompt: Texto del prompt
            max_tokens: Número máximo de tokens
            temperature: Temperatura
            preferred_provider: Proveedor preferido (opcional)
        
        Returns:
            tuple: (respuesta, nombre_proveedor_usado)
        """
        # Determinar orden de proveedores a intentar
        if preferred_provider and preferred_provider in self.providers:
            providers_to_try = [preferred_provider] + [
                k for k in self.provider_keys if k != preferred_provider
            ]
        else:
            providers_to_try = self.provider_keys.copy()
            if self.load_balance:
                random.shuffle(providers_to_try)
        
        last_error = None
        
        # Intentar con cada proveedor
        for provider_name in providers_to_try:
            try:
                provider = self.providers[provider_name]
                print(f"[INFO] Intentando con {provider.get_provider_name()}...")
                response = provider.generate_completion(prompt, max_tokens, temperature)
                print(f"[OK] Respuesta exitosa de {provider.get_provider_name()}")
                return response, provider_name
            except Exception as e:
                last_error = e
                print(f"[ERROR] Error con {provider_name}: {str(e)[:100]}")
                continue
        
        # Si todos fallaron
        raise Exception(f"Todos los proveedores fallaron. Último error: {last_error}")


# Ejemplo de uso
if __name__ == "__main__":
    print("=== Demostración de AI Provider Strategy ===\n")
    
    # Crear factory con balanceo de carga
    factory = AIProviderFactory(load_balance=True)
    
    # Ejemplo 1: Usar proveedor específico
    print("\n1. Usando OpenAI específicamente:")
    try:
        provider = factory.get_provider('openai')
        response = provider.generate_completion("Di 'Hola' en 3 palabras", max_tokens=50)
        print(f"Respuesta: {response}\n")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Ejemplo 2: Balanceo de carga automático
    print("2. Balanceo de carga automático:")
    for i in range(3):
        try:
            provider = factory.get_provider()
            print(f"  Solicitud {i+1}: {provider.get_provider_name()}")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Ejemplo 3: Fallback automático
    print("\n3. Fallback automático:")
    try:
        response, provider_used = factory.generate_with_fallback(
            "Di 'Hola mundo' en 5 palabras",
            max_tokens=50
        )
        print(f"Proveedor usado: {provider_used}")
        print(f"Respuesta: {response}")
    except Exception as e:
        print(f"Error: {e}")
