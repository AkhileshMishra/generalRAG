variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_connector_id" {
  type = string
}

variable "api_service_account" {
  type = string
}

variable "worker_service_account" {
  type = string
}

resource "google_cloud_run_v2_service" "api" {
  name     = "generalrag-api-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = var.api_service_account
    timeout         = "3600s"

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/generalrag/api:latest"

      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "gemini-api-key"
            version = "latest"
          }
        }
      }

      env {
        name = "VESPA_ENDPOINT"
        value_source {
          secret_key_ref {
            secret  = "vespa-endpoint"
            version = "latest"
          }
        }
      }

      env {
        name = "DB_CONNECTION_STRING"
        value_source {
          secret_key_ref {
            secret  = "db-connection-string"
            version = "latest"
          }
        }
      }

      env {
        name = "JWT_SECRET"
        value_source {
          secret_key_ref {
            secret  = "jwt-secret"
            version = "latest"
          }
        }
      }
    }

    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = 10
    }

    vpc_access {
      connector = var.vpc_connector_id
      egress    = "PRIVATE_RANGES_ONLY"
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

resource "google_cloud_run_v2_service" "worker" {
  name     = "generalrag-worker-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = var.worker_service_account
    timeout         = "3600s"

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/generalrag/worker:latest"

      resources {
        limits = {
          cpu    = "4"
          memory = "8Gi"
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "gemini-api-key"
            version = "latest"
          }
        }
      }

      env {
        name = "VESPA_ENDPOINT"
        value_source {
          secret_key_ref {
            secret  = "vespa-endpoint"
            version = "latest"
          }
        }
      }

      env {
        name = "DB_CONNECTION_STRING"
        value_source {
          secret_key_ref {
            secret  = "db-connection-string"
            version = "latest"
          }
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    vpc_access {
      connector = var.vpc_connector_id
      egress    = "PRIVATE_RANGES_ONLY"
    }
  }
}

resource "google_cloud_run_service_iam_member" "api_public" {
  count    = var.environment == "dev" ? 1 : 0
  location = var.region
  project  = var.project_id
  service  = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "api_url" {
  value = google_cloud_run_v2_service.api.uri
}

output "worker_url" {
  value = google_cloud_run_v2_service.worker.uri
}
