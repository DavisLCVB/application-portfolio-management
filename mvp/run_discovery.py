#!/usr/bin/env python3
"""
Orquestador CLI del Pipeline de Descubrimiento Continuo Multimodal (MVP 1).

Ejecuta el flujo completo de descubrimiento multi-agente federado:
1. Agente 1: Extracción técnica sobre repositorios (Code-to-Catalog).
2. Agente 2: Minería de documentos y contratos (Dark Data Miner).
3. Conectores Multimodales: Ingesta de diagramas (PlantUML, Archi, draw.io) y catálogos.
4. Agente 3: Reconciliación semántica y scoring (Semantic Reconciliator).
5. Agente 4: Generación de micro-nudges proactivos (Micro-Nudge Generator).
6. Persistencia de borradores de Fact Sheets, micro-nudges y evidencias de diagramas.
7. Renderizado de tablas resumen en consola.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Garantizar que el paquete src sea importable
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.code_to_catalog import CodeToCatalogExtractor
from src.connectors import ConnectorRegistry, DiagramConnector
from src.contract_miner import ContractMiner
from src.models import (
    EvidenciaContractual,
    EvidenciaDiagrama,
    EvidenciaTecnica,
    HipotesisFactSheet,
    MicroNudge,
)
from src.nudge_generator import NudgeGenerator
from src.reconciliator import SemanticReconciliator


def run_pipeline(
    scan_dir: Optional[Union[str, Path]] = None,
    repos_dir: Optional[Union[str, Path]] = None,
    contracts_dir: Optional[Union[str, Path]] = None,
    diagrams_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Ejecuta el pipeline completo de descubrimiento sobre fixtures de prueba,
    un directorio multimodal arbitrario, o rutas específicas de repositorios,
    contratos y diagramas.
    """
    fixtures_dir = BASE_DIR / "fixtures"
    output_dir = BASE_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("================================================================================")
    print("  APM AI Discovery Pipeline - MVP 1 (Multimodal Continuous Discovery & Matching)  ")
    print("================================================================================\n")

    registry = ConnectorRegistry()
    diagram_evidences: List[EvidenciaDiagrama] = []
    tech_evidences: List[EvidenciaTecnica] = []
    contract_evidences: List[EvidenciaContractual] = []

    has_custom_targets = any(x is not None for x in [scan_dir, repos_dir, contracts_dir, diagrams_dir])

    if scan_dir is not None:
        target_path = Path(scan_dir)
        print(f"[Directorio Multimodal] Escaneando fuentes federadas en: {target_path}...")
        extracted_all = registry.scan_directory(target_path)
        partition = registry.partition_evidences(extracted_all)

        tech_evidences = partition["tecnica"]
        contract_evidences = partition["contractual"]
        diagram_evidences = partition["diagrama"]

        print(f"  ✓ Evidencias técnicas encontradas: {len(tech_evidences)}")
        print(f"  ✓ Evidencias contractuales encontradas: {len(contract_evidences)}")
        print(f"  ✓ Diagramas de arquitectura encontrados: {len(diagram_evidences)}")

    elif repos_dir is not None or contracts_dir is not None or diagrams_dir is not None:
        extractor = CodeToCatalogExtractor()
        miner = ContractMiner()
        diag_conn = DiagramConnector()

        # 1. Repositorios de código
        if repos_dir:
            rpath = Path(repos_dir)
            print(f"[1/5] Agente 1: Escaneando repositorios en: {rpath}...")
            # Detectar si el path mismo es un repositorio
            if (rpath / "pom.xml").is_file() or (rpath / "package.json").is_file() or (rpath / ".git").is_dir():
                candidates = [rpath]
            else:
                candidates = [d for d in rpath.iterdir() if d.is_dir() and not d.name.startswith(".")]

            for c in sorted(candidates):
                try:
                    ev = extractor.extract(str(c))
                    tech_evidences.append(ev)
                    print(f"  ✓ Repositorio '{ev.repo_name}': {ev.primary_language} ({ev.runtime_version}), {len(ev.dependencies)} dependencias, {len(ev.endpoints)} endpoints.")
                except Exception:
                    continue

        # 2. Contratos y TDRs
        if contracts_dir:
            cpath = Path(contracts_dir)
            print(f"\n[2/5] Agente 2: Minando contratos y TDRs en: {cpath}...")
            doc_files = sorted(list(cpath.glob("*.md")) + list(cpath.glob("*.txt")))
            for df in doc_files:
                try:
                    cev = miner.extract(str(df))
                    contract_evidences.append(cev)
                    print(f"  ✓ Documento '{cev.doc_id}': Proveedor '{cev.provider_name}', SLA: {cev.sla_uptime}, {len(cev.acquired_licenses)} licencias.")
                except Exception:
                    continue

        # 3. Diagramas de arquitectura
        if diagrams_dir:
            dpath = Path(diagrams_dir)
            print(f"\n[3/5] Capa Multimodal: Ingesta de diagramas en: {dpath}...")
            diag_files = sorted([f for f in dpath.glob("**/*") if f.is_file() and diag_conn.can_handle(f)])
            for df in diag_files:
                try:
                    devs = diag_conn.extract(df)
                    diagram_evidences.extend(devs)
                    for dev in devs:
                        print(f"  ✓ Diagrama '{dev.source_file}' ({dev.format_type}): {len(dev.components)} componentes, {len(dev.relations)} relaciones.")
                except Exception:
                    continue

    else:
        # Modo por defecto: Fixtures canónicos del MVP
        print("[1/5] Agente 1: Ejecutando extracción de código (Code-to-Catalog)...")
        extractor = CodeToCatalogExtractor()
        repo_dirs = [
            fixtures_dir / "repo-recaudacion",
            fixtures_dir / "repo-portal-atencion",
        ]
        for rdir in repo_dirs:
            if rdir.is_dir():
                ev = extractor.extract(str(rdir))
                tech_evidences.append(ev)
                print(f"  ✓ Repositorio '{ev.repo_name}': {ev.primary_language} ({ev.runtime_version}), {len(ev.dependencies)} dependencias, {len(ev.endpoints)} endpoints.")

        # 2. Agente 2: Dark Data Miner
        print("\n[2/5] Agente 2: Ejecutando minería de Dark Data y TDRs (Dark Data Miner)...")
        miner = ContractMiner()
        contracts_dir_path = fixtures_dir / "contracts"
        contract_files = [
            contracts_dir_path / "tdr-recaudacion-digital.md",
            contracts_dir_path / "tdr-portal-ciudadano.md",
        ]
        for cfile in contract_files:
            if cfile.is_file():
                cev = miner.extract(str(cfile))
                contract_evidences.append(cev)
                print(f"  ✓ Documento '{cev.doc_id}': Proveedor '{cev.provider_name}', SLA: {cev.sla_uptime}, {len(cev.acquired_licenses)} licencias.")

        # 3. Capa Multimodal: Ingesta de Diagramas y Modelos Técnicos
        print("\n[3/5] Capa Multimodal: Ingesta de diagramas arquitectónicos (DiagramConnector)...")
        diagrams_dir_path = fixtures_dir / "diagrams"
        if diagrams_dir_path.is_dir():
            extracted_diags = registry.scan_directory(diagrams_dir_path)
            diagram_evidences = [e for e in extracted_diags if isinstance(e, EvidenciaDiagrama)]
            for dev in diagram_evidences:
                print(f"  ✓ Diagrama '{dev.source_file}' ({dev.format_type}): {len(dev.components)} componentes, {len(dev.relations)} relaciones.")

    # 4. Agente 3: Reconciliador Semántico
    print("\n[4/5] Agente 3: Reconciliando semánticamente código vs. contratos...")
    reconciliator = SemanticReconciliator(confidence_threshold=0.85)
    matched_results = reconciliator.match_all(tech_evidences, contract_evidences)

    fact_sheets: List[HipotesisFactSheet] = []
    all_nudges: List[MicroNudge] = []
    nudge_generator = NudgeGenerator(confidence_threshold=0.85)

    # 5. Agente 4: Generador de Micro-Nudges
    print("\n[5/5] Agente 4: Evaluando umbrales de gobernanza y generando Micro-Nudges...")
    export_data = []

    for hipotesis, tech, contract in matched_results:
        fact_sheets.append(hipotesis)
        nudges = nudge_generator.evaluate_and_generate(hipotesis, tech, contract)
        all_nudges.extend(nudges)

        print(f"  ✓ Fact Sheet '{hipotesis.entity_name}': Confianza {hipotesis.confidence_score * 100:.1f}%, Estado: {hipotesis.status}, {len(nudges)} Micro-Nudges generados.")

        export_data.append({
            "fact_sheet": hipotesis.to_dict(),
            "technical_evidence": tech.to_dict(),
            "contractual_evidence": contract.to_dict(),
            "micro_nudges": [n.to_dict() for n in nudges],
        })

    # Guardar en archivo JSON de salida
    output_file = output_dir / "fact_sheets_draft.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    # Guardar evidencias de diagramas
    if diagram_evidences:
        diag_output_file = output_dir / "diagram_evidences.json"
        with open(diag_output_file, "w", encoding="utf-8") as f:
            json.dump([d.to_dict() for d in diagram_evidences], f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Fact Sheets exportados exitosamente a: {output_file.relative_to(BASE_DIR.parent)}")

    # Imprimir tablas resumen CLI
    print_summary_table(fact_sheets, all_nudges)
    if diagram_evidences:
        print_diagram_summary_table(diagram_evidences)

    return {
        "fact_sheets": fact_sheets,
        "nudges": all_nudges,
        "diagrams": diagram_evidences,
        "output_file": str(output_file),
    }


def print_summary_table(fact_sheets: List[HipotesisFactSheet], nudges: List[MicroNudge]) -> None:
    """Renderiza una tabla resumen en la terminal en formato legible."""
    print("\n" + "=" * 105)
    print(f"{'RESUMEN DE FACT SHEETS IDENTIFICADOS (LEANIX METAMODEL v4)':^105}")
    print("=" * 105)
    header = f"{'Entidad / Aplicación':<36} | {'Stack Técnico':<20} | {'Proveedor':<20} | {'SLA':<7} | {'Score':<6} | {'Estado':<10}"
    print(header)
    print("-" * 105)

    for fs in fact_sheets:
        name = fs.entity_name[:34] + ".." if len(fs.entity_name) > 34 else fs.entity_name
        stack = fs.technical_stack[:18] + ".." if len(fs.technical_stack) > 18 else fs.technical_stack
        prov = fs.provider[:18] + ".." if len(fs.provider) > 18 else fs.provider
        score = f"{fs.confidence_score:.2f}"
        print(f"{name:<36} | {stack:<20} | {prov:<20} | {fs.sla_uptime:<7} | {score:<6} | {fs.status:<10}")

    print("=" * 105)
    print(f"Total Fact Sheets candidatos: {len(fact_sheets)} | Total Micro-Nudges interactivos: {len(nudges)}")
    print("=" * 105 + "\n")

    # Muestra de Micro-Nudges generados
    print("--------------------------------------------------------------------------------")
    print("EJEMPLO DE MICRO-NUDGE GENERADO (Adaptive Card Payload):")
    print("--------------------------------------------------------------------------------")
    if nudges:
        sample_nudge = nudges[0]
        print(f"Destinatario : {sample_nudge.recipient}")
        print(f"Canal        : {sample_nudge.channel}")
        print(f"Pregunta     : {sample_nudge.question_title}")
        print(f"Valor propuesto: {sample_nudge.proposed_value}")
        print("Botones de acción en 1 clic:")
        for action in sample_nudge.quick_actions:
            print(f"  [{action['id']}] -> {action['label']} (Action: {action['action']})")
    print("--------------------------------------------------------------------------------\n")


def print_diagram_summary_table(diagrams: List[EvidenciaDiagrama]) -> None:
    """Renderiza una tabla con el resumen de diagramas y modelos técnicos descubiertos."""
    print("=" * 105)
    print(f"{'DIAGRAMAS Y MODELOS ARQUITECTÓNICOS DESCUBIERTOS (PlantUML / Archi / draw.io)':^105}")
    print("=" * 105)
    header = f"{'Archivo Origen':<32} | {'Formato':<16} | {'Componentes':<12} | {'Relaciones':<12} | {'Citas':<8}"
    print(header)
    print("-" * 105)

    for d in diagrams:
        fn = d.source_file[:30] + ".." if len(d.source_file) > 30 else d.source_file
        fmt = d.format_type[:14]
        n_comp = str(len(d.components))
        n_rel = str(len(d.relations))
        n_cit = str(len(d.citations))
        print(f"{fn:<32} | {fmt:<16} | {n_comp:<12} | {n_rel:<12} | {n_cit:<8}")

    print("=" * 105 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="APM Continuous Discovery Multi-Agent Pipeline")
    parser.add_argument("--dir", dest="scan_dir", default=None, help="Directorio para escaneo multimodal federado general")
    parser.add_argument("--repos", dest="repos_dir", default=None, help="Directorio con repositorios de código fuente")
    parser.add_argument("--contracts", dest="contracts_dir", default=None, help="Directorio con contratos y TDRs (.md, .txt)")
    parser.add_argument("--diagrams", dest="diagrams_dir", default=None, help="Directorio con diagramas (.puml, .archimate, .drawio, .xml)")
    args = parser.parse_args()

    run_pipeline(
        scan_dir=args.scan_dir,
        repos_dir=args.repos_dir,
        contracts_dir=args.contracts_dir,
        diagrams_dir=args.diagrams_dir,
    )
