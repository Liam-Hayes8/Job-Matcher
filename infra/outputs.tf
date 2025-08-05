output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "vpc_name" {
  description = "VPC Network Name"
  value       = google_compute_network.vpc.name
}

output "gke_cluster_name" {
  description = "GKE Cluster Name"
  value       = google_container_cluster.primary.name
}

output "gke_cluster_endpoint" {
  description = "GKE Cluster Endpoint"
  value       = google_container_cluster.primary.endpoint
}

output "artifact_registry_url" {
  description = "Artifact Registry URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_repo.repository_id}"
}

output "database_connection_name" {
  description = "Cloud SQL Connection Name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "database_private_ip" {
  description = "Cloud SQL Private IP"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "function_url" {
  description = "Resume Parser Function URL"
  value       = google_cloudfunctions2_function.resume_parser.url
}

output "resume_upload_bucket" {
  description = "Resume Upload Bucket Name"
  value       = google_storage_bucket.resume_uploads.name
}

output "app_service_account_email" {
  description = "Application Service Account Email"
  value       = google_service_account.app_service_account.email
}