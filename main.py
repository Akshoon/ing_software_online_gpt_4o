"""
Adaptador primario: CLI (Command Line Interface)
Recibe entrada del usuario por consola y delega a los casos de uso.
"""
import os
from dotenv import load_dotenv

from src.infrastructure.database.db import init_db
from src.infrastructure.database.migrate_db import migrate_db
from src.container import (
    build_process_files_use_case,
    build_generate_report_use_case,
    build_notify_careers_use_case,
)

load_dotenv()


def main():
    """Función principal del programa (CLI)."""
    init_db()
    migrate_db()

    print("=" * 60)
    print("PROCESADOR DE BIBLIOGRAFÍA")
    print("=" * 60)

    facultad = input("Selecciona la facultad [Ciencias Sociales]: ") or "Ciencias Sociales"
    carrera = input("Selecciona la carrera [Trabajo Social]: ") or "Trabajo Social"

    directorio = 'archivos/'
    if not os.path.exists(directorio):
        nueva_ruta = input(f"El directorio '{directorio}' no existe. Ingresa ruta: ")
        if nueva_ruta:
            directorio = nueva_ruta

    if os.path.exists(directorio):
        process_use_case = build_process_files_use_case()
        process_use_case.execute(directorio, facultad=facultad, carrera_default=carrera)

        report_use_case = build_generate_report_use_case()
        report_use_case.execute()

        notify_use_case = build_notify_careers_use_case()
        notify_use_case.execute()
    else:
        print("Error: El directorio no existe.")


if __name__ == '__main__':
    main()
