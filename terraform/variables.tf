variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  default     = "capstone-506616"
}

variable "region" {
  description = "Google Cloud primary region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment stage"
  type        = string
  default     = "production"
}

variable "backend_image" {
  description = "Container image URI for Backend Cloud Run service"
  type        = string
  default     = "us-central1-docker.pkg.dev/capstone-506616/medquad/medquad-backend:latest"
}

variable "frontend_image" {
  description = "Container image URI for Frontend Cloud Run service"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "invoker_member" {
  description = "IAM member for Cloud Run invoker access"
  type        = string
  default     = "serviceAccount:sa-medquad-runtime@capstone-506616.iam.gserviceaccount.com"
}


