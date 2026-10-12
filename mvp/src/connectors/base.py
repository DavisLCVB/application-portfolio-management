"""
Clase base abstracta para los conectores federados multimodales del APM.

Define la interfaz común que deben implementar todos los conectores de ingesta:
- Verificación de compatibilidad de formato (can_handle).
- Extracción de evidencias estructuradas (extract), devolviendo instancias
  de EvidenciaTecnica, EvidenciaContractual o EvidenciaDiagrama con trazabilidad.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List, Union


class BaseConnector(ABC):
    """
    Clase base para todos los conectores de fuentes multimodales.
    """

    name: str = "BaseConnector"
    supported_extensions: List[str] = []

    def can_handle(self, path: Union[str, Path]) -> bool:
        """
        Determina si el conector puede procesar el archivo o ruta dada.
        Por defecto verifica si la extensión coincide con las soportadas.
        """
        p = Path(path)
        if p.is_dir():
            return False
        return p.suffix.lower() in [ext.lower() for ext in self.supported_extensions]

    @abstractmethod
    def extract(self, path: Union[str, Path]) -> List[Any]:
        """
        Extrae evidencias estructuradas del archivo o recurso proporcionado.
        
        Returns:
            Lista de objetos de evidencia canónicos:
            EvidenciaTecnica, EvidenciaContractual o EvidenciaDiagrama.
        """
        raise NotImplementedError
