"""
Script de prueba para Gemini con manejo de errores mejorado
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

print("="*60)
print("TEST GEMINI CON MANEJO DE ERRORES")
print("="*60)

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
print(f"\n✓ API Key: {api_key[:10]}...{api_key[-4:]}")

genai.configure(api_key=api_key)

# Probar con el modelo configurado
modelo_nombre = 'gemini-2.5-flash'
print(f"\n🔄 Probando {modelo_nombre}...")

try:
    modelo = genai.GenerativeModel(modelo_nombre)
    
    # Test 1: Prompt simple
    print("\n1. Test simple:")
    response = modelo.generate_content(
        "Di 'Hola' en una palabra",
        generation_config={'max_output_tokens': 10}
    )
    
    # Verificar respuesta
    if not response.parts:
        print("   ✗ Respuesta bloqueada o vacía")
        print(f"   Feedback: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'}")
    else:
        try:
            print(f"   ✓ Respuesta: {response.text}")
        except ValueError as e:
            print(f"   ✗ Error accediendo a texto: {e}")
    
    # Test 2: Prompt más complejo (bibliografía)
    print("\n2. Test con bibliografía:")
    prompt_biblio = """
Extrae la bibliografía del siguiente texto:

Bibliografía básica:
- Martuccelli, D. (2007). Cambio de rumbo. Santiago: LOM.
- Bourdieu, P. (1999). La miseria del mundo. Buenos Aires: FCE.

Retorna en JSON:
{"basic": [{"author": "...", "year": "...", "title": "..."}]}
"""
    
    response2 = modelo.generate_content(
        prompt_biblio,
        generation_config={'max_output_tokens': 500, 'temperature': 0.7}
    )
    
    if not response2.parts:
        print("   ✗ Respuesta bloqueada o vacía")
        if hasattr(response2, 'prompt_feedback'):
            print(f"   Feedback: {response2.prompt_feedback}")
    else:
        try:
            print(f"   ✓ Respuesta: {response2.text[:200]}...")
        except ValueError as e:
            print(f"   ✗ Error accediendo a texto: {e}")
            
    print("\n✓ Gemini funcionando correctamente")
    
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    print("\nSoluciones:")
    print("1. Verifica que el modelo 'gemini-2.5-flash' esté disponible")
    print("2. Prueba con 'gemini-2.5-flash-lite'")
    print("3. Usa solo OpenAI (el sistema tiene fallback)")

print("\n" + "="*60)
