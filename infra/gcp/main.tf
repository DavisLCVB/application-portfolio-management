terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# --- Artifact Registry: repositorio privado de imágenes Docker ---
resource "google_artifact_registry_repository" "mvp" {
  location      = var.region
  repository_id = var.repository_id
  format        = "DOCKER"
  description   = "Imágenes del APM Discovery MVP"
}

# --- Cuenta de servicio de Cloud Run ---
resource "google_service_account" "run_sa" {
  account_id   = "apm-mvp-run"
  display_name = "APM MVP Cloud Run"
  description  = "Cuenta de servicio para ejecutar el servicio Cloud Run del MVP"
}

# --- Servicio Cloud Run (v2) ---
resource "google_cloud_run_v2_service" "mvp" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.run_sa.email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_id}/${var.image_name}:${var.image_tag}"
      ports {
        container_port = 8080
        name           = "http1"
      }
    }
  }
}

# --- Invocación pública (sin autenticación) para poder probar el MVP ---
# Para producción, retirar este recurso y controlar el acceso con IAM.
resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.mvp.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
