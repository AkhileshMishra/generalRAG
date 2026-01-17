variable "project_id" { type = string }

resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  project   = var.project_id
  replication { auto {} }
}

resource "google_secret_manager_secret" "vespa_endpoint" {
  secret_id = "vespa-endpoint"
  project   = var.project_id
  replication { auto {} }
}

resource "google_secret_manager_secret" "db_connection_string" {
  secret_id = "db-connection-string"
  project   = var.project_id
  replication { auto {} }
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "jwt-secret"
  project   = var.project_id
  replication { auto {} }
}

output "gemini_api_key_id" { value = google_secret_manager_secret.gemini_api_key.id }
output "vespa_endpoint_id" { value = google_secret_manager_secret.vespa_endpoint.id }
output "db_connection_string_id" { value = google_secret_manager_secret.db_connection_string.id }
output "jwt_secret_id" { value = google_secret_manager_secret.jwt_secret.id }
