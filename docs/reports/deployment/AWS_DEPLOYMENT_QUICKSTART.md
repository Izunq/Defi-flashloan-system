# 🚀 AWS DEPLOYMENT QUICK START GUIDE

## 📋 PRE-DEPLOYMENT CHECKLIST

### **AWS Account Requirements**
- [ ] AWS Account with billing enabled
- [ ] Service quotas increased for:
  - EC2 GPU instances (p4d.24xlarge): 10 instances
  - ECS Fargate: 1000 vCPUs
  - Aurora Serverless v2: 64 ACUs
  - KMS keys: 100 customer managed keys

### **Development Environment Setup**
- [ ] AWS CLI v2 installed and configured
- [ ] Docker Desktop installed
- [ ] Terraform or AWS CDK installed
- [ ] kubectl installed for EKS (optional)

---

## 🛠️ STEP-BY-STEP DEPLOYMENT

### **Phase 1: Core Infrastructure (Day 1)**

#### **1. VPC and Networking Setup**
```bash
# Create VPC with CloudFormation
aws cloudformation create-stack \
  --stack-name arbitrage-vpc \
  --template-body file://cloudformation/vpc.yml \
  --parameters ParameterKey=Environment,ParameterValue=Production \
  --capabilities CAPABILITY_IAM

# Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name arbitrage-vpc
```

#### **2. Security Infrastructure**
```bash
# Create KMS keys
aws kms create-key \
  --description "Arbitrage Trading Data Encryption" \
  --key-usage ENCRYPT_DECRYPT \
  --key-spec SYMMETRIC_DEFAULT

# Create Secrets Manager secrets
aws secretsmanager create-secret \
  --name "arbitrage/database/credentials" \
  --description "Database credentials for arbitrage system" \
  --secret-string '{"username":"postgres","password":"CHANGE_ME_SECURE_PASSWORD"}'

# Create CloudHSM cluster
aws cloudhsmv2 create-cluster \
  --subnet-ids subnet-12345678 subnet-87654321 \
  --hsm-type hsm1.medium
```

### **Phase 2: Database and Storage (Day 2)**

#### **3. Aurora Serverless v2 Setup**
```bash
# Create Aurora cluster
aws rds create-db-cluster \
  --db-cluster-identifier arbitrage-aurora-cluster \
  --engine aurora-postgresql \
  --engine-version 14.6 \
  --master-username postgres \
  --master-user-password $(aws secretsmanager get-secret-value --secret-id arbitrage/database/credentials --query SecretString --output text | jq -r .password) \
  --serverless-v2-scaling-configuration MinCapacity=0.5,MaxCapacity=64 \
  --storage-encrypted \
  --backup-retention-period 35

# Create Aurora instances
aws rds create-db-instance \
  --db-instance-identifier arbitrage-aurora-writer \
  --db-instance-class db.serverless \
  --engine aurora-postgresql \
  --db-cluster-identifier arbitrage-aurora-cluster

aws rds create-db-instance \
  --db-instance-identifier arbitrage-aurora-reader \
  --db-instance-class db.serverless \
  --engine aurora-postgresql \
  --db-cluster-identifier arbitrage-aurora-cluster
```

#### **4. ElastiCache Redis Setup**
```bash
# Create Redis cluster
aws elasticache create-replication-group \
  --replication-group-id arbitrage-redis \
  --description "Redis cluster for arbitrage system" \
  --num-cache-clusters 3 \
  --cache-node-type cache.r6g.xlarge \
  --engine redis \
  --engine-version 7.0 \
  --port 6379 \
  --cache-subnet-group-name arbitrage-cache-subnet-group \
  --security-group-ids sg-12345678 \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled
```

### **Phase 3: Container Infrastructure (Day 3)**

#### **5. ECS Cluster Setup**
```bash
# Create ECS cluster
aws ecs create-cluster \
  --cluster-name arbitrage-trading-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy capacityProvider=FARGATE_SPOT,weight=3 capacityProvider=FARGATE,weight=1

# Create ECR repositories
aws ecr create-repository --repository-name arbitrage-trading
aws ecr create-repository --repository-name matlab-compute
```

#### **6. Build and Push Docker Images**
```bash
# Build trading engine image
cd docker/trading-engine
docker build -t arbitrage-trading:latest .

# Tag and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

docker tag arbitrage-trading:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/arbitrage-trading:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/arbitrage-trading:latest
```

### **Phase 4: MATLAB Compute Setup (Day 4)**

#### **7. EC2 GPU Instances for MATLAB**
```bash
# Create launch template for MATLAB instances
aws ec2 create-launch-template \
  --launch-template-name matlab-compute-template \
  --launch-template-data '{
    "ImageId": "ami-0abcdef1234567890",
    "InstanceType": "p4d.24xlarge",
    "SecurityGroupIds": ["sg-matlab-compute"],
    "IamInstanceProfile": {"Name": "matlab-compute-role"},
    "UserData": "'$(base64 -w 0 scripts/matlab-setup.sh)'"
  }'

# Create Auto Scaling Group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name matlab-compute-asg \
  --launch-template LaunchTemplateName=matlab-compute-template,Version='$Latest' \
  --min-size 1 \
  --max-size 10 \
  --desired-capacity 2 \
  --vpc-zone-identifier "subnet-12345678,subnet-87654321"
```

### **Phase 5: Application Deployment (Day 5)**

#### **8. Deploy Trading Engine to ECS**
```bash
# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://ecs/trading-task-definition.json

# Create ECS service
aws ecs create-service \
  --cluster arbitrage-trading-cluster \
  --service-name arbitrage-trading-service \
  --task-definition arbitrage-trading:1 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration '{
    "awsvpcConfiguration": {
      "subnets": ["subnet-12345678", "subnet-87654321"],
      "securityGroups": ["sg-trading-engine"],
      "assignPublicIp": "DISABLED"
    }
  }'
```

---

## 📊 MONITORING SETUP

### **CloudWatch Dashboard Creation**
```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
  --dashboard-name ArbitrageTradingDashboard \
  --dashboard-body file://monitoring/dashboard.json

# Create alarms
aws cloudwatch put-metric-alarm \
  --alarm-name TradingEngine-HighCPU \
  --alarm-description "Trading engine high CPU usage" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

---

## 🔐 SECURITY CONFIGURATION

### **IAM Roles and Policies**
```bash
# Create ECS execution role
aws iam create-role \
  --role-name ecsExecutionRole \
  --assume-role-policy-document file://iam/ecs-execution-role-trust.json

aws iam attach-role-policy \
  --role-name ecsExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create custom policy for trading operations
aws iam create-policy \
  --policy-name ArbitrageTradingPolicy \
  --policy-document file://iam/trading-policy.json

aws iam attach-role-policy \
  --role-name ecsExecutionRole \
  --policy-arn arn:aws:iam::123456789012:policy/ArbitrageTradingPolicy
```

---

## 🧪 TESTING AND VALIDATION

### **Infrastructure Testing**
```bash
# Test database connectivity
aws rds describe-db-clusters \
  --db-cluster-identifier arbitrage-aurora-cluster

# Test Redis connectivity
aws elasticache describe-replication-groups \
  --replication-group-id arbitrage-redis

# Test ECS service health
aws ecs describe-services \
  --cluster arbitrage-trading-cluster \
  --services arbitrage-trading-service
```

### **Application Testing**
```python
# Test trading engine health
import requests
import boto3

def test_trading_engine():
    # Get ECS service endpoint
    elbv2 = boto3.client('elbv2')
    response = elbv2.describe_load_balancers(
        Names=['arbitrage-trading-alb']
    )
    
    lb_dns = response['LoadBalancers'][0]['DNSName']
    health_url = f"https://{lb_dns}/health"
    
    # Test health endpoint
    response = requests.get(health_url)
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
    
    print("✅ Trading engine health check passed")

def test_matlab_compute():
    # Test MATLAB compute cluster
    import matlab.engine
    
    try:
        eng = matlab.engine.start_matlab()
        result = eng.eval('1+1')
        assert result == 2
        print("✅ MATLAB compute cluster operational")
    except Exception as e:
        print(f"❌ MATLAB test failed: {e}")

if __name__ == "__main__":
    test_trading_engine()
    test_matlab_compute()
```

---

## 🎯 POST-DEPLOYMENT CHECKLIST

### **Day 1 Verification**
- [ ] VPC and subnets created successfully
- [ ] Security groups configured properly
- [ ] KMS keys operational
- [ ] CloudHSM cluster active

### **Day 2 Verification**
- [ ] Aurora cluster running and accessible
- [ ] Redis cluster operational
- [ ] S3 buckets created with encryption
- [ ] Backup procedures tested

### **Day 3 Verification**
- [ ] ECS cluster operational
- [ ] Docker images pushed to ECR
- [ ] Load balancer health checks passing
- [ ] Auto-scaling policies active

### **Day 4 Verification**
- [ ] MATLAB instances launching successfully
- [ ] GPU acceleration working
- [ ] Auto Scaling Group scaling properly
- [ ] Cost optimization measures active

### **Day 5 Verification**
- [ ] Trading application deployed and running
- [ ] All integrations functional
- [ ] Monitoring dashboards operational
- [ ] Alert notifications working

---

## 💰 COST MONITORING

### **Daily Cost Tracking**
```bash
# Check daily costs
aws ce get-cost-and-usage \
  --time-period Start=2025-06-01,End=2025-06-15 \
  --granularity DAILY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Set up budget alerts
aws budgets create-budget \
  --account-id 123456789012 \
  --budget file://budgets/monthly-budget.json
```

### **Cost Optimization Recommendations**
- Monitor Spot Instance savings (target: 60% reduction)
- Use Aurora Serverless v2 auto-pause (target: 80% savings during idle)
- Implement S3 Intelligent Tiering (target: 30% storage savings)
- Regular rightsizing analysis for EC2 instances

---

## 🚨 TROUBLESHOOTING GUIDE

### **Common Issues and Solutions**

#### **ECS Tasks Failing to Start**
```bash
# Check task logs
aws logs get-log-events \
  --log-group-name /ecs/arbitrage-trading \
  --log-stream-name ecs/trading-engine/[TASK-ID]

# Common fixes:
# 1. Check IAM permissions
# 2. Verify secrets in Secrets Manager
# 3. Check security group rules
```

#### **MATLAB Instances Not Scaling**
```bash
# Check Auto Scaling Group
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names matlab-compute-asg

# Check instance health
aws ec2 describe-instances \
  --filters Name=tag:aws:autoscaling:groupName,Values=matlab-compute-asg
```

#### **Database Connection Issues**
```bash
# Check Aurora cluster status
aws rds describe-db-clusters \
  --db-cluster-identifier arbitrage-aurora-cluster

# Test connectivity
psql -h [AURORA-ENDPOINT] -U postgres -d arbitrage_trading
```

---

## 📞 SUPPORT ESCALATION

### **Critical Issues (24/7)**
1. **AWS Support** (Business/Enterprise plan required)
2. **On-call Engineer**: +1-XXX-XXX-XXXX
3. **AWS TAM** (Technical Account Manager)

### **Service-Specific Support**
- **ECS/Fargate**: AWS Container Support
- **Aurora**: AWS RDS Support  
- **EC2/GPU**: AWS Compute Support
- **KMS/Security**: AWS Security Support

This deployment guide provides step-by-step instructions for deploying your arbitrage system on AWS with enterprise-grade infrastructure, security, and monitoring.
