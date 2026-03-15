# ☁️ AWS CLOUD DEPLOYMENT ARCHITECTURE
**Enterprise-Grade AWS Infrastructure for DeFi Arbitrage Platform**

## 🏗️ AWS CLOUD ARCHITECTURE OVERVIEW

### **Multi-Region, High-Availability Design**

```yaml
# AWS Infrastructure Overview
aws_architecture:
  primary_region: us-east-1
  disaster_recovery_region: us-west-2
  edge_locations: global
  
  compute:
    trading_engine: ECS Fargate + EC2 Spot (cost optimization)
    matlab_compute: EC2 GPU instances (p4d.24xlarge)
    database_engine: RDS Aurora Serverless v2
    cache_layer: ElastiCache Redis Cluster
    
  security:
    key_management: AWS KMS + CloudHSM
    secrets: AWS Secrets Manager + Parameter Store
    identity: IAM + AWS SSO + Cognito
    networking: VPC + Private Subnets + NAT Gateway
    
  storage:
    hot_data: EBS gp3 + EFS
    warm_data: S3 Standard-IA
    cold_data: S3 Glacier Instant Retrieval
    backup: S3 Cross-Region Replication
    
  monitoring:
    logging: CloudWatch + CloudTrail
    metrics: CloudWatch + X-Ray
    alerting: SNS + EventBridge + Lambda
    security: GuardDuty + Security Hub + Inspector
```

---

## 🚀 CORE INFRASTRUCTURE COMPONENTS

### **1. ECS Fargate Trading Engine**

#### **Auto-Scaling Trading Containers**
```yaml
# trading-engine-ecs.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: trading-engine-config
data:
  AWS_REGION: us-east-1
  CLUSTER_NAME: arbitrage-trading-cluster
  
---
# ECS Service Definition
Resources:
  TradingEngineService:
    Type: AWS::ECS::Service
    Properties:
      Cluster: !Ref TradingCluster
      TaskDefinition: !Ref TradingTaskDefinition
      DesiredCount: 3
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          SecurityGroups:
            - !Ref TradingSecurityGroup
          Subnets:
            - !Ref PrivateSubnet1
            - !Ref PrivateSubnet2
          AssignPublicIp: DISABLED
      
      # Auto-scaling configuration
      ServiceTags:
        - Key: Environment
          Value: Production
        - Key: Application
          Value: ArbitrageTrading
          
  TradingTaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: arbitrage-trading
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      Cpu: 4096
      Memory: 8192
      ExecutionRoleArn: !Ref ECSExecutionRole
      TaskRoleArn: !Ref ECSTaskRole
      
      ContainerDefinitions:
        - Name: trading-engine
          Image: !Sub ${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/arbitrage-trading:latest
          Essential: true
          
          Environment:
            - Name: AWS_DEFAULT_REGION
              Value: !Ref AWS::Region
            - Name: RDS_ENDPOINT
              Value: !GetAtt AuroraCluster.Endpoint.Address
            - Name: REDIS_ENDPOINT
              Value: !GetAtt RedisCluster.RedisEndpoint.Address
              
          Secrets:
            - Name: DATABASE_PASSWORD
              ValueFrom: !Ref DatabasePassword
            - Name: API_KEYS
              ValueFrom: !Ref APIKeysSecret
              
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: /ecs/arbitrage-trading
              awslogs-region: !Ref AWS::Region
              awslogs-stream-prefix: ecs
              
          HealthCheck:
            Command:
              - CMD-SHELL
              - curl -f http://localhost:8080/health || exit 1
            Interval: 30
            Timeout: 5
            Retries: 3
```

#### **Python Application with AWS SDK Integration**
```python
# aws_trading_engine.py
import boto3
import asyncio
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

# AWS service clients
class AWSServicesManager:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.session = boto3.Session(region_name=region)
        
        # Initialize AWS services
        self.secrets_manager = self.session.client('secretsmanager')
        self.kms = self.session.client('kms')
        self.rds = self.session.client('rds')
        self.s3 = self.session.client('s3')
        self.cloudwatch = self.session.client('cloudwatch')
        self.sns = self.session.client('sns')
        self.ssm = self.session.client('ssm')
        
        # ECS metadata for service discovery
        self.ecs_metadata = self._get_ecs_metadata()
        
    async def get_secret(self, secret_name: str) -> Dict:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.secrets_manager.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except Exception as e:
            logging.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise
    
    async def encrypt_sensitive_data(self, data: str, key_id: str) -> str:
        """Encrypt data using AWS KMS"""
        try:
            response = self.kms.encrypt(
                KeyId=key_id,
                Plaintext=data.encode('utf-8')
            )
            return response['CiphertextBlob'].hex()
        except Exception as e:
            logging.error(f"KMS encryption failed: {e}")
            raise
    
    async def send_alert(self, topic_arn: str, message: str, subject: str):
        """Send alert via SNS"""
        try:
            self.sns.publish(
                TopicArn=topic_arn,
                Message=message,
                Subject=subject
            )
        except Exception as e:
            logging.error(f"SNS alert failed: {e}")
    
    async def put_metric(self, metric_name: str, value: float, unit: str = 'Count'):
        """Send custom metric to CloudWatch"""
        try:
            self.cloudwatch.put_metric_data(
                Namespace='ArbitrageTrading',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': value,
                        'Unit': unit,
                        'Dimensions': [
                            {
                                'Name': 'Environment',
                                'Value': 'Production'
                            },
                            {
                                'Name': 'Service',
                                'Value': 'TradingEngine'
                            }
                        ]
                    }
                ]
            )
        except Exception as e:
            logging.error(f"CloudWatch metric failed: {e}")

class CloudArbitrageEngine:
    def __init__(self):
        self.aws_services = AWSServicesManager()
        self.trading_config = None
        self.is_running = False
        
    async def initialize(self):
        """Initialize cloud trading engine"""
        # Load configuration from AWS Systems Manager
        self.trading_config = await self._load_config_from_ssm()
        
        # Initialize database connections
        await self._setup_database_connections()
        
        # Setup monitoring and alerting
        await self._setup_monitoring()
        
        logging.info("Cloud arbitrage engine initialized successfully")
    
    async def _load_config_from_ssm(self) -> Dict:
        """Load configuration from AWS Systems Manager Parameter Store"""
        try:
            parameters = [
                '/arbitrage/trading/max_position_size',
                '/arbitrage/trading/risk_tolerance',
                '/arbitrage/trading/enabled_strategies',
                '/arbitrage/aws/region',
                '/arbitrage/aws/kms_key_id'
            ]
            
            config = {}
            for param in parameters:
                response = self.aws_services.ssm.get_parameter(
                    Name=param,
                    WithDecryption=True
                )
                key = param.split('/')[-1]
                config[key] = response['Parameter']['Value']
                
            return config
        except Exception as e:
            logging.error(f"Failed to load config from SSM: {e}")
            raise
    
    async def execute_arbitrage_trade(self, opportunity: Dict) -> Dict:
        """Execute arbitrage trade with AWS integration"""
        try:
            # Log trade attempt
            await self.aws_services.put_metric('TradeAttempts', 1)
            
            # Encrypt sensitive trade data
            encrypted_data = await self.aws_services.encrypt_sensitive_data(
                json.dumps(opportunity),
                self.trading_config['kms_key_id']
            )
            
            # Execute trade logic here
            result = await self._execute_trade_logic(opportunity)
            
            # Store encrypted trade record in S3
            await self._store_trade_record(encrypted_data, result)
            
            # Send success metric
            await self.aws_services.put_metric('TradeSuccesses', 1)
            
            return result
            
        except Exception as e:
            # Send failure metric and alert
            await self.aws_services.put_metric('TradeFailures', 1)
            await self.aws_services.send_alert(
                self.trading_config['alert_topic_arn'],
                f"Trade execution failed: {str(e)}",
                "Trading Alert: Execution Failure"
            )
            raise
```

### **2. MATLAB Compute Cluster on AWS**

#### **GPU-Optimized EC2 Instances**
```yaml
# matlab-compute-cluster.yml
Resources:
  MATLABAutoScalingGroup:
    Type: AWS::AutoScaling::AutoScalingGroup
    Properties:
      VPCZoneIdentifier:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2
      LaunchTemplate:
        LaunchTemplateId: !Ref MATLABLaunchTemplate
        Version: !GetAtt MATLABLaunchTemplate.LatestVersionNumber
      MinSize: 1
      MaxSize: 10
      DesiredCapacity: 2
      TargetGroupARNs:
        - !Ref MATLABTargetGroup
      Tags:
        - Key: Name
          Value: MATLAB-Compute-Node
          PropagateAtLaunch: true
        - Key: Environment
          Value: Production
          PropagateAtLaunch: true
          
  MATLABLaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateName: MATLAB-Compute-Template
      LaunchTemplateData:
        InstanceType: p4d.24xlarge  # 8 NVIDIA A100 GPUs
        ImageId: ami-0abcdef1234567890  # Custom AMI with MATLAB
        SecurityGroupIds:
          - !Ref MATLABSecurityGroup
        IamInstanceProfile:
          Arn: !GetAtt MATLABInstanceProfile.Arn
        
        UserData:
          Fn::Base64:
            !Sub |
              #!/bin/bash
              # Install MATLAB Parallel Server
              wget https://matlab-downloads.s3.amazonaws.com/matlab-parallel-server.tar.gz
              tar -xzf matlab-parallel-server.tar.gz
              
              # Configure for GPU acceleration
              nvidia-smi
              matlab -batch "parpool('local', 8); gpuDeviceCount"
              
              # Start MATLAB Engine API server
              python -c "import matlab.engine; matlab.engine.start_matlab()"
              
              # Register with load balancer
              aws elbv2 register-targets --target-group-arn ${MATLABTargetGroup} \
                --targets Id=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
        
        TagSpecifications:
          - ResourceType: instance
            Tags:
              - Key: Name
                Value: MATLAB-Compute-Node
```

#### **MATLAB Distributed Computing Integration**
```matlab
% aws_matlab_arbitrage_optimizer.m
classdef AWSMATLABOptimizer < handle
    properties
        cluster
        gpuPool
        awsSession
        s3Bucket
        cloudWatchClient
    end
    
    methods
        function obj = AWSMATLABOptimizer()
            % Initialize AWS MATLAB optimizer
            obj.setupAWSIntegration();
            obj.setupParallelComputing();
            obj.setupGPUComputing();
        end
        
        function setupAWSIntegration(obj)
            % Setup AWS SDK for MATLAB
            obj.awsSession = aws.Session();
            obj.s3Bucket = 'arbitrage-matlab-data';
            obj.cloudWatchClient = aws.CloudWatch.CloudWatchClient();
        end
        
        function setupParallelComputing(obj)
            % Setup parallel computing cluster
            obj.cluster = parcluster('local');
            obj.cluster.NumWorkers = 32; % Scale based on instance type
            
            % Configure cluster for AWS
            obj.cluster.AdditionalProperties.AdditionalPaths = {'/opt/matlab/arbitrage'};
            obj.cluster.saveProfile;
        end
        
        function setupGPUComputing(obj)
            % Setup GPU pool for acceleration
            if gpuDeviceCount > 0
                obj.gpuPool = parpool('local', gpuDeviceCount);
                fprintf('Initialized %d GPU devices\n', gpuDeviceCount);
            end
        end
        
        function result = optimizeArbitragePortfolio(obj, marketData)
            % Optimize arbitrage portfolio using AWS infrastructure
            
            tic; % Start timing
            
            % Upload market data to S3 for backup
            obj.uploadToS3(marketData, 'market-data');
            
            % Parallel optimization across multiple GPUs
            spmd (obj.gpuPool.NumWorkers)
                localGPU = gpuDevice(labindex);
                localData = gpuArray(marketData.prices(labindex:numlabs:end, :));
                
                % GPU-accelerated optimization
                localResult = obj.optimizeOnGPU(localData);
            end
            
            % Combine results from all workers
            result = obj.combineOptimizationResults(localResult);
            
            executionTime = toc;
            
            % Send metrics to CloudWatch
            obj.sendCloudWatchMetric('OptimizationTime', executionTime);
            obj.sendCloudWatchMetric('OptimizationSuccess', 1);
            
            % Store results in S3
            obj.uploadToS3(result, 'optimization-results');
        end
        
        function localResult = optimizeOnGPU(obj, gpuData)
            % GPU-accelerated optimization function
            
            % Define objective function for GPU
            objective = @(weights) -obj.calculateSharpeRatioGPU(weights, gpuData);
            
            % Constraints
            numAssets = size(gpuData, 2);
            Aeq = ones(1, numAssets, 'gpuArray');
            beq = gpuArray(1);
            lb = gpuArray(zeros(numAssets, 1));
            ub = gpuArray(ones(numAssets, 1) * 0.3); % Max 30% per asset
            
            % GPU-optimized solver
            options = optimoptions('fmincon', ...
                'Algorithm', 'interior-point', ...
                'UseParallel', true, ...
                'MaxIterations', 1000);
            
            initialWeights = gpuArray(ones(numAssets, 1) / numAssets);
            [optimalWeights, fval] = fmincon(objective, initialWeights, ...
                [], [], Aeq, beq, lb, ub, [], options);
            
            localResult.weights = gather(optimalWeights);
            localResult.value = gather(fval);
        end
        
        function uploadToS3(obj, data, prefix)
            % Upload data to S3 with encryption
            filename = sprintf('%s/%s_%s.mat', prefix, ...
                datestr(now, 'yyyy-mm-dd-HH-MM-SS'), ...
                char(java.util.UUID.randomUUID));
            
            % Save to temporary file
            tempFile = [tempdir, filename];
            save(tempFile, 'data', '-v7.3');
            
            % Upload to S3 with server-side encryption
            s3Object = aws.S3.S3Object(obj.s3Bucket, filename);
            s3Object.upload(tempFile, 'ServerSideEncryption', 'AES256');
            
            % Clean up
            delete(tempFile);
        end
        
        function sendCloudWatchMetric(obj, metricName, value)
            % Send custom metric to CloudWatch
            try
                metricData = aws.CloudWatch.MetricDatum();
                metricData.MetricName = metricName;
                metricData.Value = value;
                metricData.Unit = 'Count';
                metricData.Timestamp = datetime('now');
                
                request = aws.CloudWatch.PutMetricDataRequest();
                request.Namespace = 'ArbitrageTrading/MATLAB';
                request.MetricData = metricData;
                
                obj.cloudWatchClient.putMetricData(request);
            catch ME
                warning('Failed to send CloudWatch metric: %s', ME.message);
            end
        end
    end
end
```

### **3. AWS Database Architecture**

#### **Aurora Serverless v2 for Trading Data**
```yaml
# aurora-database.yml
Resources:
  AuroraSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for Aurora cluster
      SubnetIds:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2
        - !Ref PrivateSubnet3
      Tags:
        - Key: Name
          Value: arbitrage-aurora-subnet-group
          
  AuroraCluster:
    Type: AWS::RDS::DBCluster
    Properties:
      Engine: aurora-postgresql
      EngineVersion: "14.6"
      EngineMode: provisioned
      ServerlessV2ScalingConfiguration:
        MinCapacity: 0.5
        MaxCapacity: 64
      
      DatabaseName: arbitrage_trading
      MasterUsername: postgres
      MasterUserPassword: !Ref DatabasePassword
      
      VpcSecurityGroupIds:
        - !Ref DatabaseSecurityGroup
      DBSubnetGroupName: !Ref AuroraSubnetGroup
      
      BackupRetentionPeriod: 35
      PreferredBackupWindow: "03:00-04:00"
      PreferredMaintenanceWindow: "Sun:04:00-Sun:05:00"
      
      # Encryption
      StorageEncrypted: true
      KmsKeyId: !Ref DatabaseKMSKey
      
      # Performance Insights
      EnablePerformanceInsights: true
      PerformanceInsightsRetentionPeriod: 7
      
      # Enhanced Monitoring
      MonitoringInterval: 60
      MonitoringRoleArn: !GetAtt EnhancedMonitoringRole.Arn
      
      DeletionProtection: true
      
      Tags:
        - Key: Environment
          Value: Production
        - Key: Application
          Value: ArbitrageTrading
          
  AuroraWriter:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceClass: db.serverless
      DBClusterIdentifier: !Ref AuroraCluster
      Engine: aurora-postgresql
      PubliclyAccessible: false
      
  AuroraReader:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceClass: db.serverless
      DBClusterIdentifier: !Ref AuroraCluster
      Engine: aurora-postgresql
      PubliclyAccessible: false
```

#### **DBeaver Cloud Connection Configuration**
```python
# aws_database_manager.py
import boto3
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import json

class AWSDatabaseManager:
    def __init__(self):
        self.rds_client = boto3.client('rds')
        self.secrets_client = boto3.client('secretsmanager')
        self.connections = {}
        
    async def setup_dbeaver_connections(self):
        """Setup DBeaver connections for AWS Aurora"""
        
        # Get database credentials from Secrets Manager
        db_credentials = await self._get_database_credentials()
        
        # Aurora Writer (Primary)
        writer_endpoint = await self._get_aurora_endpoint('writer')
        self.connections['aurora_writer'] = {
            'host': writer_endpoint,
            'port': 5432,
            'database': 'arbitrage_trading',
            'username': db_credentials['username'],
            'password': db_credentials['password'],
            'ssl_mode': 'require',
            'connection_pool': {
                'min_connections': 5,
                'max_connections': 50,
                'connection_timeout': 30
            }
        }
        
        # Aurora Reader (Read Replicas)
        reader_endpoint = await self._get_aurora_endpoint('reader')
        self.connections['aurora_reader'] = {
            'host': reader_endpoint,
            'port': 5432,
            'database': 'arbitrage_trading',
            'username': db_credentials['username'],
            'password': db_credentials['password'],
            'ssl_mode': 'require',
            'read_only': True,
            'connection_pool': {
                'min_connections': 10,
                'max_connections': 100,
                'connection_timeout': 30
            }
        }
        
        # Generate DBeaver connection file
        await self._generate_dbeaver_config()
    
    async def _get_database_credentials(self) -> dict:
        """Retrieve database credentials from AWS Secrets Manager"""
        try:
            response = self.secrets_client.get_secret_value(
                SecretId='arbitrage/database/credentials'
            )
            return json.loads(response['SecretString'])
        except Exception as e:
            raise Exception(f"Failed to retrieve database credentials: {e}")
    
    async def _get_aurora_endpoint(self, endpoint_type: str) -> str:
        """Get Aurora cluster endpoint"""
        try:
            response = self.rds_client.describe_db_clusters(
                DBClusterIdentifier='arbitrage-aurora-cluster'
            )
            
            cluster = response['DBClusters'][0]
            if endpoint_type == 'writer':
                return cluster['Endpoint']
            else:
                return cluster['ReaderEndpoint']
                
        except Exception as e:
            raise Exception(f"Failed to get Aurora endpoint: {e}")
    
    async def _generate_dbeaver_config(self):
        """Generate DBeaver configuration for team use"""
        dbeaver_config = {
            'connections': {
                'aurora-writer': {
                    'driver': 'postgresql',
                    'url': f"jdbc:postgresql://{self.connections['aurora_writer']['host']}:5432/arbitrage_trading",
                    'properties': {
                        'user': self.connections['aurora_writer']['username'],
                        'ssl': 'true',
                        'sslmode': 'require',
                        'ApplicationName': 'DBeaver-ArbitrageTrading'
                    },
                    'provider-properties': {
                        'show-non-default-db': 'true',
                        'show-template-db': 'false',
                        'read-only': 'false'
                    }
                },
                'aurora-reader': {
                    'driver': 'postgresql',
                    'url': f"jdbc:postgresql://{self.connections['aurora_reader']['host']}:5432/arbitrage_trading",
                    'properties': {
                        'user': self.connections['aurora_reader']['username'],
                        'ssl': 'true',
                        'sslmode': 'require',
                        'ApplicationName': 'DBeaver-ArbitrageTrading-ReadOnly'
                    },
                    'provider-properties': {
                        'show-non-default-db': 'true',
                        'show-template-db': 'false',
                        'read-only': 'true'
                    }
                }
            }
        }
        
        # Save configuration for team distribution
        with open('/shared/dbeaver/connections.json', 'w') as f:
            json.dump(dbeaver_config, f, indent=2)
```

### **4. AWS Security Integration**

#### **KMS + CloudHSM for Cryptographic Operations**
```python
# aws_security_manager.py
import boto3
import json
from typing import Dict, List
import logging

class AWSSecurityManager:
    def __init__(self):
        self.kms_client = boto3.client('kms')
        self.secrets_client = boto3.client('secretsmanager')
        self.hsm_client = boto3.client('cloudhsmv2')
        self.iam_client = boto3.client('iam')
        
        # KMS keys for different purposes
        self.kms_keys = {
            'trading_data': 'arn:aws:kms:us-east-1:123456789012:key/trading-data-key',
            'transaction_signing': 'arn:aws:kms:us-east-1:123456789012:key/transaction-key',
            'backup_encryption': 'arn:aws:kms:us-east-1:123456789012:key/backup-key'
        }
        
    async def setup_keepassxc_aws_integration(self):
        """Setup KeePassXC with AWS Secrets Manager backend"""
        
        # Create secret for KeePassXC master password
        master_password_secret = {
            'description': 'KeePassXC master password for arbitrage system',
            'master_password': self._generate_secure_password(32),
            'keyfile_s3_location': 's3://arbitrage-secure-keys/keepassxc/master.key',
            'rotation_schedule': 'rate(30 days)'
        }
        
        await self._store_secret('arbitrage/keepassxc/master', master_password_secret)
        
        # Setup automatic rotation
        await self._setup_secret_rotation('arbitrage/keepassxc/master')
        
    async def setup_gnupg_hsm_integration(self):
        """Setup GnuPG with CloudHSM integration"""
        
        # Create HSM cluster if not exists
        hsm_cluster = await self._ensure_hsm_cluster()
        
        # Configure GnuPG for HSM
        gnupg_hsm_config = {
            'hsm_cluster_id': hsm_cluster['ClusterId'],
            'hsm_ip_address': hsm_cluster['Hsms'][0]['EniIp'],
            'pkcs11_library': '/opt/cloudhsm/lib/libcloudhsm_pkcs11.so',
            'key_label': 'arbitrage-trading-key',
            'pin': await self._get_hsm_pin()
        }
        
        await self._store_secret('arbitrage/gnupg/hsm-config', gnupg_hsm_config)
        
    async def encrypt_trading_data(self, data: str, purpose: str = 'trading_data') -> str:
        """Encrypt trading data using AWS KMS"""
        try:
            key_id = self.kms_keys.get(purpose, self.kms_keys['trading_data'])
            
            response = self.kms_client.encrypt(
                KeyId=key_id,
                Plaintext=data.encode('utf-8'),
                EncryptionContext={
                    'purpose': purpose,
                    'application': 'arbitrage-trading',
                    'timestamp': str(datetime.now().timestamp())
                }
            )
            
            return response['CiphertextBlob'].hex()
            
        except Exception as e:
            logging.error(f"KMS encryption failed: {e}")
            raise
    
    async def decrypt_trading_data(self, encrypted_data: str, purpose: str = 'trading_data') -> str:
        """Decrypt trading data using AWS KMS"""
        try:
            ciphertext_blob = bytes.fromhex(encrypted_data)
            
            response = self.kms_client.decrypt(
                CiphertextBlob=ciphertext_blob,
                EncryptionContext={
                    'purpose': purpose,
                    'application': 'arbitrage-trading'
                }
            )
            
            return response['Plaintext'].decode('utf-8')
            
        except Exception as e:
            logging.error(f"KMS decryption failed: {e}")
            raise
    
    async def _ensure_hsm_cluster(self) -> Dict:
        """Ensure CloudHSM cluster exists"""
        try:
            # Check if cluster exists
            clusters = self.hsm_client.describe_clusters()
            
            for cluster in clusters['Clusters']:
                if cluster['ClusterState'] == 'ACTIVE':
                    return cluster
            
            # Create new cluster if none active
            response = self.hsm_client.create_cluster(
                SubnetIds=[
                    'subnet-12345678',  # Private subnet 1
                    'subnet-87654321'   # Private subnet 2
                ],
                HsmType='hsm1.medium',
                SourceBackupId=None  # Create new cluster
            )
            
            cluster_id = response['Cluster']['ClusterId']
            
            # Wait for cluster to be active
            waiter = self.hsm_client.get_waiter('cluster_active')
            waiter.wait(ClusterId=cluster_id)
            
            return response['Cluster']
            
        except Exception as e:
            logging.error(f"HSM cluster setup failed: {e}")
            raise
```

### **5. Monitoring and Alerting**

#### **CloudWatch Dashboard for Trading Metrics**
```python
# aws_monitoring_dashboard.py
import boto3
import json
from typing import Dict, List

class AWSMonitoringDashboard:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.sns = boto3.client('sns')
        self.eventbridge = boto3.client('events')
        
    async def create_trading_dashboard(self):
        """Create comprehensive CloudWatch dashboard"""
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0, "y": 0,
                    "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            ["ArbitrageTrading", "TradeSuccesses", {"stat": "Sum"}],
                            ["ArbitrageTrading", "TradeFailures", {"stat": "Sum"}],
                            ["ArbitrageTrading", "TotalProfit", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": "us-east-1",
                        "title": "Trading Performance"
                    }
                },
                {
                    "type": "metric",
                    "x": 12, "y": 0,
                    "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/ECS", "CPUUtilization", "ServiceName", "arbitrage-trading"],
                            ["AWS/ECS", "MemoryUtilization", "ServiceName", "arbitrage-trading"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "ECS Performance"
                    }
                },
                {
                    "type": "metric",
                    "x": 0, "y": 6,
                    "width": 12, "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/RDS", "DatabaseConnections", "DBClusterIdentifier", "arbitrage-aurora-cluster"],
                            ["AWS/RDS", "CPUUtilization", "DBClusterIdentifier", "arbitrage-aurora-cluster"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Database Performance"
                    }
                },
                {
                    "type": "log",
                    "x": 12, "y": 6,
                    "width": 12, "height": 6,
                    "properties": {
                        "query": "SOURCE '/aws/ecs/arbitrage-trading'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 100",
                        "region": "us-east-1",
                        "title": "Recent Errors"
                    }
                }
            ]
        }
        
        self.cloudwatch.put_dashboard(
            DashboardName='ArbitrageTradingDashboard',
            DashboardBody=json.dumps(dashboard_body)
        )
    
    async def setup_alerting(self):
        """Setup CloudWatch alarms and SNS notifications"""
        
        # Create SNS topics
        critical_alerts_topic = await self._create_sns_topic('arbitrage-critical-alerts')
        warning_alerts_topic = await self._create_sns_topic('arbitrage-warning-alerts')
        
        # Critical alarms
        await self._create_alarm(
            alarm_name='TradingEngine-HighFailureRate',
            metric_name='TradeFailures',
            threshold=10,
            comparison_operator='GreaterThanThreshold',
            evaluation_periods=2,
            alarm_actions=[critical_alerts_topic]
        )
        
        await self._create_alarm(
            alarm_name='Database-HighCPU',
            metric_name='CPUUtilization',
            namespace='AWS/RDS',
            threshold=80,
            comparison_operator='GreaterThanThreshold',
            evaluation_periods=3,
            alarm_actions=[warning_alerts_topic]
        )
        
        # Setup EventBridge rules for custom events
        await self._setup_eventbridge_rules()
    
    async def _create_sns_topic(self, topic_name: str) -> str:
        """Create SNS topic for alerts"""
        response = self.sns.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']
        
        # Subscribe email endpoints
        email_endpoints = [
            'security@arbitrage-system.com',
            'trading@arbitrage-system.com',
            'devops@arbitrage-system.com'
        ]
        
        for email in email_endpoints:
            self.sns.subscribe(
                TopicArn=topic_arn,
                Protocol='email',
                Endpoint=email
            )
        
        return topic_arn
```

### **6. Cost Optimization Strategy**

#### **AWS Cost Management**
```yaml
# cost-optimization.yml
cost_optimization:
  compute:
    strategy: "spot_instances_with_on_demand_backup"
    spot_percentage: 70
    savings_target: "60%"
    
    ec2_instances:
      matlab_compute:
        primary: "p4d.24xlarge (Spot)"
        backup: "p3.8xlarge (On-Demand)"
        auto_scaling: true
        
    ecs_fargate:
      spot_capacity_providers: true
      cost_savings: "50-70%"
      
  storage:
    strategy: "intelligent_tiering"
    
    s3_buckets:
      hot_data:
        storage_class: "Standard"
        lifecycle_rules:
          - transition_to_ia: 30
          - transition_to_glacier: 90
          
      backup_data:
        storage_class: "Glacier Instant Retrieval"
        
  database:
    aurora_serverless_v2:
      min_capacity: 0.5
      max_capacity: 64
      auto_pause: true
      pause_delay: 300  # 5 minutes
      
  networking:
    nat_gateway_optimization:
      use_nat_instances: false  # NAT Gateway more reliable
      vpc_endpoints: true       # Reduce data transfer costs
      
estimated_monthly_costs:
  compute: "$15,000 (with 60% spot savings)"
  storage: "$2,000"
  database: "$3,000"
  networking: "$500"
  total: "$20,500"
  
cost_alerts:
  budget_threshold: "$25,000"
  alert_percentage: 80
  notification_frequency: "daily"
```

This comprehensive AWS cloud architecture provides enterprise-grade infrastructure for your arbitrage system with built-in security, scalability, and cost optimization. The system leverages AWS managed services to minimize operational overhead while maximizing performance and reliability.
