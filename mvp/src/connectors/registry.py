"""
Registro y orquestador de conectores federados multimodales (ConnectorRegistry).

Permite registrar e invocar automáticamente conectores especializados para
diversas fuentes de verdad (código, contratos, hojas de cálculo, presentaciones,
diagramas), inspeccionando directorios y abstrayendo la multimodalidad.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from ..code_to_catalog import CodeToCatalogExtractor
from ..contract_miner import ContractMiner
from ..models import EvidenciaContractual, EvidenciaDiagrama, EvidenciaTecnica
from .base import BaseConnector
from .diagram_connector import DiagramConnector
from .presentation_connector import PresentationConnector
from .spreadsheet_connector import SpreadsheetConnector


class CodeToCatalogConnector(BaseConnector):
    """Adaptador de BaseConnector para el extractor Code-to-Catalog."""

    name: str = "CodeToCatalogConnector"
    supported_extensions: List[str] = [".pom", ".json", ".dockerfile"]

    def __init__(self):
        self._extractor = CodeToCatalogExtractor()

    def can_handle(self, path: Union[str, Path]) -> bool:
        p = Path(path)
        if p.is_dir():
            # Es un repositorio si contiene pom.xml, package.json o Dockerfile
            return (
                (p / "pom.xml").is_file()
                or (p / "package.json").is_file()
                or (p / "Dockerfile").is_file()
                or (p / ".git").is_dir()
            )
        if p.is_file():
            return p.name.lower() in ["pom.xml", "package.json", "dockerfile"]
        return False

    def extract(self, path: Union[str, Path]) -> List[EvidenciaTecnica]:
        p = Path(path)
        repo_dir = p.parent if p.is_file() else p
        ev = self._extractor.extract(str(repo_dir))
        return [ev]


class ContractMinerConnector(BaseConnector):
    """Adaptador de BaseConnector para el minero de contratos y Dark Data."""

    name: str = "ContractMinerConnector"
    supported_extensions: List[str] = [".md", ".txt"]

    def __init__(self):
        self._miner = ContractMiner()

    def can_handle(self, path: Union[str, Path]) -> bool:
        p = Path(path)
        if not p.is_file():
            return False
        # Maneja archivos de texto/markdown que sean TDRs o contengan patrones contractuales
        if p.suffix.lower() in self.supported_extensions:
            # Si el nombre sugiere TDR/contrato o está en carpetas de contratos
            name_lower = p.name.lower()
            if "tdr" in name_lower or "contrato" in name_lower or "contract" in name_lower:
                return True
            if "contract" in str(p).lower() or "contrato" in str(p).lower():
                return True
            # Inspección rápida de contenido
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    snippet = f.read(512).lower()
                    if any(k in snippet for k in ["términos de referencia", "tdr", "contratista", "proveedor", "sla", "cláusula"]):
                        return True
            except Exception:
                pass
        return False

    def extract(self, path: Union[str, Path]) -> List[EvidenciaContractual]:
        p = Path(path)
        ev = self._miner.extract(str(p))
        return [ev]


class ConnectorRegistry:
    """
    Registro federado central de conectores multimodales de descubrimiento.
    """

    def __init__(self, register_defaults: bool = True):
        self._connectors: List[BaseConnector] = []
        if register_defaults:
            self._register_defaults()

    def _register_defaults(self) -> None:
        """Registra los conectores estándar del sistema."""
        self.register(SpreadsheetConnector())
        self.register(PresentationConnector())
        self.register(DiagramConnector())
        self.register(CodeToCatalogConnector())
        self.register(ContractMinerConnector())

    def register(self, connector: BaseConnector) -> None:
        """Registra un nuevo conector en el registry."""
        self._connectors.append(connector)

    @property
    def registered_connectors(self) -> List[BaseConnector]:
        """Devuelve la lista de conectores actualmente registrados."""
        return list(self._connectors)

    def get_connector_for(self, path: Union[str, Path]) -> Optional[BaseConnector]:
        """
        Busca el primer conector que declare soporte para el recurso dado.
        """
        p = Path(path)
        for conn in self._connectors:
            if conn.can_handle(p):
                return conn
        return None

    def scan_file(self, file_path: Union[str, Path]) -> List[Any]:
        """
        Detecta el conector apropiado para un archivo y ejecuta la extracción.
        """
        p = Path(file_path)
        conn = self.get_connector_for(p)
        if conn:
            return conn.extract(p)
        return []

    def scan_directory(
        self, dir_path: Union[str, Path], recursive: bool = True
    ) -> List[Any]:
        """
        Escanea recursivamente un directorio identificando fuentes de información,
        detectando repositorios de código enteros o archivos individuales.
        """
        root = Path(dir_path)
        if not root.is_dir():
            raise NotADirectoryError(f"Ruta no es un directorio válido: {dir_path}")

        evidences: List[Any] = []
        visited_dirs = set()

        # 1. Comprobar primero si directorios inmediatos son repositorios de código
        # para evitar procesar archivos internos individualmente
        for child in root.iterdir():
            if child.is_dir():
                code_conn = next((c for c in self._connectors if isinstance(c, CodeToCatalogConnector)), None)
                if code_conn and code_conn.can_handle(child):
                    try:
                        evs = code_conn.extract(child)
                        evidences.extend(evs)
                        visited_dirs.add(child.resolve())
                    except Exception:
                        pass

        # 2. Recorrer archivos restantes
        pattern = "**/*" if recursive else "*"
        for path in root.glob(pattern):
            if path.is_file():
                # Verificar que no pertenezca a un directorio de repo ya procesado
                if any(v in path.resolve().parents for v in visited_dirs):
                    continue

                conn = self.get_connector_for(path)
                if conn:
                    try:
                        extracted = conn.extract(path)
                        evidences.extend(extracted)
                    except Exception:
                        continue

        return evidences

    @staticmethod
    def partition_evidences(evidences: List[Any]) -> Dict[str, List[Any]]:
        """
        Agrupa una lista heterogénea de evidencias por su tipo canónico.
        """
        partition: Dict[str, List[Any]] = {
            "tecnica": [],
            "contractual": [],
            "diagrama": [],
            "otros": [],
        }
        for ev in evidences:
            if isinstance(ev, EvidenciaTecnica):
                partition["tecnica"].append(ev)
            elif isinstance(ev, EvidenciaContractual):
                partition["contractual"].append(ev)
            elif isinstance(ev, EvidenciaDiagrama):
                partition["diagrama"].append(ev)
            else:
                partition["otros"].append(ev)
        return partition
