"""
Caso de uso: NotifyCareersUseCase
Notifica a las carreras sobre títulos disponibles.
"""
from src.domain.ports.repository_ports import AdquisicionRepositoryPort


class NotifyCareersUseCase:
    """Notifica a las carreras sobre títulos con estado 'disponible'."""

    def __init__(self, adquisicion_repo: AdquisicionRepositoryPort):
        self._adquisicion_repo = adquisicion_repo

    def execute(self) -> None:
        """Imprime notificaciones de disponibilidad por carrera."""
        adquisiciones = self._adquisicion_repo.get_all_available()
        for adq in adquisiciones:
            titulo = adq.titulo
            carreras = [asig.carrera.name for asig in titulo.asignaturas]
            print(
                f"Notificando a las carreras {carreras} sobre el título disponible: "
                f"{titulo.normalized_title}"
            )
