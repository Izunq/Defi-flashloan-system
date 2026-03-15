# Variables for GCP infrastructure

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "project_name" {
  description = "The project name used for resource naming"
  type        = string
  default     = "flashloan-arbitrage"
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
}

# GKE Variables
variable "gke_num_nodes" {
  description = "Number of nodes in the GKE cluster"
  type        = number
  default     = 2
}

variable "gke_min_nodes" {
  description = "Minimum number of nodes in the GKE cluster"
  type        = number
  default     = 1
}

variable "gke_max_nodes" {
  description = "Maximum number of nodes in the GKE cluster"
  type        = number
  default     = 10
}

variable "gke_machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-standard-4"
}

variable "use_preemptible_nodes" {
  description = "Use preemptible nodes for cost savings"
  type        = bool
  default     = true
}

# Database Variables
variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}

variable "database_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "flashloan_db"
}

variable "database_user" {
  description = "Database user name"
  type        = string
  default     = "flashloan_user"
}

variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# Cloud Run Variables
variable "artemis_image" {
  description = "Container image for Artemis AI Core"
  type        = string
  default     = "gcr.io/PROJECT_ID/artemis-ai-core:latest"
}

variable "frontend_image" {
  description = "Container image for React frontend"
  type        = string
  default     = "gcr.io/PROJECT_ID/flashloan-frontend:latest"
}

# AI/ML Variables
variable "gemini_api_key" {
  description = "Google Gemini API key"
  type        = string
  sensitive   = true
}

# Blockchain RPC URLs
variable "ethereum_rpc_url" {
  description = "Ethereum RPC URL"
  type        = string
  default     = ""
}

variable "polygon_rpc_url" {
  description = "Polygon RPC URL"
  type        = string
  default     = "https://polygon-rpc.com"
}

variable "bsc_rpc_url" {
  description = "BSC RPC URL"
  type        = string
  default     = "https://bsc-dataseed.binance.org"
}

# Monitoring Variables
variable "notification_email" {
  description = "Email for monitoring notifications"
  type        = string
  default     = ""
}

variable "enable_monitoring" {
  description = "Enable Cloud Monitoring and alerting"
  type        = bool
  default     = true
}

# Cost optimization variables
variable "enable_autoscaling" {
  description = "Enable autoscaling for services"
  type        = bool
  default     = true
}

variable "use_spot_instances" {
  description = "Use spot instances where possible"
  type        = bool
  default     = true
}
