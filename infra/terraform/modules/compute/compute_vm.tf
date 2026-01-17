variable "project_id" { type = string }
variable "region" { type = string }
variable "zone" { type = string }
variable "environment" { type = string }
variable "subnet_id" { type = string }
variable "vespa_service_account" { type = string }

resource "google_compute_instance" "vespa" {
  name         = "generalrag-vespa-${var.environment}"
  machine_type = var.environment == "prod" ? "e2-standard-8" : "e2-standard-4"
  zone         = var.zone
  project      = var.project_id

  tags = ["vespa"]

  boot_disk {
    initialize_params {
      image = "projects/cos-cloud/global/images/family/cos-stable"
      size  = var.environment == "prod" ? 500 : 100
      type  = "pd-ssd"
    }
  }

  network_interface {
    subnetwork = var.subnet_id
  }

  metadata = {
    gce-container-declaration = yamlencode({
      spec = {
        containers = [{
          image = "vespaengine/vespa:8"
          volumeMounts = [{
            name      = "vespa-data"
            mountPath = "/opt/vespa/var"
          }]
        }]
        volumes = [{
          name = "vespa-data"
          hostPath = { path = "/mnt/disks/vespa-data" }
        }]
        restartPolicy = "Always"
      }
    })
  }

  service_account {
    email  = var.vespa_service_account
    scopes = ["cloud-platform"]
  }

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
  }

  shielded_instance_config {
    enable_secure_boot = true
  }
}

output "vespa_internal_ip" { value = google_compute_instance.vespa.network_interface[0].network_ip }
