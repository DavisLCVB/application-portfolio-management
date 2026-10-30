"""
Generador determinista del conjunto sintético etiquetado para calibrar el reconciliador.

El APM es un caso académico sin datos reales: este conjunto, con verdad conocida, permite
medir precisión/recall del pipeline y calibrar sus umbrales. La organización es hipotética.
Misma semilla → mismos bytes (solo biblioteca estándar, sin marcas de tiempo).

Uso (desde `mvp/`):
    uv run python -m src.synthetic --seed 42 --out datasets/sintetico
    uv run python run_discovery.py --repos datasets/sintetico/repos \
        --contracts datasets/sintetico/contratos --catalog datasets/sintetico/catalogo_aplicaciones.csv

Estructura de salida:
    catalogo_aplicaciones.csv   catálogo existente (mismo formato que fixtures/catalogs/)
    repos/<slug>/               pom.xml o package.json + Dockerfile
    contratos/<doc-id>.md       TDRs con la estructura de fixtures/contracts/
    labels.json                 verdad conocida por evidencia

Esquema de labels.json:
    {
      "seed": int,
      "calibration_ratio": 0.7,
      "category_counts": {category: int},
      "items": [{
        "evidence_id": str,        # repo_name (artifactId / name de package.json) o doc_id del TDR,
                                   # es decir, el identificador que usa la salida del pipeline
        "evidence_type": "repositorio" | "contrato",
        "path": str,               # ruta relativa a la raíz del conjunto
        "category": "clear_match" | "divergent_alias" | "multi_app_contract" | "orphan_repo"
                    | "orphan_contract" | "conflict" | "noise",
        "noise": "typo" | "abbreviation" | "repeated_vendor" | null,
        "expected_outcome": "linked" | "multi_app" | "orphan" | "conflict",
        "expected_app_ids": [str], # 1 si linked, ≥2 si multi_app o conflict (candidatas), 0 si orphan
        "split": "calibration" | "evaluation"
      }]
    }

La partición calibración/evaluación es estratificada por categoría (≈70/30) y determinista.
"""

import argparse
import csv
import io
import json
import random
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CATALOG_FILE = "catalogo_aplicaciones.csv"
REPOS_DIR = "repos"
CONTRACTS_DIR = "contratos"
LABELS_FILE = "labels.json"
CALIBRATION_RATIO = 0.7
CATEGORIES = (
    "clear_match", "divergent_alias", "multi_app_contract",
    "orphan_repo", "orphan_contract", "conflict", "noise",
)

# (nombre oficial, slug de repositorio, abreviatura)
DOMAINS: List[Tuple[str, str, str]] = [
    ("Sistema de Gestión de Expedientes", "gestion-expedientes", "SGE"),
    ("Sistema de Trámite Documentario", "tramite-documentario", "STD"),
    ("Registro de Proveedores del Estado", "registro-proveedores", "RPE"),
    ("Sistema de Planeamiento Presupuestal", "planeamiento-presupuestal", "SPP"),
    ("Sistema de Contabilidad Gubernamental", "contabilidad-gubernamental", "SCG"),
    ("Sistema de Logística y Abastecimiento", "logistica-abastecimiento", "SILAB"),
    ("Portal de Transparencia Institucional", "transparencia-institucional", "PTI"),
    ("Sistema de Gestión de Inversiones", "gestion-inversiones", "SGI"),
    ("Plataforma de Datos Abiertos", "datos-abiertos", "PDA"),
    ("Sistema de Control de Asistencia", "control-asistencia", "SCA"),
    ("Sistema de Gestión de Proyectos", "gestion-proyectos", "SGP"),
    ("Sistema de Monitoreo de Metas", "monitoreo-metas", "SMM"),
    ("Sistema de Fiscalización Tributaria", "fiscalizacion-tributaria", "SFT"),
    ("Registro de Licencias de Funcionamiento", "licencias-funcionamiento", "RLF"),
    ("Sistema de Gestión de Becas", "gestion-becas", "SGB"),
    ("Sistema de Programas Sociales", "programas-sociales", "SPS"),
    ("Sistema de Gestión de Archivos", "gestion-archivos", "SGA"),
    ("Sistema de Notificaciones Electrónicas", "notificaciones-electronicas", "SNE"),
    ("Sistema de Control de Viáticos", "control-viaticos", "SCV"),
    ("Sistema de Gestión de Capacitaciones", "gestion-capacitaciones", "SGCAP"),
    ("Sistema de Seguimiento de Obras", "seguimiento-obras", "SSO"),
    ("Catastro Municipal Digital", "catastro-municipal", "CMD"),
    ("Sistema de Registro Civil", "registro-civil", "SRC"),
    ("Sistema de Gestión de Flota Vehicular", "flota-vehicular", "SGFV"),
    ("Sistema de Defensa Legal", "defensa-legal", "SDL"),
    ("Sistema de Gestión de Riesgos", "gestion-riesgos", "SGR"),
    ("Sistema de Auditoría Interna", "auditoria-interna", "SAI"),
    ("Sistema de Control de Almacenes", "control-almacenes", "SCALM"),
    ("Sistema de Gestión de Convenios", "gestion-convenios", "SGCON"),
    ("Sistema de Quejas y Reclamos", "quejas-reclamos", "SQR"),
    ("Sistema de Gestión de Citas", "gestion-citas", "SGCIT"),
]

# (nombre oficial, alias funcional, slug técnico divergente)
DIVERGENT: List[Tuple[str, str, str]] = [
    ("Pasarela de Recaudación", "Pagos en Línea", "svc-pagos-v2"),
    ("Registro Único de Beneficiarios", "Padrón de Beneficiarios", "padron-api"),
    ("Sistema de Control Patrimonial", "Inventario de Bienes", "bienes-inventory-svc"),
    ("Plataforma de Firma Electrónica", "Firmador Institucional", "firmador-backend"),
    ("Gestión de Recursos Humanos", "Planillas", "planillas-core"),
    ("Sistema de Atención al Ciudadano", "Mesa de Ayuda", "helpdesk-ciudadano"),
]

# (nombre base, slug común, calificadores simétricos de las dos aplicaciones gemelas)
TWINS: List[Tuple[str, str, Tuple[str, str]]] = [
    ("Mesa de Partes Virtual", "mesa-partes-virtual", ("Central", "Regional")),
    ("Sistema de Gestión de Pagos", "gestion-pagos", ("Proveedores", "Terceros")),
    ("Sistema de Registro de Visitas", "registro-visitas", ("Interno", "Externo")),
    ("Sistema de Consulta de Deudas", "consulta-deudas", ("Tributarias", "Coactivas")),
    ("Sistema de Reportes Gerenciales", "reportes-gerenciales", ("Financieros", "Operativos")),
]

# Pocos proveedores repartidos entre muchas aplicaciones: ruido de "proveedor repetido"
VENDORS = [
    "Consorcio Andino de Software S.A.C.",
    "Soluciones Digitales del Sur S.A.",
    "TecnoServicios Públicos E.I.R.L.",
    "Integra Sistemas Corporativos S.A.C.",
]
OWNERS = ["Lucía Ramos", "Martín Quispe", "Rosa Huamán", "Diego Salas", "Elena Torres", "Raúl Vega"]

STACKS = {
    "java": {"language": "Java", "runtime": "OpenJDK 17", "deps": "Spring Boot, Hibernate, PostgreSQL JDBC",
             "licenses": "Java OpenJDK, Spring Boot Framework, PostgreSQL Community Database"},
    "node": {"language": "TypeScript", "runtime": "Node.js 20", "deps": "React, Next.js, Express",
             "licenses": "Node.js, React, Next.js, PostgreSQL Community Database"},
}

N_CLEAR, N_DIVERGENT, N_TWINS, N_NOISE, N_MULTI_POOL, N_MULTI = 5, 4, 4, 6, 7, 4
N_ORPHAN_REPOS, N_ORPHAN_CONTRACTS = 4, 4


def _de(name: str) -> str:
    """Contracción gramatical ante el nombre: 'del Sistema', 'de la Plataforma'."""
    feminine = ("Plataforma", "Pasarela", "Mesa", "Gestión")
    return f"de la {name}" if name.startswith(feminine) else f"del {name}"


def _typo(word: str, rng: random.Random) -> str:
    """Transpone dos letras internas contiguas (typo determinista)."""
    i = rng.randrange(1, len(word) - 2)
    return word[:i] + word[i + 1] + word[i] + word[i + 2:]


def _typo_slug(slug: str, rng: random.Random) -> str:
    parts = slug.split("-")
    idx = max(range(len(parts)), key=lambda k: len(parts[k]))
    parts[idx] = _typo(parts[idx], rng)
    return "-".join(parts)


def _pom(slug: str, title: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>

    <groupId>org.entidad.hipotetica</groupId>
    <artifactId>{slug}</artifactId>
    <version>1.0.0</version>
    <name>{title}</name>

    <properties>
        <java.version>17</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
        </dependency>
    </dependencies>
</project>
"""


def _package_json(slug: str, title: str) -> str:
    data = {
        "name": slug,
        "version": "1.0.0",
        "description": title,
        "engines": {"node": ">=20.0.0"},
        "dependencies": {"express": "^4.19.2", "next": "^14.1.4", "react": "^18.2.0"},
    }
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _dockerfile(kind: str, slug: str) -> str:
    if kind == "java":
        return f'FROM eclipse-temurin:17-jre-alpine\nWORKDIR /app\nCOPY target/{slug}.jar app.jar\nENTRYPOINT ["java", "-jar", "app.jar"]\n'
    return 'FROM node:20-alpine\nWORKDIR /app\nCOPY . .\nRUN npm ci --omit=dev\nCMD ["npm", "start"]\n'


def _tdr(doc_id: str, title: str, vendor: str, kind: str, rng: random.Random) -> str:
    year = rng.choice([2023, 2024, 2025])
    sla = rng.choice(["99.0", "99.5", "99.8", "99.9"])
    return f"""# Términos de Referencia: {title}

## Cláusula 1: Identificación y Objeto del Servicio
- Código de referencia contractual: {doc_id}
- Objeto: Contratación del servicio de soporte, mantenimiento correctivo y evolutivo de la solución indicada en el título.

## Cláusula 2: Proveedor Adjudicado y Razón Social
- Proveedor adjudicado: {vendor}

## Cláusula 3: Vigencia y Calendario Contractual
- Periodo de vigencia: desde {year}-01-01 hasta {year + 2}-12-31

## Cláusula 4: Acuerdos de Nivel de Servicio (SLA)
- Disponibilidad mínima garantizada (SLA uptime): {sla}% mensual.

## Cláusula 5: Arquitectura Técnica y Licenciamiento Homologado
- Software y licencias requeridas: {STACKS[kind]['licenses']}.
"""


def build(seed: int) -> Dict[str, object]:
    """Construye en memoria el conjunto completo: {ruta relativa: contenido} + etiquetas."""
    rng = random.Random(seed)
    domains = rng.sample(DOMAINS, N_CLEAR + N_NOISE + N_MULTI_POOL + N_ORPHAN_REPOS + N_ORPHAN_CONTRACTS)
    clear, rest = domains[:N_CLEAR], domains[N_CLEAR:]
    noisy, rest = rest[:N_NOISE], rest[N_NOISE:]
    multi_pool, rest = rest[:N_MULTI_POOL], rest[N_MULTI_POOL:]
    orphan_repos, orphan_contracts = rest[:N_ORPHAN_REPOS], rest[N_ORPHAN_REPOS:]
    divergent = rng.sample(DIVERGENT, N_DIVERGENT)
    twins = rng.sample(TWINS, N_TWINS)

    # Aplicaciones del catálogo: (clave, nombre, alias, slug, abreviatura)
    apps: List[Dict[str, str]] = []
    for name, slug, abbr in clear + noisy + multi_pool:
        apps.append({"key": slug, "name": name, "alias": abbr, "slug": slug, "abbr": abbr})
    for name, alias, slug in divergent:
        apps.append({"key": slug, "name": name, "alias": alias, "slug": slug, "abbr": ""})
    for base, slug, quals in twins:
        for q in quals:
            apps.append({"key": f"{slug}#{q}", "name": f"{base} {q}", "alias": "", "slug": slug, "abbr": ""})
    rng.shuffle(apps)  # los códigos no delatan la categoría
    twin_kind = {slug: rng.choice(["java", "node"]) for _, slug, _ in twins}
    for i, app in enumerate(apps, start=1):
        app["code"] = f"APP-{i:03d}"
        app["kind"] = twin_kind.get(app["slug"]) or rng.choice(["java", "node"])
        app["vendor"] = rng.choice(VENDORS)
        app["owner"] = rng.choice(OWNERS)
    by_key = {a["key"]: a for a in apps}

    files: Dict[str, str] = {}
    items: List[Dict[str, object]] = []
    doc_numbers = iter(rng.sample(range(100, 1000), 40))

    def add_repo(slug: str, title: str, kind: str, category: str, outcome: str,
                 app_ids: List[str], noise: Optional[str] = None) -> None:
        base = f"{REPOS_DIR}/{slug}"
        if kind == "java":
            files[f"{base}/pom.xml"] = _pom(slug, title)
        else:
            files[f"{base}/package.json"] = _package_json(slug, title)
        files[f"{base}/Dockerfile"] = _dockerfile(kind, slug)
        items.append({"evidence_id": slug, "evidence_type": "repositorio", "path": base, "category": category,
                      "noise": noise, "expected_outcome": outcome, "expected_app_ids": app_ids})

    def add_tdr(title: str, vendor: str, kind: str, category: str, outcome: str,
                app_ids: List[str], noise: Optional[str] = None) -> None:
        doc_id = f"TDR-2024-ORG-{next(doc_numbers):04d}"
        path = f"{CONTRACTS_DIR}/{doc_id.lower()}.md"
        files[path] = _tdr(doc_id, title, vendor, kind, rng)
        items.append({"evidence_id": doc_id, "evidence_type": "contrato", "path": path, "category": category,
                      "noise": noise, "expected_outcome": outcome, "expected_app_ids": app_ids})

    for _, slug, _ in clear:
        a = by_key[slug]
        add_repo(slug, a["name"], a["kind"], "clear_match", "linked", [a["code"]])
        add_tdr(f"Soporte y Mantenimiento {_de(a['name'])}", a["vendor"], a["kind"], "clear_match", "linked", [a["code"]])

    for _, _, slug in divergent:
        a = by_key[slug]
        add_repo(slug, a["alias"], a["kind"], "divergent_alias", "linked", [a["code"]])

    for base, slug, quals in twins:
        pair = [by_key[f"{slug}#{q}"] for q in quals]
        add_repo(slug, base, pair[0]["kind"], "conflict", "conflict", sorted(a["code"] for a in pair))

    # Ruido: 2 typos en repos, 2 abreviaturas en repos, 1 typo en TDR, 1 TDR abreviado de proveedor repetido
    n0, n1, n2, n3, n4, n5 = (by_key[slug] for _, slug, _ in noisy)
    add_repo(_typo_slug(n0["slug"], rng), n0["name"], n0["kind"], "noise", "linked", [n0["code"]], "typo")
    add_repo(_typo_slug(n1["slug"], rng), n1["name"], n1["kind"], "noise", "linked", [n1["code"]], "typo")
    add_repo(f"{n2['abbr'].lower()}-core", n2["abbr"], n2["kind"], "noise", "linked", [n2["code"]], "abbreviation")
    add_repo(f"{n3['abbr'].lower()}-api", n3["abbr"], n3["kind"], "noise", "linked", [n3["code"]], "abbreviation")
    typo_name = " ".join(_typo(w, rng) if len(w) > 6 else w for w in n4["name"].split())
    add_tdr(f"Mantenimiento {_de(typo_name)}", n4["vendor"], n4["kind"], "noise", "linked", [n4["code"]], "typo")
    # El proveedor más frecuente del catálogo: el proveedor no discrimina
    common_vendor = max(VENDORS, key=lambda v: (sum(a["vendor"] == v for a in apps), v))
    add_tdr(f"Soporte del {n5['abbr']}", common_vendor, n5["kind"], "noise", "linked", [n5["code"]], "repeated_vendor")

    pool = [by_key[slug] for _, slug, _ in multi_pool]
    for i in range(N_MULTI):
        a, b = pool[(2 * i) % len(pool)], pool[(2 * i + 1) % len(pool)]
        add_tdr(f"Mantenimiento Evolutivo {_de(a['name'])} y {_de(b['name'])}", a["vendor"], a["kind"],
                "multi_app_contract", "multi_app", sorted([a["code"], b["code"]]))

    for name, slug, _ in orphan_repos:
        add_repo(slug, name, rng.choice(["java", "node"]), "orphan_repo", "orphan", [])
    for name, _, _ in orphan_contracts:
        add_tdr(f"Implementación {_de(name)}", rng.choice(VENDORS), rng.choice(["java", "node"]),
                "orphan_contract", "orphan", [])

    # Partición estratificada por categoría
    for category in CATEGORIES:
        in_cat = [it for it in items if it["category"] == category]
        rng.shuffle(in_cat)
        n_cal = round(len(in_cat) * CALIBRATION_RATIO)
        for k, it in enumerate(in_cat):
            it["split"] = "calibration" if k < n_cal else "evaluation"

    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["Codigo", "Nombre Aplicacion", "Responsable Tecnico", "Lenguaje Principal",
                     "Version Runtime", "Dependencias", "SLA Uptime", "Proveedor", "Alias"])
    for a in apps:
        stack = STACKS[a["kind"]]
        email = a["owner"].split()[0][0].lower() + a["owner"].split()[1].lower().replace("á", "a")
        writer.writerow([a["code"], a["name"], f"{a['owner']} <{email}@entidad.example>", stack["language"],
                         stack["runtime"], stack["deps"], "99.5%", a["vendor"], a["alias"]])
    files[CATALOG_FILE] = buf.getvalue()

    counts = {c: sum(it["category"] == c for it in items) for c in CATEGORIES}
    labels = {"seed": seed, "calibration_ratio": CALIBRATION_RATIO, "category_counts": counts,
              "items": sorted(items, key=lambda it: it["evidence_id"])}
    files[LABELS_FILE] = json.dumps(labels, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    return files


def generate(seed: int, out_dir: Path) -> Path:
    """Escribe el conjunto en `out_dir`, reemplazando solo un conjunto generado previamente."""
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()) and not (out / LABELS_FILE).is_file():
        raise ValueError(f"{out} no está vacío y no es un conjunto sintético generado (falta {LABELS_FILE})")
    for sub in (REPOS_DIR, CONTRACTS_DIR):
        shutil.rmtree(out / sub, ignore_errors=True)
    for rel, content in build(seed).items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador del conjunto sintético etiquetado")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="datasets/sintetico")
    args = parser.parse_args()
    print(f"Conjunto sintético (semilla {args.seed}) escrito en: {generate(args.seed, Path(args.out))}")
