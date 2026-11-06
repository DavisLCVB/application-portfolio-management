#!/usr/bin/env bash
# Build y push de la imagen del MVP a Artifact Registry.
# Uso (desde cualquier carpeta):
#   ./deploy/build-push.sh <project_id> [region] [repository] [image] [tag]
set -euo pipefail

PROJECT_ID="${1:?Uso: build-push.sh <project_id> [region] [repository] [image] [tag]}"
REGION="${2:-us-central1}"
REPOSITORY="${3:-apm-mvp}"
IMAGE="${4:-apm-mvp-api}"
TAG="${5:-latest}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

FULL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE}:${TAG}"

echo "==> Configurando credenciales Docker para Artifact Registry (${REGION})"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "==> Construyendo ${FULL}"
docker build -f deploy/Dockerfile -t "${FULL}" .

echo "==> Publicando ${FULL}"
docker push "${FULL}"

echo "==> Imagen lista: ${FULL}"
