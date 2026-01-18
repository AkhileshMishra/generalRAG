variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository in format 'owner/repo'"
}

variable "environment" {
  type        = string
  description = "Environment name (dev, prod)"
}
