# Outputs for GCP infrastructure

output "project_id" {
  description = "GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP region"
  value       = var.region
}

# VPC Outputs
output "vpc_name" {
  description = "Name of the VPC"
  value       = google_compute_network.main.name
}

output "vpc_self_link" {
  description = "Self link of the VPC"
  value       = google_compute_network.main.self_link
}

output "subnet_name" {
  description = "Name of the GKE subnet"
  value       = google_compute_subnetwork.gke_subnet.name
}

# GKE Outputs
output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "gke_cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.primary.master_auth.0.cluster_ca_certificate
  sensitive   = true
}

output "gke_service_account_email" {
  description = "Email of the GKE node service account"
  value       = google_service_account.gke_nodes.email
}

# Database Outputs
output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.main.connection_name
}

output "database_public_ip" {
  description = "Public IP of the Cloud SQL instance"
  value       = google_sql_database_instance.main.public_ip_address
}

output "database_private_ip" {
  description = "Private IP of the Cloud SQL instance"
  value       = google_sql_database_instance.main.private_ip_address
}

output "database_name" {
  description = "Name of the database"
  value       = google_sql_database.database.name
}

# Storage Outputs
output "logs_bucket_name" {
  description = "Name of the logs storage bucket"
  value       = google_storage_bucket.logs.name
}

output "reports_bucket_name" {
  description = "Name of the reports storage bucket"
  value       = google_storage_bucket.reports.name
}

output "models_bucket_name" {
  description = "Name of the ML models storage bucket"
  value       = google_storage_bucket.models.name
}

# Pub/Sub Outputs
output "pubsub_topic_name" {
  description = "Name of the Pub/Sub topic"
  value       = google_pubsub_topic.trading_data.name
}

output "pubsub_subscription_name" {
  description = "Name of the Pub/Sub subscription"
  value       = google_pubsub_subscription.trading_data_sub.name
}

# KMS Outputs
output "kms_key_ring_name" {
  description = "Name of the KMS key ring"
  value       = google_kms_key_ring.key_ring.name
}

output "kms_crypto_key_name" {
  description = "Name of the KMS crypto key"
  value       = google_kms_crypto_key.secret_key.name
}

# BigQuery Outputs
output "bigquery_dataset_id" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.trading_analytics.dataset_id
}

# Service Account Outputs
output "cloud_run_service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = google_service_account.cloud_run.email
}

# Kubernetes Config
output "kubernetes_config_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region=${var.region} --project=${var.project_id}"
}

# Cloud Run deployment URLs (will be populated after deployment)
output "artemis_ai_core_url" {
  description = "URL of the deployed Artemis AI Core service"
  value       = "https://artemis-ai-core-${random_id.bucket_suffix.hex}-uc.a.run.app"
}

output "frontend_url" {
  description = "URL of the deployed frontend service"
  value       = "https://flashloan-frontend-${random_id.bucket_suffix.hex}-uc.a.run.app"
}

# Environment variables for applications
output "environment_variables" {
  description = "Environment variables for applications"
  value = {
    GCP_PROJECT_ID         = var.project_id
    GCP_REGION            = var.region
    DATABASE_URL          = "postgresql://${var.database_user}:${var.database_password}@${google_sql_database_instance.main.public_ip_address}:5432/${var.database_name}"
    LOGS_BUCKET           = google_storage_bucket.logs.name
    REPORTS_BUCKET        = google_storage_bucket.reports.name
    MODELS_BUCKET         = google_storage_bucket.models.name
    PUBSUB_TOPIC          = google_pubsub_topic.trading_data.name
    PUBSUB_SUBSCRIPTION   = google_pubsub_subscription.trading_data_sub.name
    BIGQUERY_DATASET      = google_bigquery_dataset.trading_analytics.dataset_id
    KMS_KEY_NAME          = google_kms_crypto_key.secret_key.name
  }
  sensitive = true
}
