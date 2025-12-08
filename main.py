import os
from dotenv import load_dotenv
from src.processor import procesar_archivos

# Cargar variables de entorno
load_dotenv()

def main():
    """Función principal del programa (CLI)."""
    print("="*60)
    print("PROCESADOR DE BIBLIOGRAFÍA")
    print("="*60)
    
    facultad = input("Selecciona la facultad [Ciencias Sociales]: ") or "Ciencias Sociales"
    carrera = input("Selecciona la carrera [Trabajo Social]: ") or "Trabajo Social"
    
    directorio = 'archivos/'
    if not os.path.exists(directorio):
        nueva_ruta = input(f"El directorio '{directorio}' no existe. Ingresa ruta: ")
        if nueva_ruta:
            directorio = nueva_ruta
    
    if os.path.exists(directorio):
        procesar_archivos(directorio, facultad=facultad, carrera_default=carrera)
    else:
        print("Error: El directorio no existe.")

if __name__ == '__main__':
    main()
