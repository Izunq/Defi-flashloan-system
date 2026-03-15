# Monitoring and Alerting configuration for GCP

# Notification channel for email alerts
resource "google_monitoring_notification_channel" "email" {
  count        = var.notification_email != "" ? 1 : 0
  display_name = "Email Notifications"
  type         = "email"

  labels = {
    email_address = var.notification_email
  }

  depends_on = [google_project_service.apis]
}

# Uptime check for Artemis AI Core
resource "google_monitoring_uptime_check_config" "artemis_uptime" {
  display_name = "Artemis AI Core Uptime Check"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path         = "/health"
    port         = "443"
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = replace(google_cloud_run_service.artemis_ai_core.status[0].url, "https://", "")
    }
  }

  depends_on = [google_project_service.apis]
}

# Uptime check for Frontend
resource "google_monitoring_uptime_check_config" "frontend_uptime" {
  display_name = "Frontend Uptime Check"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path         = "/"
    port         = "443"
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = replace(google_cloud_run_service.frontend.status[0].url, "https://", "")
    }
  }

  depends_on = [google_project_service.apis]
}

# Alert policy for Artemis AI Core downtime
resource "google_monitoring_alert_policy" "artemis_downtime" {
  count        = var.enable_monitoring ? 1 : 0
  display_name = "Artemis AI Core Downtime"
  combiner     = "OR"

  conditions {
    display_name = "Artemis AI Core is down"

    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type=\"uptime_url\""
      duration        = "300s"
      comparison      = "COMPARISON_LT"
      threshold_value = 1

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_NEXT_OLDER"
      }
    }
  }

  notification_channels = var.notification_email != "" ? [google_monitoring_notification_channel.email[0].id] : []

  alert_strategy {
    auto_close = "1800s"
  }

  depends_on = [google_project_service.apis]
}

# Alert policy for high error rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  count        = var.enable_monitoring ? 1 : 0
  display_name = "High Error Rate"
  combiner     = "OR"

  conditions {
    display_name = "Error rate is above 5%"

    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.labels.service_name"]
      }
    }
  }

  notification_channels = var.notification_email != "" ? [google_monitoring_notification_channel.email[0].id] : []

  depends_on = [google_project_service.apis]
}

# Alert policy for high latency
resource "google_monitoring_alert_policy" "high_latency" {
  count        = var.enable_monitoring ? 1 : 0
  display_name = "High Latency"
  combiner     = "OR"

  conditions {
    display_name = "Request latency is above 2 seconds"

    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/request_latencies\" AND resource.type=\"cloud_run_revision\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 2000

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
        group_by_fields      = ["resource.labels.service_name"]
      }
    }
  }

  notification_channels = var.notification_email != "" ? [google_monitoring_notification_channel.email[0].id] : []

  depends_on = [google_project_service.apis]
}

# Alert policy for database connection issues
resource "google_monitoring_alert_policy" "database_connections" {
  count        = var.enable_monitoring ? 1 : 0
  display_name = "Database Connection Issues"
  combiner     = "OR"

  conditions {
    display_name = "Database connections are high"

    condition_threshold {
      filter          = "metric.type=\"cloudsql.googleapis.com/database/postgresql/num_backends\" AND resource.type=\"cloudsql_database\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 80

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = var.notification_email != "" ? [google_monitoring_notification_channel.email[0].id] : []

  depends_on = [google_project_service.apis]
}

# Alert policy for storage usage
resource "google_monitoring_alert_policy" "storage_usage" {
  count        = var.enable_monitoring ? 1 : 0
  display_name = "High Storage Usage"
  combiner     = "OR"

  conditions {
    display_name = "Storage bucket usage is above 80%"

    condition_threshold {
      filter          = "metric.type=\"storage.googleapis.com/storage/object_count\" AND resource.type=\"gcs_bucket\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10000

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = var.notification_email != "" ? [google_monitoring_notification_channel.email[0].id] : []

  depends_on = [google_project_service.apis]
}

# Dashboard for system monitoring
resource "google_monitoring_dashboard" "main_dashboard" {
  dashboard_json = jsonencode({
    displayName = "Flash Loan Arbitrage System Dashboard"
    mosaicLayout = {
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "Cloud Run Request Count"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_RATE"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Requests/sec"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width  = 6
          height = 4
          xPos   = 6
          widget = {
            title = "Cloud Run Request Latency"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/request_latencies\" AND resource.type=\"cloud_run_revision\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_DELTA"
                      crossSeriesReducer = "REDUCE_PERCENTILE_95"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Latency (ms)"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width  = 6
          height = 4
          yPos   = 4
          widget = {
            title = "Database Connections"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"cloudsql.googleapis.com/database/postgresql/num_backends\" AND resource.type=\"cloudsql_database\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_MEAN"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Connections"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width  = 6
          height = 4
          xPos   = 6
          yPos   = 4
          widget = {
            title = "Storage Usage"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"storage.googleapis.com/storage/total_bytes\" AND resource.type=\"gcs_bucket\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_MEAN"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Bytes"
                scale = "LINEAR"
              }
            }
          }
        }
      ]
    }
  })

  depends_on = [google_project_service.apis]
}

# Log-based metrics for custom monitoring
resource "google_logging_metric" "trading_errors" {
  name   = "trading_errors"
  filter = "resource.type=\"cloud_run_revision\" AND severity=\"ERROR\" AND textPayload:\"trading\""

  metric_descriptor {
    metric_kind = "COUNTER"
    value_type  = "INT64"
    display_name = "Trading Errors"
  }

  depends_on = [google_project_service.apis]
}

resource "google_logging_metric" "ai_requests" {
  name   = "ai_requests"
  filter = "resource.type=\"cloud_run_revision\" AND textPayload:\"AI request\" OR textPayload:\"Gemini\""

  metric_descriptor {
    metric_kind = "COUNTER"
    value_type  = "INT64"
    display_name = "AI Requests"
  }

  depends_on = [google_project_service.apis]
}
