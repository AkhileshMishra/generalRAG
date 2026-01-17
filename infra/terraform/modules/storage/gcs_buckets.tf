variable "project_id" { type = string }
variable "region" { type = string }
variable "environment" { type = string }

resource "google_storage_bucket" "raw_pdfs" {
  name          = "${var.project_id}-generalrag-${var.environment}-raw-pdfs"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment == "dev"

  uniform_bucket_level_access = true
  
  versioning { enabled = true }
}

resource "google_storage_bucket" "page_crops" {
  name          = "${var.project_id}-generalrag-${var.environment}-page-crops"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment == "dev"

  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "user_uploads" {
  name          = "${var.project_id}-generalrag-${var.environment}-user-uploads"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment == "dev"

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition { age = 30 }
    action { type = "Delete" }
  }
}

output "raw_pdfs_bucket" { value = google_storage_bucket.raw_pdfs.name }
output "page_crops_bucket" { value = google_storage_bucket.page_crops.name }
output "user_uploads_bucket" { value = google_storage_bucket.user_uploads.name }
