"""
Adaptador de infraestructura: CsvReportAdapter
Implementa ReportPort generando reportes en formato CSV con pandas.
"""
import os
from datetime import datetime
from typing import List, Dict

import pandas as pd

from src.domain.ports.report_port import ReportPort


class CsvReportAdapter(ReportPort):
    """
    Genera reportes en formato CSV e implementa ReportPort.
    Encapsula toda la lógica de pandas y filesystem.
    """

    DEFAULT_FILENAME = 'reporte_bibliografia.csv'

    def generate(self, data: List[Dict]) -> str:
        """
        Genera el CSV y retorna la ruta del archivo generado.

        Args:
            data: Lista de diccionarios con las filas del reporte

        Returns:
            Ruta al archivo CSV generado
        """
        df = pd.DataFrame(data)
        nombre_archivo = self.DEFAULT_FILENAME

        try:
            if os.path.exists(nombre_archivo):
                try:
                    os.remove(nombre_archivo)
                except PermissionError:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    nombre_archivo = f'reporte_bibliografia_{timestamp}.csv'

            df.to_csv(nombre_archivo, index=False, sep=';', encoding='utf-8-sig')
            print(f"[OK] Reporte generado exitosamente: {nombre_archivo}")
            return nombre_archivo
        except Exception as e:
            print(f"[ERROR] Error generando reporte: {e}")
            raise
