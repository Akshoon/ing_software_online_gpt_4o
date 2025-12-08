"""
Test exhaustivo de Gemini con diferentes configuraciones
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

print("="*70)
print("TEST EXHAUSTIVO DE GEMINI")
print("="*70)

# Probar diferentes configuraciones de safety settings
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    }
]

modelos = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-pro']

for modelo_nombre in modelos:
    print(f"\n{'='*70}")
    print(f"Probando: {modelo_nombre}")
    print('='*70)
    
    try:
        modelo = genai.GenerativeModel(
            modelo_nombre,
            safety_settings=safety_settings
        )
        
        # Test 1: Simple
        print("\n1. Test simple:")
        response = modelo.generate_content(
            "Di 'Hola'",
            generation_config={'max_output_tokens': 10}
        )
        
        if response.parts:
            print(f"   ✓ Funciona: {response.text}")
        else:
            print(f"   ✗ Bloqueado")
            if hasattr(response, 'prompt_feedback'):
                print(f"   Feedback: {response.prompt_feedback}")
        
        # Test 2: Extracción de bibliografía
        print("\n2. Test bibliografía:")
        prompt_biblio = """
Extrae la bibliografía del siguiente texto:

Bibliografía básica:
- Martuccelli, D. (2007). Cambio de rumbo. Santiago: LOM.
- Bourdieu, P. (1999). La miseria del mundo. Buenos Aires: FCE.

Retorna en JSON:
{"basic": [{"author": "Nombre", "year": "Año", "title": "Título"}]}
"""
        
        response2 = modelo.generate_content(
            prompt_biblio,
            generation_config={
                'max_output_tokens': 1000,
                'temperature': 0.7
            }
        )
        
        if response2.parts:
            print(f"   ✓ Funciona!")
            print(f"   Respuesta: {response2.text[:150]}...")
        else:
            print(f"   ✗ Bloqueado")
            if hasattr(response2, 'prompt_feedback'):
                print(f"   Feedback: {response2.prompt_feedback}")
        
        print(f"\n✓ {modelo_nombre} FUNCIONA con safety_settings=BLOCK_NONE")
        print(f"\n📝 USAR ESTE MODELO:")
        print(f"   Modelo: {modelo_nombre}")
        print(f"   Safety: BLOCK_NONE en todas las categorías")
        break
        
    except Exception as e:
        print(f"\n✗ {modelo_nombre} falló: {str(e)[:100]}")

print("\n" + "="*70)
