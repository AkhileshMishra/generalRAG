variable "project_id" { type = string }
variable "environment" { type = string }

resource "google_service_account" "api" {
  account_id   = "generalrag-api-${var.environment}"
  display_name = "GeneralRAG API Service Account"
  project      = var.project_id
}

resource "google_service_account" "worker" {
  account_id   = "generalrag-worker-${var.environment}"
  display_name = "GeneralRAG Worker Service Account"
  project      = var.project_id
}

resource "google_service_account" "vespa" {
  account_id   = "generalrag-vespa-${var.environment}"
  display_name = "GeneralRAG Vespa Service Account"
  project      = var.project_id
}

output "api_service_account" { value = google_service_account.api.email }
output "worker_service_account" { value = google_service_account.worker.email }
output "vespa_service_account" { value = google_service_account.vespa.email }
