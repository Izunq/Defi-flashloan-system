# Cloud Run configuration for Artemis AI Core and Frontend

# Cloud Run service for Artemis AI Core
resource "google_cloud_run_service" "artemis_ai_core" {
  name     = "${var.project_name}-artemis-ai-core"
  location = var.region

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "100"
        "autoscaling.knative.dev/minScale" = "1"
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.main.connection_name
        "run.googleapis.com/execution-environment" = "gen2"
      }
    }

    spec {
      service_account_name = google_service_account.cloud_run.email
      container_concurrency = 80
      timeout_seconds = 300

      containers {
        image = var.artemis_image

        ports {
          container_port = 8082
        }

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
          requests = {
            cpu    = "1"
            memory = "1Gi"
          }
        }

        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "DATABASE_URL"
          value = "postgresql://${var.database_user}:${var.database_password}@/${var.database_name}?host=/cloudsql/${google_sql_database_instance.main.connection_name}"
        }

        env {
          name  = "GOOGLE_API_KEY"
          value = var.gemini_api_key
        }

        env {
          name  = "AI_PROVIDER"
          value = "gemini"
        }

        env {
          name  = "GEMINI_MODEL"
          value = "gemini-1.5-pro"
        }

        env {
          name  = "LOGS_BUCKET"
          value = google_storage_bucket.logs.name
        }

        env {
          name  = "REPORTS_BUCKET"
          value = google_storage_bucket.reports.name
        }

        env {
          name  = "MODELS_BUCKET"
          value = google_storage_bucket.models.name
        }

        env {
          name  = "PUBSUB_TOPIC"
          value = google_pubsub_topic.trading_data.name
        }

        env {
          name  = "BIGQUERY_DATASET"
          value = google_bigquery_dataset.trading_analytics.dataset_id
        }

        env {
          name  = "ETHEREUM_RPC_URL"
          value = var.ethereum_rpc_url
        }

        env {
          name  = "POLYGON_RPC_URL"
          value = var.polygon_rpc_url
        }

        env {
          name  = "BSC_RPC_URL"
          value = var.bsc_rpc_url
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "ARTEMIS_PORT"
          value = "8082"
        }

        env {
          name  = "ARTEMIS_HOST"
          value = "0.0.0.0"
        }

        env {
          name  = "ENABLE_CORS"
          value = "true"
        }

        env {
          name  = "DEBUG"
          value = var.environment == "development" ? "true" : "false"
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.apis]
}

# Cloud Run service for React Frontend
resource "google_cloud_run_service" "frontend" {
  name     = "${var.project_name}-frontend"
  location = var.region

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "100"
        "autoscaling.knative.dev/minScale" = "1"
        "run.googleapis.com/execution-environment" = "gen2"
      }
    }

    spec {
      container_concurrency = 1000
      timeout_seconds = 60

      containers {
        image = var.frontend_image

        ports {
          container_port = 80
        }

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
          requests = {
            cpu    = "0.5"
            memory = "256Mi"
          }
        }

        env {
          name  = "REACT_APP_ARTEMIS_API_URL"
          value = google_cloud_run_service.artemis_ai_core.status[0].url
        }

        env {
          name  = "REACT_APP_ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "REACT_APP_GCP_PROJECT_ID"
          value = var.project_id
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.apis, google_cloud_run_service.artemis_ai_core]
}

# IAM policy to allow public access to Cloud Run services
resource "google_cloud_run_service_iam_binding" "artemis_public" {
  location = google_cloud_run_service.artemis_ai_core.location
  service  = google_cloud_run_service.artemis_ai_core.name
  role     = "roles/run.invoker"
  members = [
    "allUsers"
  ]
}

resource "google_cloud_run_service_iam_binding" "frontend_public" {
  location = google_cloud_run_service.frontend.location
  service  = google_cloud_run_service.frontend.name
  role     = "roles/run.invoker"
  members = [
    "allUsers"
  ]
}

# Cloud Scheduler job for periodic tasks
resource "google_cloud_scheduler_job" "trading_data_sync" {
  name     = "${var.project_name}-trading-data-sync"
  region   = var.region
  schedule = "*/5 * * * *"  # Every 5 minutes

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.artemis_ai_core.status[0].url}/api/sync-trading-data"

    oidc_token {
      service_account_email = google_service_account.cloud_run.email
    }
  }

  depends_on = [google_project_service.apis]
}

# Cloud Scheduler job for strategy optimization
resource "google_cloud_scheduler_job" "strategy_optimization" {
  name     = "${var.project_name}-strategy-optimization"
  region   = var.region
  schedule = "0 */6 * * *"  # Every 6 hours

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.artemis_ai_core.status[0].url}/api/optimize-strategies"

    oidc_token {
      service_account_email = google_service_account.cloud_run.email
    }
  }

  depends_on = [google_project_service.apis]
}
