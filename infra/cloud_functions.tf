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