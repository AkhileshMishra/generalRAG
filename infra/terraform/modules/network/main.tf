variable "project_id" { type = string }
variable "region" { type = string }
variable "environment" { type = string }

resource "google_compute_network" "main" {
  name                    = "generalrag-${var.environment}"
  auto_create_subnetworks = false
  project                 = var.project_id
}

resource "google_compute_subnetwork" "main" {
  name          = "generalrag-${var.environment}-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.main.id
  project       = var.project_id

  private_ip_google_access = true
}

resource "google_compute_firewall" "vespa_internal" {
  name    = "generalrag-${var.environment}-vespa-internal"
  network = google_compute_network.main.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["8080", "19071", "19092"]
  }

  source_ranges = ["10.0.0.0/24"]
  target_tags   = ["vespa"]
}

resource "google_compute_firewall" "allow_iap" {
  name    = "generalrag-${var.environment}-allow-iap"
  network = google_compute_network.main.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["vespa"]
}

resource "google_compute_global_address" "private_ip" {
  name          = "generalrag-${var.environment}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
  project       = var.project_id
}

resource "google_service_networking_connection" "private_vpc" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip.name]
}

resource "google_vpc_access_connector" "connector" {
  name          = "generalrag-${var.environment}-vpc"
  region        = var.region
  project       = var.project_id
  network       = google_compute_network.main.name
  ip_cidr_range = "10.8.0.0/28"
}

output "network_id" { value = google_compute_network.main.id }
output "subnet_id" { value = google_compute_subnetwork.main.id }
output "vpc_connector_id" { value = google_vpc_access_connector.connector.id }
