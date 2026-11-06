---
title: Guía técnica del MVP
description: "Guía rápida: ejecutar, probar y desplegar el pipeline de descubrimiento multi-agente del APM."
---

# Guía técnica del MVP — APM con IA Agéntica

> Complemento práctico del **Informe final**: el *cómo* (ejecutar, probar y
> desplegar), no el *porqué*.

## Qué es

Pipeline de **descubrimiento continuo y reconciliación semántica** en Python
(solo biblioteca estándar), con 4 agentes: **Code-to-Catalog** (repos),
**Dark Data Miner** (contratos/TDRs), **Reconciliador Semántico** (ancla en el
catálogo, relación N:M, score heurístico) y **Micro-Nudge** (validación en 1
clic). Cada dato lleva cita primaria (ej. `pom.xml#L16`).

## Ejecutar localmente

```bash
cd mvp
python3 run_discovery.py                  # fixtures canónicos
python3 calibrate.py                      # barrido de umbrales
python3 -m unittest discover -s tests     # 103 tests
```

## API desplegada (Cloud Run)

`https://apm-mvp-5dcohejqua-uc.a.run.app`

- `GET /health` — estado y umbrales vigentes
- `POST /discover` — ejecuta el pipeline (Fact Sheets, nudges, huérfanos, conflictos)
- `POST /calibrate` — barrido de calibración

```bash
curl https://apm-mvp-5dcohejqua-uc.a.run.app/health
curl -X POST https://apm-mvp-5dcohejqua-uc.a.run.app/discover \
  -H 'Content-Type: application/json' -d '{}'
```

## Desplegar en GCP (Terraform)

Infraestructura como código en `infra/gcp/`; capa HTTP en `deploy/` (FastAPI +
Docker). Detalle en `deploy/README.md`.

```bash
gcloud services enable artifactregistry.googleapis.com run.googleapis.com
cd infra/gcp && terraform init && terraform apply -target=google_artifact_registry_repository.mvp
cd ../.. && ./deploy/build-push.sh MI_PROYECTO us-central1 apm-mvp apm-mvp-api latest
cd infra/gcp && terraform apply
```

## Calibración del score

Conjunto sintético etiquetado (36 evidencias: 26 calibración / 10 evaluación,
semilla fija). Umbrales vigentes `0.50 / 0.05 / 0.85`: exactitud **0.8462**,
F1 macro **0.8194**. El barrido completo (7×7) elige `0.60 / 0.01`, pero no
generaliza a evaluación → **no se cambian los umbrales** (overfitting a muestra
minúscula). El score no es una probabilidad.

## Límites

- Datos sintéticos (caso académico), sin cliente real ni datos de producción.
- El score no alcanza cero errores de auto-publicación.
- Cloud Run escala a cero: la primera petición tarda unos segundos (cold start).
