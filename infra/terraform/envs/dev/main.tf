terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "generalrag-terraform-state-dev"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region

  default_labels = {
    managed_by  = "github_actions"
    environment = "development"
    cost_center = "ai-infrastructure"
    project     = "generalrag"
  }
}

locals {
  environment = "dev"
}

# Artifact Registry for Docker images
module "artifact_registry" {
  source     = "../../modules/artifact_registry"
  project_id = var.project_id
  region     = var.region
}

module "network" {
  source      = "../../modules/network"
  project_id  = var.project_id
  region      = var.region
  environment = local.environment
}

module "storage" {
  source      = "../../modules/storage"
  project_id  = var.project_id
  region      = var.region
  environment = local.environment
}

# Service accounts only
module "iam" {
  source      = "../../modules/iam"
  project_id  = var.project_id
  environment = local.environment
}

module "secrets" {
  source     = "../../modules/secrets"
  project_id = var.project_id
}

module "database" {
  source      = "../../modules/database"
  project_id  = var.project_id
  region      = var.region
  environment = local.environment
  network_id  = module.network.network_id
  db_password = var.db_password
  depends_on  = [module.network]
}

module "compute" {
  source                 = "../../modules/compute"
  project_id             = var.project_id
  region                 = var.region
  environment            = local.environment
  vpc_connector_id       = module.network.vpc_connector_id
  api_service_account    = module.iam.api_service_account
  worker_service_account = module.iam.worker_service_account
  depends_on             = [module.secrets, module.artifact_registry]
}

# IAM bindings - separate call
module "iam_bindings" {
  source                 = "../../modules/iam"
  project_id             = var.project_id
  environment            = local.environment
  api_service_account    = module.iam.api_service_account
  worker_service_account = module.iam.worker_service_account
  raw_pdfs_bucket        = module.storage.raw_pdfs_bucket
  page_crops_bucket      = module.storage.page_crops_bucket
  user_uploads_bucket    = module.storage.user_uploads_bucket
  depends_on             = [module.iam, module.storage]
}
