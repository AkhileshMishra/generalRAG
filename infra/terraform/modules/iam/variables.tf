variable "project_id" {
  type = string
}

variable "environment" {
  type    = string
  default = ""
}

variable "api_service_account" {
  type    = string
  default = ""
}

variable "worker_service_account" {
  type    = string
  default = ""
}

variable "raw_pdfs_bucket" {
  type    = string
  default = ""
}

variable "page_crops_bucket" {
  type    = string
  default = ""
}

variable "user_uploads_bucket" {
  type    = string
  default = ""
}
