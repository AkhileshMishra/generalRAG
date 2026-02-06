variable "project_id" {
  type = string
}

variable "api_service_account" {
  type = string
}

variable "worker_service_account" {
  type = string
}

variable "raw_pdfs_bucket" {
  type = string
}

variable "page_crops_bucket" {
  type = string
}

variable "user_uploads_bucket" {
  type = string
}

# API service account roles
resource "google_project_iam_member" "api_secretmanager" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${var.api_service_account}"
}

resource "google_project_iam_member" "api_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${var.api_service_account}"
}

resource "google_storage_bucket_iam_member" "api_raw_pdfs" {
  bucket = var.raw_pdfs_bucket
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.api_service_account}"
}

resource "google_storage_bucket_iam_member" "api_crops" {
  bucket = var.page_crops_bucket
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.api_service_account}"
}

resource "google_storage_bucket_iam_member" "api_user_uploads" {
  bucket = var.user_uploads_bucket
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.api_service_account}"
}

# Worker service account roles
resource "google_project_iam_member" "worker_secretmanager" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${var.worker_service_account}"
}

resource "google_project_iam_member" "worker_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${var.worker_service_account}"
}

resource "google_storage_bucket_iam_member" "worker_raw_pdfs" {
  bucket = var.raw_pdfs_bucket
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.worker_service_account}"
}

resource "google_storage_bucket_iam_member" "worker_crops" {
  bucket = var.page_crops_bucket
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.worker_service_account}"
}

resource "google_storage_bucket_iam_member" "worker_user_uploads" {
  bucket = var.user_uploads_bucket
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.worker_service_account}"
}
