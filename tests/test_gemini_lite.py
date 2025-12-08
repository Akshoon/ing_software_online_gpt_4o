"""
Test rápido para gemini-2.5-flash-lite
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

print("="*60)
print("TEST: gemini-2.5-flash-lite")
print("="*60)

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
print(f"\n✓ API Key: {api_key[:10]}...{api_key[-4:]}")

genai.configure(api_key=api_key)

try:
    print("\n🔄 Probando gemini-2.5-flash-lite...")
    modelo = genai.GenerativeModel('gemini-2.5-flash-lite')
    respuesta = modelo.generate_content(
        "Di 'Hola' en una palabra",
        generation_config={'max_output_tokens': 10}
    )
    
    print("✓ ¡FUNCIONA!")
    print(f"Respuesta: {respuesta.text}")
    print("\n📝 Usa este modelo en ai_providers.py línea 149:")
    print("   self.model = genai.GenerativeModel('gemini-2.5-flash-lite')")
    
except Exception as e:
    print(f"✗ FALLÓ: {str(e)}")
    print("\nPrueba con otros modelos o usa solo OpenAI")

print("\n" + "="*60)
