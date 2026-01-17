variable "project_id" { type = string }
variable "region" { type = string }
variable "environment" { type = string }
variable "network_id" { type = string }
variable "db_password" { type = string sensitive = true }

resource "google_sql_database_instance" "main" {
  name             = "generalrag-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region
  project          = var.project_id

  settings {
    tier              = var.environment == "prod" ? "db-custom-2-4096" : "db-f1-micro"
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_size         = var.environment == "prod" ? 50 : 10
    disk_type         = "PD_SSD"

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_id
    }

    backup_configuration {
      enabled            = var.environment == "prod"
      binary_log_enabled = false
    }
  }

  deletion_protection = var.environment == "prod"
}

resource "google_sql_database" "main" {
  name     = "generalrag"
  instance = google_sql_database_instance.main.name
  project  = var.project_id
}

resource "google_sql_user" "app" {
  name     = "app"
  instance = google_sql_database_instance.main.name
  password = var.db_password
  project  = var.project_id
}

output "instance_connection_name" { value = google_sql_database_instance.main.connection_name }
output "private_ip" { value = google_sql_database_instance.main.private_ip_address }
