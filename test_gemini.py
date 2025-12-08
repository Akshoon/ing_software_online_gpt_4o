"""
Script de prueba para verificar configuración de Gemini API

Este script te ayudará a diagnosticar problemas con Gemini.
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

print("="*60)
print("VERIFICACIÓN DE GEMINI API")
print("="*60)

# Cargar variables de entorno
load_dotenv()

# Paso 1: Verificar API key
print("\n1. Verificando API Key...")
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("   ✗ No se encontró GEMINI_API_KEY en .env")
    print("   → Agrega GEMINI_API_KEY=tu_clave en el archivo .env")
    exit(1)
else:
    print(f"   ✓ API Key encontrada: {api_key[:10]}...{api_key[-4:]}")

# Configurar Gemini
genai.configure(api_key=api_key)

# Paso 2: Probar modelos disponibles
print("\n2. Probando modelos disponibles...")

modelos_a_probar = [
    ('gemini-pro', 'Modelo estable y confiable'),
    ('gemini-1.5-flash', 'Rápido y económico (recomendado)'),
    ('gemini-2.0-flash', 'Última versión (puede no estar disponible)')
]

modelos_funcionando = []

for modelo_nombre, descripcion in modelos_a_probar:
    try:
        print(f"\n   🔄 Probando {modelo_nombre}...")
        print(f"      ({descripcion})")
        
        modelo = genai.GenerativeModel(modelo_nombre)
        respuesta = modelo.generate_content(
            "Di 'Hola' en una palabra",
            generation_config={'max_output_tokens': 10}
        )
        
        print(f"   ✓ {modelo_nombre} FUNCIONA!")
        print(f"      Respuesta: {respuesta.text}")
        modelos_funcionando.append(modelo_nombre)
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ✗ {modelo_nombre} FALLÓ")
        
        if '429' in error_msg:
            print(f"      Error: Cuota excedida o API key inválida")
        elif '404' in error_msg:
            print(f"      Error: Modelo no encontrado o no disponible en tu región")
        elif '403' in error_msg:
            print(f"      Error: Sin permisos o región restringida")
        else:
            print(f"      Error: {error_msg[:100]}")

# Paso 3: Resumen y recomendaciones
print("\n" + "="*60)
print("RESUMEN")
print("="*60)

if modelos_funcionando:
    print(f"\n✓ {len(modelos_funcionando)} modelo(s) funcionando:")
    for modelo in modelos_funcionando:
        print(f"   - {modelo}")
    
    print("\n📝 RECOMENDACIÓN:")
    if 'gemini-1.5-flash' in modelos_funcionando:
        print("   Usa 'gemini-1.5-flash' (rápido y económico)")
        print("\n   En ai_providers.py línea 149, usa:")
        print("   self.model = genai.GenerativeModel('gemini-1.5-flash')")
    elif 'gemini-pro' in modelos_funcionando:
        print("   Usa 'gemini-pro' (estable)")
        print("\n   En ai_providers.py línea 149, usa:")
        print("   self.model = genai.GenerativeModel('gemini-pro')")
    else:
        print(f"   Usa '{modelos_funcionando[0]}'")
        print(f"\n   En ai_providers.py línea 149, usa:")
        print(f"   self.model = genai.GenerativeModel('{modelos_funcionando[0]}')")
else:
    print("\n✗ Ningún modelo funcionó")
    print("\n📝 POSIBLES SOLUCIONES:")
    print("   1. Verifica que tu API key sea válida en:")
    print("      https://aistudio.google.com/app/apikey")
    print("   2. Genera una nueva API key si es necesario")
    print("   3. Verifica que Gemini esté disponible en tu región")
    print("   4. Usa solo OpenAI (el sistema tiene fallback automático)")
    print("\n   Para usar solo OpenAI, comenta en .env:")
    print("   # GEMINI_API_KEY=...")

print("\n" + "="*60)
