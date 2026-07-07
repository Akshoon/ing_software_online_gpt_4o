"""
Módulo de compatibilidad hacia atrás (backward compatibility shim).

ARQUITECTURA HEXAGONAL: Este módulo es un shim de compatibilidad.
La lógica real vive ahora en:
  - src/domain/use_cases/process_files_use_case.py
  - src/domain/use_cases/generate_report_use_case.py
  - src/domain/use_cases/notify_careers_use_case.py

Este archivo mantiene la interfaz pública original para no romper tests u
otros módulos que aún lo importen directamente.
"""
from src.container import (
    build_process_files_use_case,
    build_generate_report_use_case,
    build_notify_careers_use_case,
)


def procesar_archivos(directorio, facultad='Ciencias Sociales', carrera_default='Trabajo Social'):
    """Procesa todos los archivos soportados en el directorio. (Shim de compatibilidad)"""
    use_case = build_process_files_use_case()
    use_case.execute(directorio, facultad=facultad, carrera_default=carrera_default)
    generar_reportes()
    notificar_carreras()


def procesar_pdfs(directorio_pdf, facultad='Ciencias Sociales', carrera_default='Trabajo Social'):
    """Alias para procesar_archivos. (Shim de compatibilidad)"""
    return procesar_archivos(directorio_pdf, facultad, carrera_default)


def generar_reportes():
    """Genera el reporte CSV. (Shim de compatibilidad)"""
    use_case = build_generate_report_use_case()
    return use_case.execute()


def notificar_carreras():
    """Notifica a las carreras. (Shim de compatibilidad)"""
    use_case = build_notify_careers_use_case()
    use_case.execute()


def importar_csv(ruta_csv):
    """Importa datos desde CSV. (Shim de compatibilidad)"""
    from src.container import build_import_csv_use_case
    use_case = build_import_csv_use_case()
    use_case.execute(ruta_csv)
