terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.15.0"
    }
  }
}

provider "google" {
  project               = var.project_id
  region                = var.region
  user_project_override = true
  billing_project       = var.project_id
}

# 1. Enable Required GCP APIs
locals {
  services = [
    "run.googleapis.com",
    "discoveryengine.googleapis.com",
    "aiplatform.googleapis.com",
    "bigquery.googleapis.com",
    "cloudtrace.googleapis.com",
    "logging.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "iamcredentials.googleapis.com",
    "cloudscheduler.googleapis.com",
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.services)
  service            = each.key
  disable_on_destroy = false
}

# 2. IAM Service Account for MedQuAD Assistant Runtime
resource "google_service_account" "runtime_sa" {
  account_id   = "sa-medquad-runtime"
  display_name = "MedQuAD Assistant Runtime Service Account"
  depends_on   = [google_project_service.apis]
}

resource "google_service_account_iam_member" "sa_token_creator" {
  for_each = toset([
    "roles/iam.serviceAccountTokenCreator",
    "roles/iam.serviceAccountOpenIdTokenCreator",
    "roles/iam.serviceAccountUser",
  ])
  service_account_id = google_service_account.runtime_sa.name
  role               = each.key
  member             = "user:admin@asadpatel.altostrat.com"
}

resource "google_project_iam_member" "sa_roles" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/discoveryengine.editor",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/cloudtrace.agent",
    "roles/logging.logWriter",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectAdmin",
    "roles/run.invoker",
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.runtime_sa.email}"
}

# 3. Google Cloud Storage Bucket for MedQuAD Grounding Corpus
resource "google_storage_bucket" "corpus_bucket" {
  name                     = "${var.project_id}-medquad-corpus"
  location                 = var.region
  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}

# 3b. Vertex AI Search / Discovery Engine Data Store & Search Engine
resource "google_discovery_engine_data_store" "medquad_ds" {
  location                     = "global"
  data_store_id                = "medquad-corpus-v1"
  display_name                 = "MedQuAD Grounding Corpus"
  industry_vertical            = "GENERIC"
  content_config               = "CONTENT_REQUIRED"
  solution_types               = ["SOLUTION_TYPE_SEARCH"]
  create_advanced_site_search  = false
  depends_on                   = [google_project_service.apis]
}

resource "google_discovery_engine_search_engine" "medquad_search" {
  location         = "global"
  collection_id    = "default_collection"
  engine_id        = "medquad-search-app-v2"
  display_name     = "MedQuAD Search Engine v2 (Full Corpus)"
  data_store_ids   = [google_discovery_engine_data_store.medquad_ds.data_store_id]
  search_engine_config {
    search_tier    = "SEARCH_TIER_STANDARD"
    search_add_ons = ["SEARCH_ADD_ON_LLM"]
  }
  lifecycle {
    ignore_changes = [industry_vertical]
  }
  depends_on       = [google_discovery_engine_data_store.medquad_ds]
}

resource "google_artifact_registry_repository" "medquad_repo" {
  location      = var.region
  repository_id = "medquad"
  description   = "Docker repository for MedQuAD containers"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "cloudbuild_storage_reader" {
  bucket = google_storage_bucket.corpus_bucket.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:1055109340350-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/storage.admin",
    "roles/artifactregistry.writer",
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:1055109340350-compute@developer.gserviceaccount.com"
}

# 4. BigQuery Telemetry Dataset & Metrics Table
resource "google_bigquery_dataset" "telemetry_ds" {
  dataset_id                  = "telemetry"
  friendly_name               = "MedQuAD Telemetry Dataset"
  description                 = "Aggregated latency, token, and cost telemetry for ADK multi-agent pipelines"
  location                    = var.region
  default_table_expiration_ms = 7776000000 # 90 days
}

resource "google_bigquery_table" "agent_metrics" {
  dataset_id = google_bigquery_dataset.telemetry_ds.dataset_id
  table_id   = "agent_metrics"

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  schema = <<EOF
[
  {"name": "query_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "session_id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
  {"name": "category", "type": "STRING", "mode": "NULLABLE"},
  {"name": "prompt_tokens", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "completion_tokens", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "cached_tokens", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "total_tokens", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "latency_ms", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "ttft_ms", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "estimated_cost_usd", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "safe_refusal", "type": "BOOLEAN", "mode": "NULLABLE"},
  {"name": "citations_count", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "model_name", "type": "STRING", "mode": "NULLABLE"}
]
EOF
}

# 5. Cloud Run Service: MedQuAD Multi-Agent Backend
resource "google_cloud_run_v2_service" "backend" {
  name     = "medquad-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.runtime_sa.email

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    containers {
      image = var.backend_image

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "2000m"
          memory = "2Gi"
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "USE_MOCK_SEARCH"
        value = "false"
      }
      env {
        name  = "VERTEX_DATASTORE_ID"
        value = "medquad-corpus-v1"
      }
      env {
        name  = "VERTEX_AI_SEARCH_DATASTORE_ID"
        value = "medquad-corpus-v1"
      }
      env {
        name  = "VERTEX_AI_SEARCH_ENGINE_ID"
        value = "medquad-search-app-v2"
      }
      env {
        name  = "MEDQUAD_CORPUS_PATH"
        value = "data/full_medquad.json"
      }
      env {
        name  = "BIGQUERY_TELEMETRY_TABLE"
        value = "${var.project_id}.telemetry.agent_metrics"
      }
      env {
        name  = "ROOT_ORCHESTRATOR_MODEL"
        value = "gemini-2.5-flash"
      }
      env {
        name  = "RESEARCHER_MODEL"
        value = "gemini-2.5-pro"
      }
      env {
        name  = "REVIEWER_MODEL"
        value = "gemini-3.5-flash"
      }
    }
  }

  depends_on = [google_project_service.apis, google_project_iam_member.sa_roles]
}

# 6. Cloud Run Service: React Frontend
resource "google_cloud_run_v2_service" "frontend" {
  name     = "medquad-frontend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = var.frontend_image

      resources {
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}

# Allow invoker access based on organization policy
locals {
  invoker_members = toset([
    var.invoker_member,
    "user:admin@asadpatel.altostrat.com",
  ])
}

resource "google_cloud_run_v2_service_iam_member" "backend_invoker" {
  for_each = local.invoker_members
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = each.key
}

resource "google_cloud_run_v2_service_iam_member" "frontend_invoker" {
  for_each = local.invoker_members
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = each.key
}

# 7. Cloud Scheduler: Automated Nightly Clinical Conversation Audit
resource "google_cloud_scheduler_job" "nightly_validation_audit" {
  name             = "medquad-nightly-validation-audit"
  description      = "Executes post-hoc clinical conversation audit pipeline across stored sessions every night at midnight UTC"
  schedule         = "0 0 * * *"
  time_zone        = "Etc/UTC"
  attempt_deadline = "600s"

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.backend.uri}/api/v1/evaluations/validate"
    body        = base64encode("{\"min_faithfulness\": 3.5, \"min_relevance\": 3.5}")
    headers = {
      "Content-Type" = "application/json"
    }

    oidc_token {
      service_account_email = google_service_account.runtime_sa.email
      audience              = google_cloud_run_v2_service.backend.uri
    }
  }

  retry_config {
    retry_count          = 3
    min_backoff_duration = "10s"
    max_backoff_duration = "300s"
  }

  depends_on = [
    google_cloud_run_v2_service.backend,
    google_project_service.apis,
    google_cloud_run_v2_service_iam_member.backend_invoker,
  ]
}

