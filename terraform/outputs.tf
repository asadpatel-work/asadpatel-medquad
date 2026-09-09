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
