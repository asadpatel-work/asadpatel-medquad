output "backend_uri" {
  description = "Public URL for MedQuAD Backend Cloud Run service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_uri" {
  description = "Public URL for MedQuAD React Frontend Cloud Run service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "corpus_bucket_name" {
  description = "GCS Bucket for MedQuAD Grounding Corpus"
  value       = google_storage_bucket.corpus_bucket.name
}

output "telemetry_table_id" {
  description = "BigQuery Full Table ID for Agent Telemetry"
  value       = "${google_bigquery_table.agent_metrics.project}:${google_bigquery_table.agent_metrics.dataset_id}.${google_bigquery_table.agent_metrics.table_id}"
}

output "runtime_service_account" {
  description = "Email of the MedQuAD runtime service account"
  value       = google_service_account.runtime_sa.email
}

output "discovery_engine_datastore_id" {
  description = "Vertex AI Search / Discovery Engine Data Store ID"
  value       = google_discovery_engine_data_store.medquad_ds.data_store_id
}

output "discovery_engine_search_engine_id" {
  description = "Vertex AI Search / Discovery Engine Search Engine ID"
  value       = google_discovery_engine_search_engine.medquad_search.engine_id
}

output "nightly_audit_scheduler_id" {
  description = "Cloud Scheduler Job ID for automated nightly conversation validation"
  value       = google_cloud_scheduler_job.nightly_validation_audit.id
}

output "cloud_armor_security_policy_id" {
  description = "Resource ID of the Cloud Armor Layer 7 WAF security policy"
  value       = google_compute_security_policy.cloud_armor_policy.id
}

output "backend_service_id" {
  description = "Global Compute Backend Service ID attaching Cloud Armor to Serverless NEG"
  value       = google_compute_backend_service.backend_service.id
}

output "load_balancer_ip" {
  description = "Global static IP address for the External Load Balancer and IAP entrypoint"
  value       = google_compute_global_address.lb_ip.address
}

output "iap_enabled" {
  description = "Indicates whether Identity-Aware Proxy is actively enforced on backend service"
  value       = var.enable_iap
}

output "cloud_trace_console_url" {
  description = "Direct Google Cloud Console URL for Cloud Trace Explorer"
  value       = "https://console.cloud.google.com/traces/list?project=${var.project_id}"
}

output "wif_provider_id" {
  description = "Workload Identity Provider resource URI to configure in GitHub Secrets"
  value       = "${google_iam_workload_identity_pool.github_pool.name}/providers/${google_iam_workload_identity_pool_provider.github_provider.workload_identity_pool_provider_id}"
}

output "wif_service_account_email" {
  description = "GitHub Actions Service Account email to configure in GitHub Secrets"
  value       = google_service_account.github_actions_sa.email
}


