# IAM bindings - only created when service accounts and buckets are provided

locals {
  create_bindings = var.api_service_account != "" && var.raw_pdfs_bucket != ""
}

# API service account roles
resource "google_project_iam_member" "api_secretmanager" {
  count   = local.create_bindings ? 1 : 0
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${var.api_service_account}"
}

resource "google_project_iam_member" "api_cloudsql" {
  count   = local.create_bindings ? 1 : 0
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${var.api_service_account}"
}

resource "google_storage_bucket_iam_member" "api_raw_pdfs" {
  count  = local.create_bindings ? 1 : 0
  bucket = var.raw_pdfs_bucket
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.api_service_account}"
}

resource "google_storage_bucket_iam_member" "api_crops" {
  count  = local.create_bindings ? 1 : 0
  bucket = var.page_crops_bucket
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.api_service_account}"
}

resource "google_storage_bucket_iam_member" "api_user_uploads" {
  count  = local.create_bindings ? 1 : 0
  bucket = var.user_uploads_bucket
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.api_service_account}"
}

# Worker service account roles
resource "google_project_iam_member" "worker_secretmanager" {
  count   = local.create_bindings ? 1 : 0
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${var.worker_service_account}"
}

resource "google_project_iam_member" "worker_cloudsql" {
  count   = local.create_bindings ? 1 : 0
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${var.worker_service_account}"
}

resource "google_storage_bucket_iam_member" "worker_raw_pdfs" {
  count  = local.create_bindings ? 1 : 0
  bucket = var.raw_pdfs_bucket
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.worker_service_account}"
}

resource "google_storage_bucket_iam_member" "worker_crops" {
  count  = local.create_bindings ? 1 : 0
  bucket = var.page_crops_bucket
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.worker_service_account}"
}

resource "google_storage_bucket_iam_member" "worker_user_uploads" {
  count  = local.create_bindings ? 1 : 0
  bucket = var.user_uploads_bucket
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.worker_service_account}"
}
