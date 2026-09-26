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

variable "enable_iap" {
  description = "Whether to enable Identity-Aware Proxy (IAP) on the External Load Balancer"
  type        = bool
  default     = false
}

variable "iap_client_id" {
  description = "OAuth 2.0 Client ID for Identity-Aware Proxy"
  type        = string
  default     = ""
}

variable "iap_client_secret" {
  description = "OAuth 2.0 Client Secret for Identity-Aware Proxy"
  type        = string
  default     = ""
  sensitive   = true
}

variable "iap_accessors" {
  description = "List of IAM identities granted roles/iap.httpsResourceAccessor"
  type        = list(string)
  default = [
    "user:admin@asadpatel.altostrat.com"
  ]
}

variable "github_repository" {
  description = "GitHub repository authorized for Workload Identity Federation (format: owner/repo)"
  type        = string
  default     = "asadpatel-work/asadpatel-medquad"
}



