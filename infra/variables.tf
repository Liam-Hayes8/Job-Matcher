variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-west2"
}

variable "zone" {
  description = "The GCP zone"
  type        = string
  default     = "us-west2-a"
}

variable "terraform_state_bucket" {
  description = "GCS bucket for Terraform state"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "job-matcher"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}