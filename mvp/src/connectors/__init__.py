"""
Capa de Conectores Federados Multimodales para APM.

Proporciona interfaces y conectores para ingesta de datos desde:
- Repositorios de código fuente (CodeToCatalogConnector)
- Contratos y especificaciones TDR (ContractMinerConnector)
- Hojas de cálculo y catálogos tabulares (SpreadsheetConnector: .csv, .xlsx)
- Presentaciones ejecutivas y de arquitectura (PresentationConnector: .pptx)
- Diagramas y modelos técnicos (DiagramConnector: .puml, .drawio, .archimate, .xml)
"""

from .base import BaseConnector
from .diagram_connector import DiagramConnector
from .presentation_connector import PresentationConnector
from .registry import (
    CodeToCatalogConnector,
    ConnectorRegistry,
    ContractMinerConnector,
)
from .spreadsheet_connector import SpreadsheetConnector

__all__ = [
    "BaseConnector",
    "SpreadsheetConnector",
    "PresentationConnector",
    "DiagramConnector",
    "CodeToCatalogConnector",
    "ContractMinerConnector",
    "ConnectorRegistry",
]
