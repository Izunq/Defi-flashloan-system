# Google Cloud Platform Deployment Scripts

## Prerequisites

Before deploying to GCP, ensure you have:

1. **Google Cloud SDK installed**
   ```bash
   # Windows: Download from https://cloud.google.com/sdk/docs/install
   # Verify installation
   gcloud --version
   ```

2. **GCP Project set up**
   ```bash
   # Create new project (optional)
   gcloud projects create your-flashloan-project --name="Flash Loan Arbitrage"
   
   # Set active project
   gcloud config set project your-flashloan-project
   
   # Enable billing (required)
   # Go to: https://console.cloud.google.com/billing
   ```

3. **Authentication configured**
   ```bash
   # Login to Google Cloud
   gcloud auth login
   
   # Set application default credentials
   gcloud auth application-default login
   ```

## Deployment Steps

### Step 1: Infrastructure Deployment

1. **Navigate to infrastructure directory**
   ```bash
   cd infrastructure/gcp
   ```

2. **Copy and configure variables**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Initialize and deploy with Terraform**
   ```bash
   # Initialize Terraform
   terraform init
   
   # Plan the deployment
   terraform plan
   
   # Apply the infrastructure
   terraform apply
   ```

### Step 2: Container Image Build and Push

1. **Build Artemis AI Core image**
   ```bash
   cd artemis_core
   
   # Build Docker image
   docker build -t gcr.io/YOUR_PROJECT_ID/artemis-ai-core:latest .
   
   # Push to Google Container Registry
   docker push gcr.io/YOUR_PROJECT_ID/artemis-ai-core:latest
   ```

2. **Build Frontend image**
   ```bash
   cd ../
   
   # Build Docker image
   docker build -t gcr.io/YOUR_PROJECT_ID/flashloan-frontend:latest .
   
   # Push to Google Container Registry
   docker push gcr.io/YOUR_PROJECT_ID/flashloan-frontend:latest
   ```

### Step 3: Service Deployment

1. **Deploy to Cloud Run**
   ```bash
   # Deploy Artemis AI Core
   gcloud run deploy artemis-ai-core \
     --image gcr.io/YOUR_PROJECT_ID/artemis-ai-core:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 2 \
     --max-instances 100
   
   # Deploy Frontend
   gcloud run deploy flashloan-frontend \
     --image gcr.io/YOUR_PROJECT_ID/flashloan-frontend:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 512Mi \
     --cpu 1 \
     --max-instances 100
   ```

2. **Configure GKE (Alternative to Cloud Run)**
   ```bash
   # Get cluster credentials
   gcloud container clusters get-credentials flashloan-arbitrage-gke-cluster \
     --region us-central1
   
   # Deploy using Kubernetes manifests
   kubectl apply -f k8s/
   ```

### Step 4: Database Setup

1. **Connect to Cloud SQL**
   ```bash
   # Install Cloud SQL proxy
   curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
   chmod +x cloud_sql_proxy
   
   # Connect to instance
   ./cloud_sql_proxy -instances=YOUR_PROJECT_ID:us-central1:flashloan-arbitrage-db-instance=tcp:5432
   ```

2. **Initialize database schema**
   ```bash
   # Connect using psql
   psql -h 127.0.0.1 -p 5432 -U flashloan_user -d flashloan_db
   
   # Run schema migrations
   \i sql/schema.sql
   ```

### Step 5: Monitoring Setup

1. **Verify monitoring dashboard**
   ```bash
   # Open Cloud Console
   gcloud console --project=YOUR_PROJECT_ID
   # Navigate to Monitoring > Dashboards
   ```

2. **Set up alerting**
   ```bash
   # Configure notification channels
   gcloud alpha monitoring channels create \
     --channel-content-from-file=monitoring/email-channel.yaml
   ```

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the `artemis_core` directory:

```bash
# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# Database
DATABASE_URL=postgresql://flashloan_user:password@/flashloan_db?host=/cloudsql/PROJECT:REGION:INSTANCE

# AI Configuration
GOOGLE_API_KEY=your-gemini-api-key
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-pro

# GCP Services
LOGS_BUCKET=your-logs-bucket
REPORTS_BUCKET=your-reports-bucket
MODELS_BUCKET=your-models-bucket
PUBSUB_TOPIC=your-topic
BIGQUERY_DATASET=your_dataset

# Blockchain RPC URLs
ETHEREUM_RPC_URL=your-ethereum-rpc
POLYGON_RPC_URL=https://polygon-rpc.com
BSC_RPC_URL=https://bsc-dataseed.binance.org

# Application Settings
ARTEMIS_PORT=8082
ARTEMIS_HOST=0.0.0.0
DEBUG=false
ENABLE_CORS=true
```

## Post-Deployment Verification

### Health Checks

1. **Test Artemis AI Core**
   ```bash
   curl https://your-artemis-service-url/health
   ```

2. **Test Frontend**
   ```bash
   curl https://your-frontend-service-url/
   ```

3. **Test Database Connection**
   ```bash
   curl https://your-artemis-service-url/api/database-health
   ```

### Performance Testing

1. **Load test with Apache Bench**
   ```bash
   ab -n 100 -c 10 https://your-artemis-service-url/api/chat
   ```

2. **Monitor metrics**
   ```bash
   # View Cloud Monitoring dashboard
   gcloud monitoring dashboards list
   ```

## Troubleshooting

### Common Issues

1. **Permission Errors**
   ```bash
   # Check IAM permissions
   gcloud projects get-iam-policy YOUR_PROJECT_ID
   
   # Add required roles
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="user:your-email@domain.com" \
     --role="roles/editor"
   ```

2. **Service Account Issues**
   ```bash
   # Create service account key
   gcloud iam service-accounts keys create key.json \
     --iam-account=SERVICE_ACCOUNT_EMAIL
   
   # Set environment variable
   export GOOGLE_APPLICATION_CREDENTIALS="key.json"
   ```

3. **Network Connectivity**
   ```bash
   # Check firewall rules
   gcloud compute firewall-rules list
   
   # Test connectivity
   gcloud compute ssh INSTANCE_NAME --zone=ZONE
   ```

### Log Analysis

1. **View application logs**
   ```bash
   # Cloud Run logs
   gcloud logs read "resource.type=cloud_run_revision" --limit=50
   
   # Specific service logs
   gcloud logs read "resource.labels.service_name=artemis-ai-core" --limit=50
   ```

2. **Error analysis**
   ```bash
   # Filter error logs
   gcloud logs read "severity>=ERROR" --limit=20
   
   # Real-time log streaming
   gcloud logs tail "resource.type=cloud_run_revision"
   ```

## Scaling and Optimization

### Auto-scaling Configuration

1. **Cloud Run auto-scaling**
   ```bash
   gcloud run services update artemis-ai-core \
     --max-instances=1000 \
     --concurrency=80 \
     --cpu-throttling
   ```

2. **GKE auto-scaling**
   ```bash
   # Enable cluster autoscaler
   gcloud container clusters update flashloan-arbitrage-gke-cluster \
     --enable-autoscaling \
     --min-nodes=1 \
     --max-nodes=10 \
     --region=us-central1
   ```

### Cost Optimization

1. **Use preemptible instances**
   ```bash
   # Already configured in Terraform
   # Monitor cost in Cloud Console
   ```

2. **Optimize BigQuery usage**
   ```bash
   # Set up partitioned tables
   # Use clustering for better performance
   # Monitor slot usage
   ```

## Multi-Cloud Setup

### Cross-Cloud Integration

1. **VPN Connections**
   ```bash
   # Set up Cloud VPN to AWS/Azure
   gcloud compute vpn-tunnels create aws-tunnel \
     --peer-address=AWS_VPN_IP \
     --region=us-central1
   ```

2. **Data Replication**
   ```bash
   # Set up cross-cloud data sync
   # Configure backup strategies
   ```

## Security Hardening

### Network Security

1. **Private clusters**
   ```bash
   # Enable private IP for GKE
   gcloud container clusters update flashloan-arbitrage-gke-cluster \
     --enable-private-nodes \
     --master-ipv4-cidr 172.16.0.32/28
   ```

2. **Firewall rules**
   ```bash
   # Restrict access to specific IPs
   gcloud compute firewall-rules create allow-specific-ips \
     --allow tcp:443 \
     --source-ranges=YOUR_IP_RANGE
   ```

### Identity and Access Management

1. **Service account security**
   ```bash
   # Rotate service account keys regularly
   gcloud iam service-accounts keys create new-key.json \
     --iam-account=SERVICE_ACCOUNT_EMAIL
   ```

2. **Audit logging**
   ```bash
   # Enable audit logs
   gcloud logging sinks create audit-sink \
     bigquery.googleapis.com/projects/PROJECT/datasets/DATASET
   ```

## Maintenance and Updates

### Regular Maintenance Tasks

1. **Update containers**
   ```bash
   # Build and deploy new versions
   docker build -t gcr.io/PROJECT/artemis-ai-core:v2.0 .
   gcloud run deploy artemis-ai-core --image gcr.io/PROJECT/artemis-ai-core:v2.0
   ```

2. **Database maintenance**
   ```bash
   # Backup database
   gcloud sql export sql INSTANCE_NAME gs://BUCKET/backup.sql
   
   # Update instance
   gcloud sql instances patch INSTANCE_NAME --backup-start-time=03:00
   ```

3. **Certificate renewal**
   ```bash
   # Managed certificates are auto-renewed
   # Monitor expiration dates
   ```

Remember to regularly review and update your infrastructure to maintain security and performance!
