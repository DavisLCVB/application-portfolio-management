# Despliegue del MVP como API en Google Cloud (Cloud Run + Terraform)

Expone el pipeline de descubrimiento del MVP como una **API HTTP mínima** sobre
**Cloud Run**, con la infraestructura declarada como código (**Terraform**).

## Qué despliega

| Endpoint | Método | Descripción |
|---|---|---|
| `/health` | GET | Estado del servicio y umbrales vigentes |
| `/discover` | POST | Ejecuta el pipeline (fixtures por defecto o rutas propias) y devuelve Fact Sheets, micro-nudges, huérfanos y conflictos |
| `/calibrate` | POST | Ejecuta el barrido de calibración sobre el conjunto sintético etiquetado |

El MVP solo usa la biblioteca estándar de Python; la API añade FastAPI + uvicorn
(ver [`requirements.txt`](requirements.txt)). **No se modifica la lógica del
pipeline**: solo se le añade una capa HTTP.

## Estructura

```
deploy/
├── app.py              # Capa HTTP (FastAPI)
├── Dockerfile          # Imagen Python 3.12 con el MVP + la API
├── requirements.txt    # Dependencias de la API
├── build-push.sh       # Build y push de la imagen a Artifact Registry
└── README.md           # Este archivo
infra/
└── gcp/
    ├── main.tf         # Artifact Registry + Cloud Run (v2) + IAM
    ├── variables.tf    # Parámetros (project_id, region, ...)
    ├── outputs.tf      # URL del servicio e imagen
    └── terraform.tfvars.example
```

## Prerrequisitos

- Proyecto GCP con *billing* (la capa gratuita de Cloud Run alcanza).
- [`gcloud`](https://cloud.google.com/sdk/docs/install) autenticado, `docker` y
  `terraform` (≥ 1.5) instalados.

## Despliegue paso a paso

```bash
# 1. Autenticación y proyecto
gcloud auth login
gcloud auth application-default login          # para Terraform
gcloud config set project MI_PROYECTO

# 2. Habilitar APIs necesarias
gcloud services enable artifactregistry.googleapis.com run.googleapis.com

# 3. Crear primero SOLO el repositorio de imágenes (así existe antes del push)
cd infra/gcp
cp terraform.tfvars.example terraform.tfvars   # edita project_id
terraform init
terraform apply -target=google_artifact_registry_repository.mvp

# 4. Build y push de la imagen (desde la raíz del repo)
cd ../..
./deploy/build-push.sh MI_PROYECTO us-central1 apm-mvp apm-mvp-api latest

# 5. Aplicar el resto (Cloud Run + IAM)
cd infra/gcp && terraform apply

# 6. URL pública del servicio
terraform output service_url
```

## Probar el servicio desplegado

```bash
URL=$(terraform -chdir=infra/gcp output -raw service_url)

curl "$URL/health"

curl -X POST "$URL/discover" -H 'Content-Type: application/json' -d '{}'

curl -X POST "$URL/discover" -H 'Content-Type: application/json' \
  -d '{"review_threshold": 0.6}'

curl -X POST "$URL/calibrate" -H 'Content-Type: application/json' -d '{}'
```

## Probar localmente (sin GCP)

```bash
cd deploy
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --reload
# http://127.0.0.1:8000/docs
```

## Notas

- El servicio se crea con **acceso público** (`allUsers` con `roles/run.invoker`)
  para poder probarlo sin token. Para producción, retira
  `google_cloud_run_v2_service_iam_member.public` de `infra/gcp/main.tf` y
  controla el acceso con IAM.
- Cloud Run **escala a cero**: la primera petición tras un periodo de inactividad
  puede tardar unos segundos (cold start).
- `POST /calibrate` usa por defecto una **rejilla pequeña** (2×2) para mantenerse
  responsive en serverless; la rejilla completa se pide pasando listas en el body
  (p. ej. `{"min_link_scores": "0.3,0.4,0.5,0.6,0.7"}`).
- Destruir todo: `terraform -chdir=infra/gcp destroy`.
