resource "google_secret_manager_secret" "db_password" {
  secret_id = "${var.app_name}-db-password"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = var.db_password
}

resource "google_secret_manager_secret" "firebase_config" {
  secret_id = "${var.app_name}-firebase-config"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "${var.app_name}-jwt-secret"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "jwt_secret" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = random_password.jwt_secret.result
}

resource "random_password" "jwt_secret" {
  length  = 32
  special = true
}

resource "google_service_account" "app_service_account" {
  account_id   = "${var.app_name}-app"
  display_name = "Job Matcher Application Service Account"
}

resource "google_secret_manager_secret_iam_member" "db_password_access" {
  secret_id = google_secret_manager_secret.db_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app_service_account.email}"
}

resource "google_secret_manager_secret_iam_member" "firebase_config_access" {
  secret_id = google_secret_manager_secret.firebase_config.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app_service_account.email}"
}

resource "google_secret_manager_secret_iam_member" "jwt_secret_access" {
  secret_id = google_secret_manager_secret.jwt_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app_service_account.email}"
}

# Workload identity binding will be configured after GKE cluster is created
# resource "google_service_account_iam_binding" "workload_identity_binding" {
#   service_account_id = google_service_account.app_service_account.name
#   role               = "roles/iam.workloadIdentityUser"
#
#   members = [
#     "serviceAccount:${var.project_id}.svc.id.goog[default/job-matcher-backend]",
#     "serviceAccount:${var.project_id}.svc.id.goog[default/job-matcher-frontend]"
#   ]
# }

# Additional secrets for job finder service
resource "google_secret_manager_secret" "vertex_ai_key" {
  secret_id = "${var.app_name}-vertex-ai-key"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "ats_api_keys" {
  secret_id = "${var.app_name}-ats-api-keys"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "vertex_ai_key_access" {
  secret_id = google_secret_manager_secret.vertex_ai_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app_service_account.email}"
}

resource "google_secret_manager_secret_iam_member" "ats_api_keys_access" {
  secret_id = google_secret_manager_secret.ats_api_keys.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app_service_account.email}"
}