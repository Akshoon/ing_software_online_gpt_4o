"""
Módulo de Construcción de Prompts con Patrón Builder

PATRÓN DE DISEÑO IMPLEMENTADO:
================================

BUILDER PATTERN (Patrón Constructor)
-------------------------------------
Propósito: Separar la construcción de un objeto complejo de su representación,
permitiendo que el mismo proceso de construcción pueda crear diferentes representaciones.

Beneficios:
- Construcción fluida y legible de prompts complejos
- Reutilización de componentes de prompts
- Facilita testing y mantenimiento
- Permite crear diferentes tipos de prompts con el mismo builder

PRINCIPIOS SOLID APLICADOS:
============================

S - Single Responsibility Principle
    ✓ Cada método del builder tiene una responsabilidad específica
    ✓ Separación entre construcción y representación

O - Open/Closed Principle
    ✓ Fácil agregar nuevos tipos de prompts sin modificar código existente

Autor: Sistema de Procesamiento de Bibliografía
Versión: 2.0
"""

from typing import Optional, List, Dict


class PromptBuilder:
    """
    Constructor fluido para prompts de OpenAI.
    
    PATRÓN: Builder (Constructor)
    PRINCIPIO SOLID: Single Responsibility Principle
    
    Permite construir prompts complejos de manera fluida y legible,
    facilitando la reutilización y el mantenimiento.
    
    Ejemplo de uso:
        >>> builder = PromptBuilder()
        >>> prompt = (builder
        ...     .set_task("Extraer bibliografía")
        ...     .add_instruction("Diferencia entre libros y artículos web")
        ...     .set_output_format("JSON")
        ...     .add_context("Texto del PDF")
        ...     .build())
    """
    
    def __init__(self):
        """
        Inicializa el builder con valores por defecto.
        
        PATRÓN: Builder - Inicializa el estado interno del constructor
        """
        self._task: Optional[str] = None
        self._instructions: List[str] = []
        self._output_format: Optional[str] = None
        self._context: Optional[str] = None
        self._examples: List[Dict[str, str]] = []
        self._constraints: List[str] = []
    
    def set_task(self, task: str) -> 'PromptBuilder':
        """
        Establece la tarea principal del prompt.
        
        PATRÓN: Builder - Método fluido que retorna self
        
        Args:
            task (str): Descripción de la tarea principal
            
        Returns:
            PromptBuilder: self para encadenamiento fluido
            
        Ejemplo:
            >>> builder.set_task("Extraer información bibliográfica")
        """
        self._task = task
        return self
    
    def add_instruction(self, instruction: str) -> 'PromptBuilder':
        """
        Agrega una instrucción al prompt.
        
        PATRÓN: Builder - Método fluido que retorna self
        
        Args:
            instruction (str): Instrucción específica
            
        Returns:
            PromptBuilder: self para encadenamiento fluido
            
        Ejemplo:
            >>> builder.add_instruction("Diferencia entre libros y artículos")
        """
        self._instructions.append(instruction)
        return self
    
    def set_output_format(self, format_type: str, schema: Optional[str] = None) -> 'PromptBuilder':
        """
        Establece el formato de salida esperado.
        
        PATRÓN: Builder - Método fluido que retorna self
        
        Args:
            format_type (str): Tipo de formato (JSON, Markdown, etc.)
            schema (str, optional): Esquema del formato si aplica
            
        Returns:
            PromptBuilder: self para encadenamiento fluido
            
        Ejemplo:
            >>> builder.set_output_format("JSON", '{"author": "...", "title": "..."}')
        """
        self._output_format = f"Formato: {format_type}"
        if schema:
            self._output_format += f"\nEsquema: {schema}"
        return self
    
    def add_context(self, context: str, max_length: Optional[int] = None) -> 'PromptBuilder':
        """
        Agrega contexto al prompt.
        
        PATRÓN: Builder - Método fluido que retorna self
        
        Args:
            context (str): Texto de contexto
            max_length (int, optional): Longitud máxima del contexto
            
        Returns:
            PromptBuilder: self para encadenamiento fluido
            
        Ejemplo:
            >>> builder.add_context(texto_documento, max_length=1000)
        """
        if max_length and len(context) > max_length:
            self._context = context[:max_length] + "..."
        else:
            self._context = context
        return self
    
    def add_example(self, input_example: str, output_example: str) -> 'PromptBuilder':
        """
        Agrega un ejemplo de entrada/salida.
        
        PATRÓN: Builder - Método fluido que retorna self
        
        Args:
            input_example (str): Ejemplo de entrada
            output_example (str): Ejemplo de salida esperada
            
        Returns:
            PromptBuilder: self para encadenamiento fluido
            
        Ejemplo:
            >>> builder.add_example(
            ...     "Martuccelli, D. (2007)",
            ...     '{"author": "Danilo Martuccelli", "year": "2007"}'
            ... )
        """
        self._examples.append({
            "input": input_example,
            "output": output_example
        })
        return self
    
    def add_constraint(self, constraint: str) -> 'PromptBuilder':
        """
        Agrega una restricción o regla.
        
        PATRÓN: Builder - Método fluido que retorna self
        
        Args:
            constraint (str): Restricción a aplicar
            
        Returns:
            PromptBuilder: self para encadenamiento fluido
            
        Ejemplo:
            >>> builder.add_constraint("No incluir referencias sin año")
        """
        self._constraints.append(constraint)
        return self
    
    def build(self) -> str:
        """
        Construye el prompt final.
        
        PATRÓN: Builder - Método final que construye el producto
        
        Returns:
            str: Prompt completo y formateado
            
        Raises:
            ValueError: Si falta información esencial (task)
            
        Ejemplo:
            >>> prompt = builder.build()
            >>> print(prompt)
        """
        if not self._task:
            raise ValueError("Debe establecer una tarea con set_task()")
        
        # Construir el prompt
        parts = []
        
        # Tarea principal
        parts.append(f"TAREA: {self._task}\n")
        
        # Instrucciones
        if self._instructions:
            parts.append("INSTRUCCIONES:")
            for i, instruction in enumerate(self._instructions, 1):
                parts.append(f"{i}. {instruction}")
            parts.append("")
        
        # Restricciones
        if self._constraints:
            parts.append("RESTRICCIONES:")
            for constraint in self._constraints:
                parts.append(f"- {constraint}")
            parts.append("")
        
        # Ejemplos
        if self._examples:
            parts.append("EJEMPLOS:")
            for i, example in enumerate(self._examples, 1):
                parts.append(f"Ejemplo {i}:")
                parts.append(f"  Entrada: {example['input']}")
                parts.append(f"  Salida: {example['output']}")
            parts.append("")
        
        # Formato de salida
        if self._output_format:
            parts.append(self._output_format)
            parts.append("")
        
        # Contexto
        if self._context:
            parts.append("CONTEXTO:")
            parts.append(self._context)
        
        return "\n".join(parts)
    
    def reset(self) -> 'PromptBuilder':
        """
        Resetea el builder para construir un nuevo prompt.
        
        PATRÓN: Builder - Permite reutilizar el builder
        
        Returns:
            PromptBuilder: self para encadenamiento fluido
            
        Ejemplo:
            >>> builder.reset().set_task("Nueva tarea")
        """
        self.__init__()
        return self


# Prompts predefinidos usando el Builder
class BibliographyPrompts:
    """
    Colección de prompts predefinidos para bibliografía.
    
    PATRÓN: Factory Method - Métodos estáticos que crean prompts específicos
    
    Proporciona prompts comunes ya configurados, evitando duplicación
    y asegurando consistencia.
    """
    
    @staticmethod
    def extract_bibliography(text: str) -> str:
        """
        Crea prompt para extraer bibliografía.
        
        Args:
            text (str): Texto del documento
            
        Returns:
            str: Prompt configurado
        """
        return (PromptBuilder()
            .set_task("Extraer bibliografía del siguiente texto")
            .add_instruction("Diferencia entre libros y artículos web")
            .add_instruction("Si tiene URL → es artículo web (type='article')")
            .add_instruction("Si tiene editorial → es libro (type='book')")
            .set_output_format("JSON", """{
  "basic": [{"author": "...", "year": "...", "title": "...", "type": "..."}],
  "complementary": [...]
}""")
            .add_context(text, max_length=3000)
            .build())
    
    @staticmethod
    def normalize_entry(author: str, title: str) -> str:
        """
        Crea prompt para normalizar entrada bibliográfica.
        
        Args:
            author (str): Autor a normalizar
            title (str): Título a normalizar
            
        Returns:
            str: Prompt configurado
        """
        return (PromptBuilder()
            .set_task("Normalizar entrada bibliográfica")
            .add_instruction("Formato de autor: 'Nombre Apellido'")
            .add_instruction("Expandir iniciales a nombres completos")
            .add_instruction("Título en Title Case")
            .add_example(
                "D. Martuccelli",
                '{"normalized_author": "Danilo Martuccelli"}'
            )
            .set_output_format("JSON", '{"normalized_author": "...", "normalized_title": "..."}')
            .add_context(f"Autor: {author}\nTítulo: {title}")
            .build())


# Ejemplo de uso
if __name__ == "__main__":
    print("=== Demostración del Patrón Builder ===\n")
    
    # Construcción fluida de un prompt
    builder = PromptBuilder()
    prompt = (builder
        .set_task("Extraer información bibliográfica")
        .add_instruction("Identifica autor, año y título")
        .add_instruction("Diferencia entre libros y artículos")
        .add_constraint("No incluir referencias sin año")
        .add_example(
            "Martuccelli, D. (2007). Cambio de rumbo.",
            '{"author": "Danilo Martuccelli", "year": "2007", "title": "Cambio de rumbo"}'
        )
        .set_output_format("JSON")
        .add_context("Texto de ejemplo...")
        .build())
    
    print(prompt)
    print("\n" + "="*50 + "\n")
    
    # Uso de prompt predefinido
    prompt2 = BibliographyPrompts.extract_bibliography("Texto del documento...")
    print("Prompt predefinido:")
    print(prompt2[:200] + "...")
