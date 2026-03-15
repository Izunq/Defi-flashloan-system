"""
Google Cloud Platform Integration Module
Provides seamless integration with GCP services for the Artemis AI Core
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

# GCP imports
from google.cloud import storage
from google.cloud import pubsub_v1
from google.cloud import bigquery
from google.cloud import monitoring_v3
from google.cloud import logging as cloud_logging
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

class GCPIntegration:
    """Google Cloud Platform service integration"""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.region = os.getenv("GCP_REGION", "us-central1")
        
        # Initialize clients
        self._init_clients()
        
        # Bucket names
        self.logs_bucket = os.getenv("LOGS_BUCKET")
        self.reports_bucket = os.getenv("REPORTS_BUCKET")
        self.models_bucket = os.getenv("MODELS_BUCKET")
        
        # Pub/Sub configuration
        self.pubsub_topic = os.getenv("PUBSUB_TOPIC")
        self.pubsub_subscription = os.getenv("PUBSUB_SUBSCRIPTION")
        
        # BigQuery configuration
        self.bigquery_dataset = os.getenv("BIGQUERY_DATASET")
        
        logger.info("GCP Integration initialized")
    
    def _init_clients(self):
        """Initialize GCP service clients"""
        try:
            # Storage client
            self.storage_client = storage.Client(project=self.project_id)
            
            # Pub/Sub clients
            self.publisher = pubsub_v1.PublisherClient()
            self.subscriber = pubsub_v1.SubscriberClient()
            
            # BigQuery client
            self.bigquery_client = bigquery.Client(project=self.project_id)
            
            # Monitoring client
            self.monitoring_client = monitoring_v3.MetricServiceClient()
            
            # Cloud Logging client
            self.logging_client = cloud_logging.Client(project=self.project_id)
            
            logger.info("GCP clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize GCP clients: {e}")
            raise

class GCPStorageManager:
    """Manages Cloud Storage operations"""
    
    def __init__(self, gcp_integration: GCPIntegration):
        self.gcp = gcp_integration
        self.client = gcp_integration.storage_client
    
    async def upload_file(self, bucket_name: str, file_path: str, 
                         destination_name: str) -> str:
        """Upload file to Cloud Storage"""
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(destination_name)
            
            blob.upload_from_filename(file_path)
            
            logger.info(f"File {file_path} uploaded to {bucket_name}/{destination_name}")
            return f"gs://{bucket_name}/{destination_name}"
            
        except Exception as e:
            logger.error(f"Failed to upload file to GCS: {e}")
            raise
    
    async def upload_data(self, bucket_name: str, data: str, 
                         destination_name: str) -> str:
        """Upload data directly to Cloud Storage"""
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(destination_name)
            
            blob.upload_from_string(data)
            
            logger.info(f"Data uploaded to {bucket_name}/{destination_name}")
            return f"gs://{bucket_name}/{destination_name}"
            
        except Exception as e:
            logger.error(f"Failed to upload data to GCS: {e}")
            raise
    
    async def download_file(self, bucket_name: str, source_name: str, 
                           destination_path: str) -> bool:
        """Download file from Cloud Storage"""
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(source_name)
            
            blob.download_to_filename(destination_path)
            
            logger.info(f"File downloaded from {bucket_name}/{source_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from GCS: {e}")
            return False
    
    async def list_files(self, bucket_name: str, prefix: str = "") -> List[str]:
        """List files in Cloud Storage bucket"""
        try:
            bucket = self.client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)
            
            return [blob.name for blob in blobs]
            
        except Exception as e:
            logger.error(f"Failed to list files in GCS: {e}")
            return []

class GCPPubSubManager:
    """Manages Pub/Sub messaging"""
    
    def __init__(self, gcp_integration: GCPIntegration):
        self.gcp = gcp_integration
        self.publisher = gcp_integration.publisher
        self.subscriber = gcp_integration.subscriber
        self.topic_path = self.publisher.topic_path(
            gcp_integration.project_id, 
            gcp_integration.pubsub_topic
        )
        self.subscription_path = self.subscriber.subscription_path(
            gcp_integration.project_id,
            gcp_integration.pubsub_subscription
        )
    
    async def publish_message(self, data: Dict[str, Any]) -> str:
        """Publish message to Pub/Sub topic"""
        try:
            message_data = json.dumps(data).encode("utf-8")
            future = self.publisher.publish(self.topic_path, message_data)
            message_id = future.result()
            
            logger.info(f"Published message {message_id} to {self.topic_path}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to publish message to Pub/Sub: {e}")
            raise
    
    async def publish_trading_data(self, trading_data: Dict[str, Any]) -> str:
        """Publish trading data to Pub/Sub"""
        message = {
            "type": "trading_data",
            "timestamp": datetime.now().isoformat(),
            "data": trading_data
        }
        return await self.publish_message(message)
    
    async def publish_ai_event(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """Publish AI event to Pub/Sub"""
        message = {
            "type": "ai_event",
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": event_data
        }
        return await self.publish_message(message)

class GCPBigQueryManager:
    """Manages BigQuery operations"""
    
    def __init__(self, gcp_integration: GCPIntegration):
        self.gcp = gcp_integration
        self.client = gcp_integration.bigquery_client
        self.dataset_id = gcp_integration.bigquery_dataset
    
    async def insert_trading_data(self, trading_records: List[Dict[str, Any]]) -> bool:
        """Insert trading data into BigQuery"""
        try:
            table_id = f"{self.gcp.project_id}.{self.dataset_id}.trading_data"
            table = self.client.get_table(table_id)
            
            errors = self.client.insert_rows_json(table, trading_records)
            
            if errors:
                logger.error(f"Failed to insert trading data: {errors}")
                return False
            
            logger.info(f"Inserted {len(trading_records)} trading records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert trading data into BigQuery: {e}")
            return False
    
    async def query_trading_analytics(self, query: str) -> List[Dict[str, Any]]:
        """Execute analytics query on trading data"""
        try:
            job = self.client.query(query)
            results = job.result()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed to execute BigQuery analytics: {e}")
            return []
    
    async def get_performance_metrics(self, 
                                    start_date: datetime, 
                                    end_date: datetime) -> Dict[str, Any]:
        """Get performance metrics from BigQuery"""
        query = f"""
        SELECT 
            COUNT(*) as total_trades,
            SUM(profit_loss) as total_profit,
            AVG(profit_loss) as avg_profit,
            MIN(timestamp) as first_trade,
            MAX(timestamp) as last_trade
        FROM `{self.gcp.project_id}.{self.dataset_id}.trading_data`
        WHERE timestamp BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
        """
        
        results = await self.query_trading_analytics(query)
        return results[0] if results else {}

class GCPMonitoringManager:
    """Manages Cloud Monitoring and alerting"""
    
    def __init__(self, gcp_integration: GCPIntegration):
        self.gcp = gcp_integration
        self.client = gcp_integration.monitoring_client
        self.project_name = f"projects/{gcp_integration.project_id}"
    
    async def create_custom_metric(self, metric_type: str, value: float, 
                                  labels: Dict[str, str] = None) -> bool:
        """Create custom metric in Cloud Monitoring"""
        try:
            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/{metric_type}"
            series.resource.type = "cloud_run_revision"
            series.resource.labels["project_id"] = self.gcp.project_id
            series.resource.labels["service_name"] = "artemis-ai-core"
            series.resource.labels["revision_name"] = "artemis-ai-core-latest"
            series.resource.labels["location"] = self.gcp.region
            
            if labels:
                for key, val in labels.items():
                    series.metric.labels[key] = val
            
            now = datetime.now()
            seconds = int(now.timestamp())
            nanos = int((now.timestamp() - seconds) * 10**9)
            interval = monitoring_v3.TimeInterval(
                {"end_time": {"seconds": seconds, "nanos": nanos}}
            )
            point = monitoring_v3.Point(
                {"interval": interval, "value": {"double_value": value}}
            )
            series.points = [point]
            
            self.client.create_time_series(
                name=self.project_name, 
                time_series=[series]
            )
            
            logger.info(f"Created custom metric: {metric_type} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create custom metric: {e}")
            return False
    
    async def record_trading_metric(self, metric_name: str, value: float, 
                                   strategy: str = None) -> bool:
        """Record trading-specific metric"""
        labels = {}
        if strategy:
            labels["strategy"] = strategy
        
        return await self.create_custom_metric(
            f"trading/{metric_name}", 
            value, 
            labels
        )
    
    async def record_ai_metric(self, metric_name: str, value: float, 
                              model: str = None) -> bool:
        """Record AI-specific metric"""
        labels = {}
        if model:
            labels["model"] = model
        
        return await self.create_custom_metric(
            f"ai/{metric_name}", 
            value, 
            labels
        )

class GCPLoggingManager:
    """Manages Cloud Logging"""
    
    def __init__(self, gcp_integration: GCPIntegration):
        self.gcp = gcp_integration
        self.client = gcp_integration.logging_client
        self.logger = self.client.logger("artemis-ai-core")
    
    async def log_trading_event(self, event_type: str, data: Dict[str, Any], 
                               severity: str = "INFO") -> bool:
        """Log trading event to Cloud Logging"""
        try:
            log_entry = {
                "message": f"Trading event: {event_type}",
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            self.logger.log_struct(log_entry, severity=severity)
            return True
            
        except Exception as e:
            logger.error(f"Failed to log trading event: {e}")
            return False
    
    async def log_ai_interaction(self, query: str, response: str, 
                                model: str, duration: float) -> bool:
        """Log AI interaction to Cloud Logging"""
        try:
            log_entry = {
                "message": "AI interaction",
                "query": query,
                "response_length": len(response),
                "model": model,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.log_struct(log_entry, severity="INFO")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log AI interaction: {e}")
            return False

# Main GCP service manager
class GCPServiceManager:
    """Main manager for all GCP services"""
    
    def __init__(self):
        self.integration = GCPIntegration()
        self.storage = GCPStorageManager(self.integration)
        self.pubsub = GCPPubSubManager(self.integration)
        self.bigquery = GCPBigQueryManager(self.integration)
        self.monitoring = GCPMonitoringManager(self.integration)
        self.logging = GCPLoggingManager(self.integration)
        
        logger.info("GCP Service Manager initialized")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all GCP services"""
        health = {
            "storage": False,
            "pubsub": False,
            "bigquery": False,
            "monitoring": False,
            "logging": False
        }
        
        try:
            # Test storage
            buckets = list(self.storage.client.list_buckets(max_results=1))
            health["storage"] = True
        except:
            pass
        
        try:
            # Test Pub/Sub
            await self.pubsub.publish_message({"test": "health_check"})
            health["pubsub"] = True
        except:
            pass
        
        try:
            # Test BigQuery
            list(self.bigquery.client.list_datasets(max_results=1))
            health["bigquery"] = True
        except:
            pass
        
        try:
            # Test monitoring
            await self.monitoring.create_custom_metric("health_check", 1.0)
            health["monitoring"] = True
        except:
            pass
        
        try:
            # Test logging
            await self.logging.log_trading_event("health_check", {})
            health["logging"] = True
        except:
            pass
        
        return health
    
    async def backup_system_state(self) -> str:
        """Backup system state to Cloud Storage"""
        try:
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "health_check": await self.health_check(),
                "system_info": {
                    "project_id": self.integration.project_id,
                    "region": self.integration.region
                }
            }
            
            backup_name = f"system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            await self.storage.upload_data(
                self.integration.logs_bucket,
                json.dumps(backup_data, indent=2),
                f"backups/{backup_name}"
            )
            
            logger.info(f"System state backed up: {backup_name}")
            return backup_name
            
        except Exception as e:
            logger.error(f"Failed to backup system state: {e}")
            raise
