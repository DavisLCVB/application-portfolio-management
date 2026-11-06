output "service_url" {
  description = "URL pública del servicio Cloud Run"
  value       = google_cloud_run_v2_service.mvp.uri
}

output "image_repository" {
  description = "Nombre completo del repositorio de imágenes"
  value       = google_artifact_registry_repository.mvp.name
}

output "full_image_path" {
  description = "Ruta completa de la imagen (para build y push)"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository_id}/${var.image_name}:${var.image_tag}"
}
