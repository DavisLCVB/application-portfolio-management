variable "project_id" {
  description = "ID del proyecto GCP (ej. mi-proyecto-gcp)"
  type        = string
}

variable "region" {
  description = "Región GCP para Artifact Registry y Cloud Run"
  type        = string
  default     = "us-central1"
}

variable "repository_id" {
  description = "Nombre del repositorio de imágenes en Artifact Registry"
  type        = string
  default     = "apm-mvp"
}

variable "image_name" {
  description = "Nombre de la imagen dentro del repositorio"
  type        = string
  default     = "apm-mvp-api"
}

variable "image_tag" {
  description = "Tag de la imagen a desplegar"
  type        = string
  default     = "latest"
}

variable "service_name" {
  description = "Nombre del servicio Cloud Run"
  type        = string
  default     = "apm-mvp"
}
