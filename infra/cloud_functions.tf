resource "google_storage_bucket" "function_source" {
  name                        = "${var.project_id}-${var.app_name}-functions"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
}

resource "google_cloudfunctions2_function" "resume_parser" {
  name        = "${var.app_name}-resume-parser"
  location    = var.region
  description = "PDF to JSON resume parser"

  build_config {
    runtime     = "python311"
    entry_point = "parse_resume"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source.name
        object = google_storage_bucket_object.function_zip.name
      }
    }
  }

  service_config {
    max_instance_count = 10
    min_instance_count = 0
    available_memory   = "512Mi"
    timeout_seconds    = 300
    
    environment_variables = {
      PROJECT_ID = var.project_id
    }

    service_account_email = google_service_account.function_service_account.email
  }

  event_trigger {
    trigger_region = var.region
    event_type     = "google.cloud.storage.object.v1.finalized"
    
    event_filters {
      attribute = "bucket"
      value     = google_storage_bucket.resume_uploads.name
    }
  }
}

resource "google_storage_bucket" "resume_uploads" {
  name                        = "${var.project_id}-${var.app_name}-resumes"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

resource "google_storage_bucket_object" "function_zip" {
  name   = "resume-parser-${timestamp()}.zip"
  bucket = google_storage_bucket.function_source.name
  source = "../functions/resume-parser.zip"

  lifecycle {
    ignore_changes = [source]
  }
}

resource "google_service_account" "function_service_account" {
  account_id   = "${var.app_name}-function"
  display_name = "Cloud Function Service Account"
}

resource "google_project_iam_member" "function_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.function_service_account.email}"
}

resource "google_project_iam_member" "function_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.function_service_account.email}"
}

# Cloud Run service for Job Finder
resource "google_cloud_run_v2_service" "job_finder" {
  name     = "job-finder"
  location = var.region

  template {
    scaling {
      max_instance_count = 10
      min_instance_count = 1
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }

    containers {
      image = "gcr.io/${var.project_id}/job-finder:latest"

      resources {
        limits = {
          cpu    = "1000m"
          memory = "2Gi"
        }
      }

      env {
        name  = "JOB_FINDER_DATABASE_URL"
        value = "postgresql://${google_sql_user.iam_user.name}@${google_sql_database_instance.postgres.private_ip_address}/${google_sql_database.database.name}?sslmode=require"
      }

      env {
        name  = "JOB_FINDER_VERTEX_AI_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "JOB_FINDER_VERTEX_AI_LOCATION"
        value = "us-central1"
      }

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }

      ports {
        container_port = 8000
      }

      liveness_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 30
        period_seconds        = 10
      }


    }

    service_account = google_service_account.app_service_account.email
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# IAM policy for Cloud Run service
resource "google_cloud_run_service_iam_member" "job_finder_public" {
  location = google_cloud_run_v2_service.job_finder.location
  service  = google_cloud_run_v2_service.job_finder.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# VPC Connector for Cloud Run
resource "google_vpc_access_connector" "connector" {
  name          = "vpc-con"
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc.name
  region        = var.region
}

# Cloud Scheduler for job cache refresh
resource "google_cloud_run_v2_job" "job_cache_refresh" {
  name     = "job-cache-refresh"
  location = var.region

  template {
    template {
      containers {
        image = "gcr.io/${var.project_id}/job-finder:latest"
        
        command = ["python", "-c", "import asyncio; from main import app; asyncio.run(app.refresh_job_cache())"]
        
        env {
          name  = "JOB_FINDER_DATABASE_URL"
          value = "postgresql://${google_sql_user.iam_user.name}@${google_sql_database_instance.postgres.private_ip_address}/${google_sql_database.database.name}?sslmode=require"
        }

        env {
          name  = "JOB_FINDER_VERTEX_AI_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
      }

      service_account = google_service_account.app_service_account.email
    }
  }
}

# Cloud Scheduler for job cache refresh
resource "google_cloud_scheduler_job" "job_cache_refresh" {
  name             = "job-cache-refresh"
  description      = "Refresh job cache every hour"
  schedule         = "0 * * * *"
  time_zone        = "UTC"
  attempt_deadline = "600s"

  http_target {
    http_method = "POST"
    uri         = "https://job-finder-${var.project_id}-uc.a.run.app/jobs/refresh"

    oidc_token {
      service_account_email = google_service_account.app_service_account.email
    }
  }
}