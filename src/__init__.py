"""
Paquete src — Arquitectura Hexagonal (Ports & Adapters)

Estructura:
  domain/       — Núcleo: entidades puras, puertos (interfaces), casos de uso
  infrastructure/ — Adaptadores secundarios: DB, AI, Scraper, FileExtractor, Report
  services/     — Implementaciones originales (reutilizadas por adaptadores de infraestructura)
  config/       — Configuración singleton
  container.py  — Composition root (ensamblaje de dependencias)
  gui.py        — Adaptador primario GUI (tkinter)
  processor.py  — Shim de compatibilidad hacia atrás
  database/     — Shims de compatibilidad hacia atrás
  models/       — Shims de compatibilidad hacia atrás
"""
