variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "environment" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "vespa_service_account" {
  type = string
}

resource "google_compute_instance" "vespa" {
  name         = "generalrag-vespa-${var.environment}"
  machine_type = "e2-standard-2"
  zone         = "${var.region}-a"
  project      = var.project_id

  tags = ["vespa"]

  boot_disk {
    initialize_params {
      image = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"
      size  = 50
      type  = "pd-standard"
    }
  }

  network_interface {
    subnetwork = var.subnet_id
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    set -e
    if ! command -v docker &> /dev/null; then
      apt-get update -y
      apt-get install -y docker.io
      systemctl enable docker
      systemctl start docker
    fi
    mkdir -p /opt/vespa-data
    chown -R 1000:1000 /opt/vespa-data
    if ! docker ps --format '{{.Names}}' | grep -q '^vespa$'; then
      docker rm -f vespa 2>/dev/null || true
      docker pull vespaengine/vespa:8
      docker run -d --name vespa --restart=always \
        -p 8080:8080 -p 19071:19071 -p 19092:19092 \
        -v /opt/vespa-data:/opt/vespa/var \
        vespaengine/vespa:8
    fi
  EOF

  service_account {
    email  = var.vespa_service_account
    scopes = ["cloud-platform"]
  }

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
  }

  shielded_instance_config {
    enable_secure_boot = false
  }
}

output "vespa_internal_ip" {
  value = google_compute_instance.vespa.network_interface[0].network_ip
}
