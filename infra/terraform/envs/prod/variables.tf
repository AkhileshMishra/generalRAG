variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP Region"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Database password"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository in format 'owner/repo'"
  default     = "AkhileshMishra/generalRAG"
}
