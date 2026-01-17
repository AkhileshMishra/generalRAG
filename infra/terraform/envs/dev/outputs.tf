output "api_url" {
  value       = module.compute.api_url
  description = "Cloud Run API URL"
}

output "vespa_internal_ip" {
  value       = module.vespa.vespa_internal_ip
  description = "Vespa VM internal IP"
}

output "raw_pdfs_bucket" {
  value = module.storage.raw_pdfs_bucket
}

output "page_crops_bucket" {
  value = module.storage.page_crops_bucket
}

output "user_uploads_bucket" {
  value = module.storage.user_uploads_bucket
}

output "db_connection_name" {
  value = module.database.instance_connection_name
}
