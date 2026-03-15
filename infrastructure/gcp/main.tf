# Google Cloud Platform Terraform Configuration
# Main configuration for GCP resources

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Data sources
data "google_client_config" "default" {}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "sqladmin.googleapis.com",
    "storage-api.googleapis.com",
    "cloudfunctions.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudkms.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "bigquery.googleapis.com",
    "dataflow.googleapis.com",
    "aiplatform.googleapis.com"
  ])

  service = each.key
  project = var.project_id

  disable_dependent_services = true
}

# VPC Network
resource "google_compute_network" "main" {
  name                    = "${var.project_name}-vpc"
  auto_create_subnetworks = false
  routing_mode           = "GLOBAL"

  depends_on = [google_project_service.apis]
}

# Subnet for GKE cluster
resource "google_compute_subnetwork" "gke_subnet" {
  name          = "${var.project_name}-gke-subnet"
  ip_cidr_range = "10.1.0.0/16"
  region        = var.region
  network       = google_compute_network.main.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.2.0.0/16"
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.3.0.0/16"
  }
}

# Firewall rules
resource "google_compute_firewall" "allow_internal" {
  name    = "${var.project_name}-allow-internal"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/8"]
}

resource "google_compute_firewall" "allow_http_https" {
  name    = "${var.project_name}-allow-http-https"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-server", "https-server"]
}

# GKE Cluster
resource "google_container_cluster" "primary" {
  name     = "${var.project_name}-gke-cluster"
  location = var.region
  
  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.main.name
  subnetwork = google_compute_subnetwork.gke_subnet.name

  # Networking configuration
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Enable network policy
  network_policy {
    enabled = true
  }

  # Enable Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Master authorized networks (restrict access to cluster master)
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "All networks"
    }
  }

  # Addons configuration
  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
  }

  depends_on = [google_project_service.apis]
}

# Separately Managed Node Pool
resource "google_container_node_pool" "primary_nodes" {
  name       = "${var.project_name}-node-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.gke_num_nodes

  node_config {
    preemptible  = var.use_preemptible_nodes
    machine_type = var.gke_machine_type

    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    service_account = google_service_account.gke_nodes.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      env = var.environment
    }

    tags = ["gke-node", "${var.project_name}-gke"]

    metadata = {
      disable-legacy-endpoints = "true"
    }
  }

  autoscaling {
    min_node_count = var.gke_min_nodes
    max_node_count = var.gke_max_nodes
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# Service account for GKE nodes
resource "google_service_account" "gke_nodes" {
  account_id   = "${var.project_name}-gke-nodes"
  display_name = "GKE Node Service Account"
}

# IAM bindings for GKE node service account
resource "google_project_iam_member" "gke_nodes" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/storage.objectViewer"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}

# Cloud SQL Instance
resource "google_sql_database_instance" "main" {
  name             = "${var.project_name}-db-instance"
  database_version = "POSTGRES_14"
  region           = var.region

  settings {
    tier = var.db_tier
    
    backup_configuration {
      enabled    = true
      start_time = "03:00"
    }

    ip_configuration {
      ipv4_enabled    = true
      authorized_networks {
        value = "0.0.0.0/0"
        name  = "allow-all"
      }
    }

    database_flags {
      name  = "log_statement"
      value = "all"
    }
  }

  deletion_protection = false

  depends_on = [google_project_service.apis]
}

# Database
resource "google_sql_database" "database" {
  name     = var.database_name
  instance = google_sql_database_instance.main.name
}

# Database user
resource "google_sql_user" "users" {
  name     = var.database_user
  instance = google_sql_database_instance.main.name
  password = var.database_password
}

# Cloud Storage Buckets
resource "google_storage_bucket" "logs" {
  name     = "${var.project_name}-logs-${random_id.bucket_suffix.hex}"
  location = "US"

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  versioning {
    enabled = true
  }
}

resource "google_storage_bucket" "reports" {
  name     = "${var.project_name}-reports-${random_id.bucket_suffix.hex}"
  location = "US"

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "models" {
  name     = "${var.project_name}-ml-models-${random_id.bucket_suffix.hex}"
  location = "US"

  uniform_bucket_level_access = true
}

resource "random_id" "bucket_suffix" {
  byte_length = 8
}

# Pub/Sub Topic for real-time data
resource "google_pubsub_topic" "trading_data" {
  name = "${var.project_name}-trading-data"

  depends_on = [google_project_service.apis]
}

# Pub/Sub Subscription
resource "google_pubsub_subscription" "trading_data_sub" {
  name  = "${var.project_name}-trading-data-sub"
  topic = google_pubsub_topic.trading_data.name

  message_retention_duration = "1200s"
  retain_acked_messages      = true

  ack_deadline_seconds = 20

  expiration_policy {
    ttl = "300000.5s"
  }
}

# Cloud KMS Key Ring
resource "google_kms_key_ring" "key_ring" {
  name     = "${var.project_name}-key-ring"
  location = var.region

  depends_on = [google_project_service.apis]
}

# Cloud KMS Crypto Key
resource "google_kms_crypto_key" "secret_key" {
  name     = "${var.project_name}-secret-key"
  key_ring = google_kms_key_ring.key_ring.id

  lifecycle {
    prevent_destroy = true
  }
}

# BigQuery Dataset
resource "google_bigquery_dataset" "trading_analytics" {
  dataset_id  = "${replace(var.project_name, "-", "_")}_trading_analytics"
  description = "Trading data analytics dataset"
  location    = "US"

  depends_on = [google_project_service.apis]
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run" {
  account_id   = "${var.project_name}-cloud-run"
  display_name = "Cloud Run Service Account"
}

# IAM bindings for Cloud Run service account
resource "google_project_iam_member" "cloud_run" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/storage.objectAdmin",
    "roles/pubsub.publisher",
    "roles/pubsub.subscriber",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/aiplatform.user"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}
