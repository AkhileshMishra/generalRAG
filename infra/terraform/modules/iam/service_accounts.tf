resource "google_service_account" "api" {
  count        = var.environment != "" ? 1 : 0
  account_id   = "generalrag-api-${var.environment}"
  display_name = "GeneralRAG API Service Account"
  project      = var.project_id
}

resource "google_service_account" "worker" {
  count        = var.environment != "" ? 1 : 0
  account_id   = "generalrag-worker-${var.environment}"
  display_name = "GeneralRAG Worker Service Account"
  project      = var.project_id
}

resource "google_service_account" "vespa" {
  count        = var.environment != "" ? 1 : 0
  account_id   = "generalrag-vespa-${var.environment}"
  display_name = "GeneralRAG Vespa Service Account"
  project      = var.project_id
}

output "api_service_account" {
  value = length(google_service_account.api) > 0 ? google_service_account.api[0].email : ""
}

output "worker_service_account" {
  value = length(google_service_account.worker) > 0 ? google_service_account.worker[0].email : ""
}

output "vespa_service_account" {
  value = length(google_service_account.vespa) > 0 ? google_service_account.vespa[0].email : ""
}
