"""
Extractor de Código a Catálogo (Code-to-Catalog Extractor).

Este módulo implementa el Agente 1 del pipeline de descubrimiento continuo:
inspecciona repositorios de código fuente, artefactos de empaquetado (pom.xml,
package.json), manifiestos Docker y repositorios Git para generar EvidenciaTecnica
con trazabilidad estricta y citas a nivel de archivo:línea (Principio OCDE 1.3).
"""

import hashlib
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import EvidenciaTecnica


class CodeToCatalogExtractor:
    """
    Agente que analiza repositorios de código y extrae la verdad técnica
    de la aplicación directamente de sus artefactos de construcción.
    """

    def __init__(self, default_contributor: str = "Equipo Core <arquitectura@mef.gob.pe>"):
        self.default_contributor = default_contributor

    def extract(self, repo_path: str) -> EvidenciaTecnica:
        """
        Inspecciona un directorio de repositorio y extrae la EvidenciaTecnica.
        """
        path = Path(repo_path)
        if not path.is_dir():
            raise FileNotFoundError(f"El directorio del repositorio no existe: {repo_path}")

        repo_name = path.name
        primary_language = "Desconocido"
        runtime_version = "Desconocido"
        dependencies: List[str] = []
        endpoints: List[str] = []
        file_citations: Dict[str, str] = {}

        # 1. Inspeccionar Maven pom.xml
        pom_file = path / "pom.xml"
        if pom_file.is_file():
            primary_language = "Java"
            pom_data = self._parse_pom_xml(pom_file)
            if pom_data["repo_name"]:
                repo_name = pom_data["repo_name"]
            if pom_data["runtime_version"]:
                runtime_version = pom_data["runtime_version"]
            dependencies.extend(pom_data["dependencies"])
            file_citations.update(pom_data["citations"])

        # 2. Inspeccionar Node.js package.json (raíz o subcarpetas comunes)
        pkg_file = path / "package.json"
        if not pkg_file.is_file():
            for sub in ["website", "app", "frontend", "client"]:
                candidate = path / sub / "package.json"
                if candidate.is_file():
                    pkg_file = candidate
                    break
        if pkg_file.is_file():
            if primary_language == "Desconocido":
                primary_language = "JavaScript / TypeScript"
            else:
                primary_language = f"{primary_language} + Node.js"

            pkg_data = self._parse_package_json(pkg_file)
            if pkg_data["repo_name"] and repo_name == path.name:
                repo_name = pkg_data["repo_name"]
            if pkg_data["runtime_version"]:
                runtime_version = pkg_data["runtime_version"]
            dependencies.extend(pkg_data["dependencies"])
            file_citations.update(pkg_data["citations"])

        # 3. Inspeccionar Python (requirements.txt / pyproject.toml)
        req_file = path / "requirements.txt"
        pyproject_file = path / "pyproject.toml"
        if req_file.is_file() or pyproject_file.is_file():
            if primary_language == "Desconocido":
                primary_language = "Python"
            py_data = self._parse_python_project(path)
            dependencies.extend(py_data["dependencies"])
            file_citations.update(py_data["citations"])
            if py_data.get("runtime_version") and runtime_version == "Desconocido":
                runtime_version = py_data["runtime_version"]

        # 4. Inspeccionar C++ (CMakeLists.txt)
        cmake_file = path / "CMakeLists.txt"
        if cmake_file.is_file():
            if primary_language == "Desconocido":
                primary_language = "C++"
            cmake_data = self._parse_cmake(cmake_file)
            if cmake_data.get("repo_name") and repo_name == path.name:
                repo_name = cmake_data["repo_name"]
            if cmake_data.get("runtime_version") and runtime_version == "Desconocido":
                runtime_version = cmake_data["runtime_version"]
            dependencies.extend(cmake_data["dependencies"])
            file_citations.update(cmake_data["citations"])

        # 5. Inspeccionar Dockerfile
        docker_file = path / "Dockerfile"
        if docker_file.is_file():
            docker_data = self._parse_dockerfile(docker_file)
            if docker_data.get("base_image"):
                file_citations["dockerfile_base"] = docker_data["citation"]
                if runtime_version == "Desconocido" or "Docker" not in runtime_version:
                    if docker_data.get("inferred_runtime"):
                        runtime_version = docker_data["inferred_runtime"]

        # 6. Inspeccionar endpoints en código fuente
        detected_endpoints, endpoint_citations = self._scan_endpoints(path)
        endpoints.extend(detected_endpoints)
        file_citations.update(endpoint_citations)

        # 5. Obtener Git commit hash y top contributor
        commit_hash, top_contributor = self._inspect_git_metadata(path)

        # 6. Fallback de lenguaje si aún es Desconocido
        if primary_language == "Desconocido":
            fallback_lang = self._detect_fallback_language(path)
            if fallback_lang != "Desconocido":
                primary_language = fallback_lang
                if runtime_version == "Desconocido":
                    runtime_version = f"{fallback_lang} Runtime"

        return EvidenciaTecnica(
            repo_name=repo_name,
            commit_hash=commit_hash,
            primary_language=primary_language,
            runtime_version=runtime_version,
            dependencies=dependencies,
            endpoints=endpoints,
            top_contributor=top_contributor,
            file_citations=file_citations,
        )

    def _detect_fallback_language(self, repo_path: Path) -> str:
        """Detecta lenguaje predominante contando extensiones de archivos de código."""
        counts: Dict[str, int] = {}
        for root, dirs, files in os.walk(repo_path):
            if any(skip in root for skip in [".git", "node_modules", "__pycache__", ".venv", "build", ".cache", "dist"]):
                continue
            for f in files:
                ext = Path(f).suffix.lower()
                if ext in [".py"]:
                    counts["Python"] = counts.get("Python", 0) + 1
                elif ext in [".cpp", ".hpp", ".cc", ".cxx", ".c", ".h"]:
                    counts["C++"] = counts.get("C++", 0) + 1
                elif ext in [".js", ".ts", ".mjs", ".astro", ".jsx", ".tsx"]:
                    counts["JavaScript / TypeScript"] = counts.get("JavaScript / TypeScript", 0) + 1
                elif ext in [".java"]:
                    counts["Java"] = counts.get("Java", 0) + 1

        if counts:
            return max(counts, key=counts.get)
        return "Desconocido"

    def _parse_pom_xml(self, pom_path: Path) -> Dict:
        """Extrae groupId/artifactId, versión de Java y dependencias de pom.xml."""
        citations: Dict[str, str] = {}
        dependencies: List[str] = []
        runtime_version = ""
        repo_name = ""

        with open(pom_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        deps_start_line: Optional[int] = None
        deps_end_line: Optional[int] = None
        current_dep_artifact: Optional[str] = None

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Detectar artifactId principal
            if not repo_name and "<artifactId>" in stripped:
                match = re.search(r"<artifactId>(.*?)</artifactId>", stripped)
                if match:
                    repo_name = match.group(1).strip()
                    citations["artifact_id"] = f"pom.xml#L{idx}"

            # Detectar versión de Java
            if "<java.version>" in stripped:
                match = re.search(r"<java.version>(.*?)</java.version>", stripped)
                if match:
                    runtime_version = f"Java {match.group(1).strip()}"
                    citations["runtime_version"] = f"pom.xml#L{idx}"
            elif "<maven.compiler.source>" in stripped and not runtime_version:
                match = re.search(r"<maven.compiler.source>(.*?)</maven.compiler.source>", stripped)
                if match:
                    runtime_version = f"Java {match.group(1).strip()}"
                    citations["runtime_version"] = f"pom.xml#L{idx}"

            # Rastrear bloque de dependencias
            if "<dependencies>" in stripped:
                deps_start_line = idx
            if "</dependencies>" in stripped:
                deps_end_line = idx

            # Capturar dependencias individuales
            if "<artifactId>" in stripped and deps_start_line is not None and deps_end_line is None:
                match = re.search(r"<artifactId>(.*?)</artifactId>", stripped)
                if match:
                    dep = match.group(1).strip()
                    if dep not in dependencies:
                        dependencies.append(dep)

        if deps_start_line:
            end = deps_end_line or len(lines)
            citations["dependencies"] = f"pom.xml#L{deps_start_line}-L{end}"

        return {
            "repo_name": repo_name,
            "runtime_version": runtime_version or "Java (sin versión explícita)",
            "dependencies": dependencies,
            "citations": citations,
        }

    def _parse_package_json(self, pkg_path: Path) -> Dict:
        """Extrae nombre, runtime y dependencias de package.json."""
        citations: Dict[str, str] = {}
        dependencies: List[str] = []
        runtime_version = ""
        repo_name = ""

        with open(pkg_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        content = "".join(lines)
        try:
            data = json.loads(content)
            repo_name = data.get("name", "")
            if "engines" in data and "node" in data["engines"]:
                runtime_version = f"Node.js {data['engines']['node']}"
            all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            dependencies = list(all_deps.keys())
        except Exception:
            data = {}

        # Determinar líneas para citas primarias
        deps_start_line: Optional[int] = None
        name_line: Optional[int] = None
        for idx, line in enumerate(lines, start=1):
            if '"name":' in line and not name_line:
                name_line = idx
                citations["project_name"] = f"package.json#L{idx}"
            if '"dependencies":' in line and not deps_start_line:
                deps_start_line = idx

        if deps_start_line:
            citations["dependencies"] = f"package.json#L{deps_start_line}"

        return {
            "repo_name": repo_name,
            "runtime_version": runtime_version or "Node.js",
            "dependencies": dependencies,
            "citations": citations,
        }

    def _parse_dockerfile(self, docker_path: Path) -> Dict:
        """Extrae imagen base de Dockerfile."""
        base_image = ""
        citation = ""
        inferred_runtime = ""

        with open(docker_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                match = re.match(r"^\s*FROM\s+([^\s]+)", line, re.IGNORECASE)
                if match:
                    base_image = match.group(1).strip()
                    citation = f"Dockerfile#L{idx}"
                    if "openjdk" in base_image or "temurin" in base_image or "corretto" in base_image:
                        inferred_runtime = f"Docker Base ({base_image})"
                    elif "node" in base_image:
                        inferred_runtime = f"Docker Node ({base_image})"
                    elif "python" in base_image:
                        inferred_runtime = f"Docker Python ({base_image})"
                    else:
                        inferred_runtime = f"Container Image ({base_image})"
                    break

        return {
            "base_image": base_image,
            "citation": citation,
            "inferred_runtime": inferred_runtime,
        }

    def _parse_python_project(self, repo_path: Path) -> Dict:
        """Extrae dependencias de requirements.txt o pyproject.toml."""
        dependencies: List[str] = []
        citations: Dict[str, str] = {}
        runtime = "Python 3"

        req_path = repo_path / "requirements.txt"
        if req_path.is_file():
            with open(req_path, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f, start=1):
                    line_s = line.strip()
                    if line_s and not line_s.startswith("#") and not line_s.startswith("-"):
                        pkg = re.split(r"[=<>~;]", line_s)[0].strip()
                        if pkg and pkg not in dependencies:
                            dependencies.append(pkg)
                            if "dependencies" not in citations:
                                citations["dependencies"] = f"requirements.txt#L{idx}"

        pyproject_path = repo_path / "pyproject.toml"
        if pyproject_path.is_file():
            citations["pyproject"] = "pyproject.toml#L1"

        return {
            "dependencies": dependencies,
            "citations": citations,
            "runtime_version": runtime,
        }

    def _parse_cmake(self, cmake_path: Path) -> Dict:
        """Extrae nombre de proyecto y estándar C++ de CMakeLists.txt."""
        repo_name = ""
        runtime = "C++"
        citations: Dict[str, str] = {}
        dependencies: List[str] = []

        with open(cmake_path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f, start=1):
                m_proj = re.search(r"project\s*\(\s*([a-zA-Z0-9_\-]+)", line, re.IGNORECASE)
                if m_proj and not repo_name:
                    repo_name = m_proj.group(1).strip()
                    citations["cmake_project"] = f"CMakeLists.txt#L{idx}"
                m_std = re.search(r"CMAKE_CXX_STANDARD\s+([0-9]+)", line, re.IGNORECASE)
                if m_std:
                    runtime = f"C++{m_std.group(1).strip()}"
                    citations["cxx_standard"] = f"CMakeLists.txt#L{idx}"
                m_pkg = re.search(r"find_package\s*\(\s*([a-zA-Z0-9_\-]+)", line, re.IGNORECASE)
                if m_pkg:
                    pkg_name = m_pkg.group(1).strip()
                    if pkg_name not in dependencies:
                        dependencies.append(pkg_name)

        return {
            "repo_name": repo_name,
            "runtime_version": runtime,
            "dependencies": dependencies,
            "citations": citations,
        }

    def _scan_endpoints(self, repo_path: Path) -> Tuple[List[str], Dict[str, str]]:
        """Escanea código fuente en busca de definiciones de endpoints REST/HTTP."""
        endpoints: List[str] = []
        citations: Dict[str, str] = {}

        # Patrones para Spring y Express
        spring_pattern = re.compile(
            r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)\s*\(\s*(?:(?:value|path)\s*=\s*)?["\']([^"\']+)["\']',
            re.IGNORECASE
        )
        express_pattern = re.compile(
            r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            re.IGNORECASE
        )

        for root, _, files in os.walk(repo_path):
            # Omitir carpetas pesadas
            if any(part in root for part in [".git", "node_modules", "target", "build", "dist"]):
                continue

            for file in files:
                if file.endswith((".java", ".js", ".ts")):
                    file_p = Path(root) / file
                    rel_p = file_p.relative_to(repo_path).as_posix()
                    try:
                        with open(file_p, "r", encoding="utf-8", errors="ignore") as f:
                            java_class_prefix = ""
                            for idx, line in enumerate(f, start=1):
                                # Buscar Spring
                                m_spring = spring_pattern.search(line)
                                if m_spring:
                                    raw_method = m_spring.group(1).replace("Mapping", "").upper()
                                    path_val = m_spring.group(2)
                                    
                                    if raw_method == "REQUEST" and not java_class_prefix and ("class " not in line):
                                        java_class_prefix = path_val.rstrip("/")
                                        method = "ANY"
                                        full_path = path_val
                                    else:
                                        method = raw_method
                                        full_path = f"{java_class_prefix}{path_val}" if java_class_prefix and not path_val.startswith(java_class_prefix) else path_val

                                    endpoint_str = f"{method} {full_path}"
                                    if endpoint_str not in endpoints:
                                        endpoints.append(endpoint_str)
                                        citations[f"endpoint_{full_path}"] = f"{rel_p}#L{idx}"

                                # Buscar Express
                                m_express = express_pattern.search(line)
                                if m_express:
                                    method = m_express.group(1).upper()
                                    path_val = m_express.group(2)
                                    endpoint_str = f"{method} {path_val}"
                                    if endpoint_str not in endpoints:
                                        endpoints.append(endpoint_str)
                                        citations[f"endpoint_{path_val}"] = f"{rel_p}#L{idx}"
                    except Exception:
                        continue

        return endpoints, citations

    def _inspect_git_metadata(self, repo_path: Path) -> Tuple[str, str]:
        """Obtiene hash de commit y top contributor vía git o fallback determinista."""
        commit_hash = ""
        top_contributor = self.default_contributor

        # 1. Intentar invocar git log si es un repo git
        if (repo_path / ".git").exists():
            try:
                # Commit hash
                res_hash = subprocess.run(
                    ["git", "rev-parse", "--short=12", "HEAD"],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if res_hash.returncode == 0 and res_hash.stdout.strip():
                    commit_hash = res_hash.stdout.strip()

                # Top contributor
                res_author = subprocess.run(
                    ["git", "log", "-n", "20", "--format=%an <%ae>"],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if res_author.returncode == 0 and res_author.stdout.strip():
                    authors = [a.strip() for a in res_author.stdout.strip().split("\n") if a.strip()]
                    if authors:
                        # Autor más frecuente
                        top_contributor = max(set(authors), key=authors.count)
            except Exception:
                pass

        # 2. Si no hay git o no produjo commit hash, generar hash determinista sobre el directorio
        if not commit_hash:
            hasher = hashlib.sha256()
            for root, _, files in sorted(os.walk(repo_path)):
                for fname in sorted(files):
                    fpath = Path(root) / fname
                    hasher.update(fname.encode("utf-8"))
                    try:
                        hasher.update(str(fpath.stat().st_size).encode("utf-8"))
                    except Exception:
                        pass
            commit_hash = hasher.hexdigest()[:12]

        return commit_hash, top_contributor
