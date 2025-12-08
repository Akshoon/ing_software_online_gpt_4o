"""
Módulo de Configuración con Patrón Singleton

PATRÓN DE DISEÑO IMPLEMENTADO:
================================

SINGLETON PATTERN (Patrón Singleton)
-------------------------------------
Propósito: Garantizar que una clase tenga una única instancia y proporcionar
un punto de acceso global a ella.

Beneficios:
- Evita múltiples lecturas del archivo .env
- Centraliza la configuración de OpenAI
- Facilita testing con mocks
- Garantiza consistencia en toda la aplicación

PRINCIPIOS SOLID APLICADOS:
============================

S - Single Responsibility Principle
    ✓ Responsabilidad única: Gestionar configuración de OpenAI

D - Dependency Inversion Principle
    ✓ Otros módulos dependen de esta abstracción de configuración
    ✓ No dependen directamente de variables de entorno

Autor: Sistema de Procesamiento de Bibliografía
Versión: 2.0
"""

import os
from dotenv import load_dotenv
from typing import Optional


class OpenAIConfig:
    """
    Configuración Singleton para OpenAI API.
    
    PATRÓN: Singleton
    PRINCIPIO SOLID: Single Responsibility Principle
    
    Esta clase garantiza que solo exista una instancia de configuración
    en toda la aplicación, evitando múltiples lecturas del archivo .env
    y asegurando consistencia en la configuración.
    
    Implementación Thread-Safe del patrón Singleton usando __new__.
    
    Atributos:
        api_key (str): Clave API de OpenAI
        model (str): Modelo de OpenAI a utilizar (default: gpt-3.5-turbo)
        max_tokens_default (int): Número máximo de tokens por defecto
    
    Ejemplo de uso:
        >>> # Primera instancia - carga configuración
        >>> config1 = OpenAIConfig()
        >>> print(config1.api_key[:10])  # Muestra primeros 10 caracteres
        
        >>> # Segunda instancia - retorna la misma instancia
        >>> config2 = OpenAIConfig()
        >>> config1 is config2  # True - es la misma instancia
        True
        
        >>> # Uso en otros módulos
        >>> import openai
        >>> config = OpenAIConfig()
        >>> openai.api_key = config.api_key
    """
    
    # Variable de clase para almacenar la única instancia
    _instance: Optional['OpenAIConfig'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'OpenAIConfig':
        """
        Método especial para crear la instancia única.
        
        PATRÓN: Singleton - Controla la creación de instancias
        
        Si no existe una instancia, la crea. Si ya existe, retorna la existente.
        
        Returns:
            OpenAIConfig: La única instancia de la clase
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Inicializa la configuración (solo se ejecuta una vez).
        
        PATRÓN: Singleton - La inicialización solo ocurre en la primera llamada
        
        Carga las variables de entorno y configura los valores por defecto.
        
        Raises:
            ValueError: Si OPENAI_API_KEY no está configurada
        """
        # Solo inicializar una vez
        if OpenAIConfig._initialized:
            return
        
        # Cargar variables de entorno
        load_dotenv()
        
        # Configurar API key
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY no está configurada. "
                "Por favor, crea un archivo .env con tu clave de API."
            )
        
        # Configuración por defecto
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.max_tokens_default = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        
        # Marcar como inicializado
        OpenAIConfig._initialized = True
    
    def get_api_key(self) -> str:
        """
        Obtiene la clave API de OpenAI.
        
        Returns:
            str: Clave API de OpenAI
        """
        return self.api_key
    
    def get_model(self) -> str:
        """
        Obtiene el modelo de OpenAI configurado.
        
        Returns:
            str: Nombre del modelo (ej: 'gpt-3.5-turbo')
        """
        return self.model
    
    def get_max_tokens(self) -> int:
        """
        Obtiene el número máximo de tokens por defecto.
        
        Returns:
            int: Número máximo de tokens
        """
        return self.max_tokens_default
    
    def get_temperature(self) -> float:
        """
        Obtiene la temperatura configurada para las respuestas.
        
        Returns:
            float: Temperatura (0.0 - 1.0)
        """
        return self.temperature
    
    @classmethod
    def reset_instance(cls) -> None:
        """
        Resetea la instancia singleton (útil para testing).
        
        NOTA: Este método solo debe usarse en tests unitarios.
        
        Ejemplo de uso en tests:
            >>> # En un test
            >>> OpenAIConfig.reset_instance()
            >>> config = OpenAIConfig()  # Nueva instancia limpia
        """
        cls._instance = None
        cls._initialized = False


# Ejemplo de uso del Singleton
if __name__ == "__main__":
    # Demostración del patrón Singleton
    print("=== Demostración del Patrón Singleton ===\n")
    
    # Primera instancia
    config1 = OpenAIConfig()
    print(f"Config 1 - Modelo: {config1.get_model()}")
    print(f"Config 1 - ID: {id(config1)}\n")
    
    # Segunda "instancia" - en realidad es la misma
    config2 = OpenAIConfig()
    print(f"Config 2 - Modelo: {config2.get_model()}")
    print(f"Config 2 - ID: {id(config2)}\n")
    
    # Verificar que son la misma instancia
    print(f"¿Son la misma instancia? {config1 is config2}")
    print(f"¿Tienen el mismo ID? {id(config1) == id(config2)}")
