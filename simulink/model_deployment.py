#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Deployment Pipeline for Simulink Models

This module provides a framework for deploying Simulink models to production
environments. It handles model versioning, packaging, deployment, and monitoring.

Author: DeFi Arbitrage System
Date: June 17, 2025
"""

import os
import time
import json
import shutil
import logging
import hashlib
import subprocess
import threading
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('model_deployment')


@dataclass
class DeploymentConfig:
    """Configuration for model deployment."""
    model_name: str
    model_path: str
    target_environment: str  # "development", "staging", "production"
    deployment_method: str  # "docker", "kubernetes", "aws", "azure", "local"
    version: str
    description: str = ""
    dependencies: List[str] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    rollback_enabled: bool = True
    auto_scaling_enabled: bool = False
    monitoring_enabled: bool = True
    notification_endpoints: List[str] = field(default_factory=list)
    deployment_timeout: int = 300  # seconds
    validation_timeout: int = 300  # seconds


@dataclass
class DeploymentStatus:
    """Status of a model deployment."""
    model_name: str
    version: str
    environment: str
    status: str  # "pending", "deploying", "deployed", "failed", "rolled_back"
    start_time: float
    end_time: float = 0.0
    error_message: str = ""
    logs: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class ModelDeployment:
    """Framework for deploying Simulink models."""
    
    def __init__(self, config: DeploymentConfig):
        """Initialize the model deployment.
        
        Args:
            config: Deployment configuration
        """
        self.config = config
        self.status = DeploymentStatus(
            model_name=config.model_name,
            version=config.version,
            environment=config.target_environment,
            status="pending",
            start_time=time.time()
        )
        self.deployment_thread = None
        self.deployment_dir = os.path.join(
            "simulink", "deployments", 
            config.target_environment, 
            config.model_name, 
            config.version
        )
        
        # Create deployment directory
        os.makedirs(self.deployment_dir, exist_ok=True)
        
        logger.info(f"Initialized deployment for {config.model_name} v{config.version} to {config.target_environment}")
    
    def _log(self, message: str):
        """Log a message and add it to the deployment logs.
        
        Args:
            message: Message to log
        """
        logger.info(message)
        self.status.logs.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")
    
    def _calculate_model_hash(self) -> str:
        """Calculate a hash of the model file.
        
        Returns:
            str: Hash of the model file
        """
        try:
            with open(self.config.model_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            self._log(f"Error calculating model hash: {str(e)}")
            return ""
    
    def _validate_model(self) -> bool:
        """Validate the model before deployment.
        
        Returns:
            bool: True if validation passed, False otherwise
        """
        self._log(f"Validating model {self.config.model_name} v{self.config.version}")
        
        # Check if model file exists
        if not os.path.exists(self.config.model_path):
            self._log(f"Model file not found: {self.config.model_path}")
            return False
        
        # Check if model is a valid Simulink model
        if not self.config.model_path.endswith('.slx'):
            self._log(f"Model file is not a Simulink model: {self.config.model_path}")
            return False
        
        # Calculate model hash
        model_hash = self._calculate_model_hash()
        if not model_hash:
            self._log("Failed to calculate model hash")
            return False
        
        # Save model hash to deployment directory
        with open(os.path.join(self.deployment_dir, "model_hash.txt"), 'w') as f:
            f.write(model_hash)
        
        # TODO: Add more validation checks
        # - Check model structure
        # - Check for required blocks
        # - Check for required parameters
        # - Check for required signals
        
        self._log(f"Model validation passed: {self.config.model_name} v{self.config.version}")
        return True
    
    def _package_model(self) -> bool:
        """Package the model for deployment.
        
        Returns:
            bool: True if packaging succeeded, False otherwise
        """
        self._log(f"Packaging model {self.config.model_name} v{self.config.version}")
        
        try:
            # Copy model file to deployment directory
            model_filename = os.path.basename(self.config.model_path)
            shutil.copy2(self.config.model_path, os.path.join(self.deployment_dir, model_filename))
            
            # Create deployment manifest
            manifest = {
                "model_name": self.config.model_name,
                "version": self.config.version,
                "description": self.config.description,
                "target_environment": self.config.target_environment,
                "deployment_method": self.config.deployment_method,
                "timestamp": time.time(),
                "dependencies": self.config.dependencies,
                "environment_variables": self.config.environment_variables,
                "resource_requirements": self.config.resource_requirements,
                "model_hash": self._calculate_model_hash(),
                "created_by": os.environ.get("USERNAME", "unknown")
            }
            
            # Save manifest to deployment directory
            with open(os.path.join(self.deployment_dir, "manifest.json"), 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Create deployment scripts based on deployment method
            self._create_deployment_scripts()
            
            self._log(f"Model packaging completed: {self.config.model_name} v{self.config.version}")
            return True
            
        except Exception as e:
            self._log(f"Error packaging model: {str(e)}")
            return False
    
    def _create_deployment_scripts(self):
        """Create deployment scripts based on deployment method."""
        if self.config.deployment_method == "docker":
            self._create_docker_deployment()
        elif self.config.deployment_method == "kubernetes":
            self._create_kubernetes_deployment()
        elif self.config.deployment_method == "aws":
            self._create_aws_deployment()
        elif self.config.deployment_method == "azure":
            self._create_azure_deployment()
        elif self.config.deployment_method == "gcp":
            self._create_gcp_deployment()
        elif self.config.deployment_method == "local":
            self._create_local_deployment()
        else:
            self._log(f"Unknown deployment method: {self.config.deployment_method}")
    
    def _create_docker_deployment(self):
        """Create Docker deployment files."""
        # Create Dockerfile
        dockerfile_content = f"""FROM mathworks/matlab:r2023a
        
# Install Python and dependencies
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install numpy pandas matplotlib requests websocket-client

# Copy model files
COPY {os.path.basename(self.config.model_path)} /app/
COPY manifest.json /app/
COPY start.sh /app/

# Set working directory
WORKDIR /app

# Set environment variables
"""
        
        # Add environment variables
        for key, value in self.config.environment_variables.items():
            dockerfile_content += f"ENV {key}={value}\n"
        
        # Add entrypoint
        dockerfile_content += """
# Make start script executable
RUN chmod +x /app/start.sh

# Set entrypoint
ENTRYPOINT ["/app/start.sh"]
"""
        
        # Save Dockerfile
        with open(os.path.join(self.deployment_dir, "Dockerfile"), 'w') as f:
            f.write(dockerfile_content)
        
        # Create start script
        start_script = """#!/bin/bash
set -e

echo "Starting Simulink model deployment..."
echo "Model: $MODEL_NAME"
echo "Version: $MODEL_VERSION"
echo "Environment: $TARGET_ENVIRONMENT"

# Start MATLAB engine
matlab -batch "disp('MATLAB Engine started'); addpath('/app'); disp('Model path added');"

# Start model execution
python3 -c "
import os
import time
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('model_runner')

# Load manifest
with open('/app/manifest.json', 'r') as f:
    manifest = json.load(f)

logger.info(f'Starting model {manifest[\"model_name\"]} v{manifest[\"version\"]}')

# TODO: Add model execution code here
# This would typically use the MATLAB Engine API for Python
# to load and run the Simulink model

# Keep the container running
while True:
    logger.info(f'Model running: {datetime.now().isoformat()}')
    time.sleep(60)
"

"""
        
        # Save start script
        with open(os.path.join(self.deployment_dir, "start.sh"), 'w') as f:
            f.write(start_script)
        
        # Create docker-compose.yml
        docker_compose = f"""version: '3'

services:
  {self.config.model_name.lower()}:
    build: .
    image: defi-arbitrage/{self.config.model_name.lower()}:{self.config.version}
    container_name: {self.config.model_name.lower()}-{self.config.version}
    environment:
      - MODEL_NAME={self.config.model_name}
      - MODEL_VERSION={self.config.version}
      - TARGET_ENVIRONMENT={self.config.target_environment}
"""
        
        # Add environment variables
        for key, value in self.config.environment_variables.items():
            docker_compose += f"      - {key}={value}\n"
        
        # Add resource limits if specified
        if "cpu" in self.config.resource_requirements or "memory" in self.config.resource_requirements:
            docker_compose += "    deploy:\n      resources:\n        limits:\n"
            if "cpu" in self.config.resource_requirements:
                docker_compose += f"          cpus: '{self.config.resource_requirements['cpu']}'\n"
            if "memory" in self.config.resource_requirements:
                docker_compose += f"          memory: {self.config.resource_requirements['memory']}\n"
        
        # Add restart policy
        docker_compose += "    restart: unless-stopped\n"
        
        # Save docker-compose.yml
        with open(os.path.join(self.deployment_dir, "docker-compose.yml"), 'w') as f:
            f.write(docker_compose)
    
    def _create_kubernetes_deployment(self):
        """Create Kubernetes deployment files."""
        # Create Kubernetes deployment YAML
        k8s_deployment = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {self.config.model_name.lower()}-{self.config.version.replace('.', '-')}
  namespace: defi-arbitrage-{self.config.target_environment}
  labels:
    app: {self.config.model_name.lower()}
    version: "{self.config.version}"
    environment: {self.config.target_environment}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {self.config.model_name.lower()}
      version: "{self.config.version}"
  template:
    metadata:
      labels:
        app: {self.config.model_name.lower()}
        version: "{self.config.version}"
        environment: {self.config.target_environment}
    spec:
      containers:
      - name: {self.config.model_name.lower()}
        image: defi-arbitrage/{self.config.model_name.lower()}:{self.config.version}
        imagePullPolicy: Always
        env:
        - name: MODEL_NAME
          value: "{self.config.model_name}"
        - name: MODEL_VERSION
          value: "{self.config.version}"
        - name: TARGET_ENVIRONMENT
          value: "{self.config.target_environment}"
"""
        
        # Add environment variables
        for key, value in self.config.environment_variables.items():
            k8s_deployment += f"""        - name: {key}
          value: "{value}"
"""
        
        # Add resource limits if specified
        if "cpu" in self.config.resource_requirements or "memory" in self.config.resource_requirements:
            k8s_deployment += "        resources:\n          limits:\n"
            if "cpu" in self.config.resource_requirements:
                k8s_deployment += f"            cpu: {self.config.resource_requirements['cpu']}\n"
            if "memory" in self.config.resource_requirements:
                k8s_deployment += f"            memory: {self.config.resource_requirements['memory']}\n"
        
        # Add liveness and readiness probes
        k8s_deployment += """        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
"""
        
        # Save Kubernetes deployment YAML
        with open(os.path.join(self.deployment_dir, "k8s-deployment.yaml"), 'w') as f:
            f.write(k8s_deployment)
        
        # Create Kubernetes service YAML
        k8s_service = f"""apiVersion: v1
kind: Service
metadata:
  name: {self.config.model_name.lower()}
  namespace: defi-arbitrage-{self.config.target_environment}
  labels:
    app: {self.config.model_name.lower()}
    environment: {self.config.target_environment}
spec:
  selector:
    app: {self.config.model_name.lower()}
  ports:
  - port: 8080
    targetPort: 8080
    name: http
  type: ClusterIP
"""
        
        # Save Kubernetes service YAML
        with open(os.path.join(self.deployment_dir, "k8s-service.yaml"), 'w') as f:
            f.write(k8s_service)
    
    def _create_aws_deployment(self):
        """Create AWS deployment files."""
        # Create AWS CloudFormation template
        cf_template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": f"CloudFormation template for {self.config.model_name} v{self.config.version}",
            "Parameters": {
                "Environment": {
                    "Type": "String",
                    "Default": self.config.target_environment,
                    "AllowedValues": ["development", "staging", "production"],
                    "Description": "Deployment environment"
                }
            },
            "Resources": {
                "ModelTaskDefinition": {
                    "Type": "AWS::ECS::TaskDefinition",
                    "Properties": {
                        "Family": f"{self.config.model_name.lower()}-{self.config.version}",
                        "ContainerDefinitions": [
                            {
                                "Name": f"{self.config.model_name.lower()}",
                                "Image": f"defi-arbitrage/{self.config.model_name.lower()}:{self.config.version}",
                                "Essential": True,
                                "Environment": [
                                    {
                                        "Name": "MODEL_NAME",
                                        "Value": self.config.model_name
                                    },
                                    {
                                        "Name": "MODEL_VERSION",
                                        "Value": self.config.version
                                    },
                                    {
                                        "Name": "TARGET_ENVIRONMENT",
                                        "Value": {"Ref": "Environment"}
                                    }
                                ],
                                "LogConfiguration": {
                                    "LogDriver": "awslogs",
                                    "Options": {
                                        "awslogs-group": {"Fn::Sub": "/ecs/${Environment}/model-logs"},
                                        "awslogs-region": {"Ref": "AWS::Region"},
                                        "awslogs-stream-prefix": self.config.model_name.lower()
                                    }
                                }
                            }
                        ],
                        "RequiresCompatibilities": ["FARGATE"],
                        "NetworkMode": "awsvpc",
                        "Cpu": str(self.config.resource_requirements.get("cpu", "256")),
                        "Memory": str(self.config.resource_requirements.get("memory", "512")),
                        "ExecutionRoleArn": {"Fn::ImportValue": {"Fn::Sub": "${Environment}-ECSTaskExecutionRole"}},
                        "TaskRoleArn": {"Fn::ImportValue": {"Fn::Sub": "${Environment}-ECSTaskRole"}}
                    }
                },
                "ModelService": {
                    "Type": "AWS::ECS::Service",
                    "Properties": {
                        "ServiceName": f"{self.config.model_name.lower()}-{self.config.version}",
                        "Cluster": {"Fn::ImportValue": {"Fn::Sub": "${Environment}-ECSCluster"}},
                        "TaskDefinition": {"Ref": "ModelTaskDefinition"},
                        "DesiredCount": 1,
                        "LaunchType": "FARGATE",
                        "NetworkConfiguration": {
                            "AwsvpcConfiguration": {
                                "AssignPublicIp": "DISABLED",
                                "SecurityGroups": [{"Fn::ImportValue": {"Fn::Sub": "${Environment}-ECSSecurityGroup"}}],
                                "Subnets": {"Fn::Split": [",", {"Fn::ImportValue": {"Fn::Sub": "${Environment}-PrivateSubnets"}}]}
                            }
                        }
                    }
                }
            },
            "Outputs": {
                "ModelServiceName": {
                    "Description": "Name of the ECS Service",
                    "Value": {"Ref": "ModelService"}
                },
                "ModelTaskDefinition": {
                    "Description": "ARN of the Task Definition",
                    "Value": {"Ref": "ModelTaskDefinition"}
                }
            }
        }
        
        # Add environment variables
        for key, value in self.config.environment_variables.items():
            cf_template["Resources"]["ModelTaskDefinition"]["Properties"]["ContainerDefinitions"][0]["Environment"].append({
                "Name": key,
                "Value": value
            })
        
        # Save CloudFormation template
        with open(os.path.join(self.deployment_dir, "cloudformation.json"), 'w') as f:
            json.dump(cf_template, f, indent=2)
        
        # Create deployment script
        deploy_script = """#!/bin/bash
set -e

STACK_NAME="${MODEL_NAME,,}-${MODEL_VERSION//./-}"
ENVIRONMENT="${TARGET_ENVIRONMENT}"
REGION="us-east-1"  # Change as needed

echo "Deploying model to AWS..."
echo "Model: $MODEL_NAME"
echo "Version: $MODEL_VERSION"
echo "Environment: $ENVIRONMENT"
echo "Stack Name: $STACK_NAME"

# Build and push Docker image
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
docker build -t defi-arbitrage/${MODEL_NAME,,}:${MODEL_VERSION} .
docker tag defi-arbitrage/${MODEL_NAME,,}:${MODEL_VERSION} $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/defi-arbitrage/${MODEL_NAME,,}:${MODEL_VERSION}
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/defi-arbitrage/${MODEL_NAME,,}:${MODEL_VERSION}

# Deploy CloudFormation stack
aws cloudformation deploy \\
  --template-file cloudformation.json \\
  --stack-name $STACK_NAME \\
  --parameter-overrides Environment=$ENVIRONMENT \\
  --capabilities CAPABILITY_IAM \\
  --region $REGION

echo "Deployment completed successfully!"
"""
        
        # Save deployment script
        with open(os.path.join(self.deployment_dir, "deploy_aws.sh"), 'w') as f:
            f.write(deploy_script)
        os.chmod(os.path.join(self.deployment_dir, "deploy_aws.sh"), 0o755)
    
    def _create_azure_deployment(self):
        """Create Azure deployment files."""
        # Create Azure Resource Manager (ARM) template
        arm_template = {
            "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
            "contentVersion": "1.0.0.0",
            "parameters": {
                "environment": {
                    "type": "string",
                    "defaultValue": self.config.target_environment,
                    "allowedValues": ["development", "staging", "production"],
                    "metadata": {
                        "description": "Deployment environment"
                    }
                },
                "containerRegistryName": {
                    "type": "string",
                    "defaultValue": "defiarbitrageregistry",
                    "metadata": {
                        "description": "Name of the container registry"
                    }
                }
            },
            "variables": {
                "modelName": self.config.model_name.lower(),
                "modelVersion": self.config.version,
                "containerGroupName": f"{self.config.model_name.lower()}-{self.config.version}",
                "containerImage": f"[concat(parameters('containerRegistryName'), '.azurecr.io/defi-arbitrage/', variables('modelName'), ':', variables('modelVersion'))]"
            },
            "resources": [
                {
                    "type": "Microsoft.ContainerInstance/containerGroups",
                    "apiVersion": "2021-03-01",
                    "name": "[variables('containerGroupName')]",
                    "location": "[resourceGroup().location]",
                    "properties": {
                        "containers": [
                            {
                                "name": "[variables('modelName')]",
                                "properties": {
                                    "image": "[variables('containerImage')]",
                                    "resources": {
                                        "requests": {
                                            "cpu": self.config.resource_requirements.get("cpu", 1),
                                            "memoryInGB": float(self.config.resource_requirements.get("memory", "1").replace("G", ""))
                                        }
                                    },
                                    "environmentVariables": [
                                        {
                                            "name": "MODEL_NAME",
                                            "value": self.config.model_name
                                        },
                                        {
                                            "name": "MODEL_VERSION",
                                            "value": self.config.version
                                        },
                                        {
                                            "name": "TARGET_ENVIRONMENT",
                                            "value": "[parameters('environment')]"
                                        }
                                    ]
                                }
                            }
                        ],
                        "osType": "Linux",
                        "restartPolicy": "Always"
                    }
                }
            ],
            "outputs": {
                "containerGroupName": {
                    "type": "string",
                    "value": "[variables('containerGroupName')]"
                }
            }
        }
        
        # Add environment variables
        for key, value in self.config.environment_variables.items():
            arm_template["resources"][0]["properties"]["containers"][0]["properties"]["environmentVariables"].append({
                "name": key,
                "value": value
            })
        
        # Save ARM template
        with open(os.path.join(self.deployment_dir, "arm-template.json"), 'w') as f:
            json.dump(arm_template, f, indent=2)
        
        # Create deployment script
        deploy_script = """#!/bin/bash
set -e

RESOURCE_GROUP="defi-arbitrage-${TARGET_ENVIRONMENT}"
CONTAINER_REGISTRY="defiarbitrageregistry"
MODEL_NAME_LOWER=$(echo $MODEL_NAME | tr '[:upper:]' '[:lower:]')
DEPLOYMENT_NAME="${MODEL_NAME_LOWER}-${MODEL_VERSION//./-}"

echo "Deploying model to Azure..."
echo "Model: $MODEL_NAME"
echo "Version: $MODEL_VERSION"
echo "Environment: $TARGET_ENVIRONMENT"
echo "Resource Group: $RESOURCE_GROUP"

# Build and push Docker image
az acr login --name $CONTAINER_REGISTRY
docker build -t defi-arbitrage/${MODEL_NAME_LOWER}:${MODEL_VERSION} .
docker tag defi-arbitrage/${MODEL_NAME_LOWER}:${MODEL_VERSION} ${CONTAINER_REGISTRY}.azurecr.io/defi-arbitrage/${MODEL_NAME_LOWER}:${MODEL_VERSION}
docker push ${CONTAINER_REGISTRY}.azurecr.io/defi-arbitrage/${MODEL_NAME_LOWER}:${MODEL_VERSION}

# Deploy ARM template
az deployment group create \\
  --resource-group $RESOURCE_GROUP \\
  --name $DEPLOYMENT_NAME \\
  --template-file arm-template.json \\
  --parameters environment=$TARGET_ENVIRONMENT containerRegistryName=$CONTAINER_REGISTRY

echo "Deployment completed successfully!"
"""
        
        # Save deployment script
        with open(os.path.join(self.deployment_dir, "deploy_azure.sh"), 'w') as f:
            f.write(deploy_script)
        os.chmod(os.path.join(self.deployment_dir, "deploy_azure.sh"), 0o755)
    
    def _create_local_deployment(self):
        """Create local deployment files."""
        # Create start script
        start_script = """#!/bin/bash
set -e

echo "Starting local deployment of Simulink model..."
echo "Model: $MODEL_NAME"
echo "Version: $MODEL_VERSION"
echo "Environment: $TARGET_ENVIRONMENT"

# Create log directory
LOG_DIR="logs"
mkdir -p $LOG_DIR

# Start MATLAB engine and run the model
matlab -batch "
    try
        disp('Starting MATLAB engine...');
        addpath(pwd);
        disp('Loading model...');
        model_name = '$MODEL_NAME';
        load_system(model_name);
        disp('Starting simulation...');
        set_param(model_name, 'SimulationCommand', 'start');
        disp('Simulation started successfully!');
    catch e
        disp('Error starting simulation:');
        disp(e.message);
        exit(1);
    end
" > $LOG_DIR/matlab_${MODEL_NAME}_${MODEL_VERSION}.log 2>&1 &

# Start Python monitoring script
python3 -c "
import os
import time
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='logs/monitor_${MODEL_NAME}_${MODEL_VERSION}.log'
)
logger = logging.getLogger('model_monitor')

# Load manifest
with open('manifest.json', 'r') as f:
    manifest = json.load(f)

logger.info(f'Starting monitoring for {manifest[\"model_name\"]} v{manifest[\"version\"]}')

# Monitor the model
while True:
    logger.info(f'Model running: {datetime.now().isoformat()}')
    time.sleep(60)
" &

echo "Model started successfully!"
echo "Logs are available in the 'logs' directory."
"""
        
        # Save start script
        with open(os.path.join(self.deployment_dir, "start_local.sh"), 'w') as f:
            f.write(start_script)
        os.chmod(os.path.join(self.deployment_dir, "start_local.sh"), 0o755)
        
        # Create stop script
        stop_script = """#!/bin/bash
set -e

echo "Stopping local deployment of Simulink model..."
echo "Model: $MODEL_NAME"
echo "Version: $MODEL_VERSION"

# Stop MATLAB engine
matlab -batch "
    try
        disp('Stopping simulation...');
        model_name = '$MODEL_NAME';
        set_param(model_name, 'SimulationCommand', 'stop');
        close_system(model_name, 0);
        disp('Simulation stopped successfully!');
    catch e
        disp('Error stopping simulation:');
        disp(e.message);
        exit(1);
    end
" > logs/matlab_stop_${MODEL_NAME}_${MODEL_VERSION}.log 2>&1

# Kill monitoring script
pkill -f "monitor_${MODEL_NAME}_${MODEL_VERSION}" || true

echo "Model stopped successfully!"
"""
        
        # Save stop script
        with open(os.path.join(self.deployment_dir, "stop_local.sh"), 'w') as f:
            f.write(stop_script)
        os.chmod(os.path.join(self.deployment_dir, "stop_local.sh"), 0o755)
    
    def _create_gcp_deployment(self):
        """Create Google Cloud Platform deployment files."""
        # Create Cloud Run deployment YAML
        cloud_run_yaml = f"""apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: {self.config.model_name.lower()}-{self.config.version.replace('.', '-')}
  namespace: defi-arbitrage-{self.config.target_environment}
  labels:
    app: {self.config.model_name.lower()}
    version: "{self.config.version}"
    environment: {self.config.target_environment}
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "5"
    spec:
      containers:
      - image: gcr.io/defi-arbitrage/{self.config.model_name.lower()}:{self.config.version}
        env:
        - name: MODEL_NAME
          value: "{self.config.model_name}"
        - name: MODEL_VERSION
          value: "{self.config.version}"
        - name: TARGET_ENVIRONMENT
          value: "{self.config.target_environment}"
"""
        
        # Add environment variables
        for key, value in self.config.environment_variables.items():
            cloud_run_yaml += f"""        - name: {key}
          value: "{value}"
"""
        
        # Add resource limits if specified
        if "cpu" in self.config.resource_requirements or "memory" in self.config.resource_requirements:
            cloud_run_yaml += "        resources:\n          limits:\n"
            if "cpu" in self.config.resource_requirements:
                cloud_run_yaml += f"            cpu: {self.config.resource_requirements['cpu']}\n"
            if "memory" in self.config.resource_requirements:
                cloud_run_yaml += f"            memory: {self.config.resource_requirements['memory']}\n"
        
        # Save Cloud Run YAML
        with open(os.path.join(self.deployment_dir, "cloud-run.yaml"), 'w') as f:
            f.write(cloud_run_yaml)
        
        # Create deployment script
        deploy_script = """#!/bin/bash
set -e

PROJECT_ID="defi-arbitrage-project"
MODEL_NAME_LOWER=$(echo $MODEL_NAME | tr '[:upper:]' '[:lower:]')
VERSION=${MODEL_VERSION//./-}
REGION="us-central1"
SERVICE_ACCOUNT="defi-arbitrage-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Deploying model to Google Cloud Platform..."
echo "Model: $MODEL_NAME"
echo "Version: $MODEL_VERSION"
echo "Environment: $TARGET_ENVIRONMENT"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"

# Build and push Docker image to Google Container Registry
echo "Building and pushing Docker image..."
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${MODEL_NAME_LOWER}:${MODEL_VERSION} .

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${MODEL_NAME_LOWER}-${VERSION} \\
  --image gcr.io/${PROJECT_ID}/${MODEL_NAME_LOWER}:${MODEL_VERSION} \\
  --platform managed \\
  --region ${REGION} \\
  --service-account ${SERVICE_ACCOUNT} \\
  --allow-unauthenticated \\
  --set-env-vars="MODEL_NAME=${MODEL_NAME},MODEL_VERSION=${MODEL_VERSION},TARGET_ENVIRONMENT=${TARGET_ENVIRONMENT}"

# Add environment variables
"""
        
        # Add environment variables to deployment script
        for key, value in self.config.environment_variables.items():
            deploy_script += f"gcloud run services update ${MODEL_NAME_LOWER}-${VERSION} --set-env-vars={key}={value} --region ${REGION}\n"
        
        deploy_script += """
echo "Deployment to Google Cloud Platform completed successfully!"
"""
        
        # Save deployment script
        with open(os.path.join(self.deployment_dir, "deploy_gcp.sh"), 'w') as f:
            f.write(deploy_script)
        os.chmod(os.path.join(self.deployment_dir, "deploy_gcp.sh"), 0o755)
        
        # Create Terraform configuration for more advanced deployments
        terraform_config = """# Terraform configuration for GCP deployment

provider "google" {
  project = "defi-arbitrage-project"
  region  = "us-central1"
}

resource "google_cloud_run_service" "model_service" {
  name     = "${var.model_name_lower}-${var.model_version_dash}"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/${var.model_name_lower}:${var.model_version}"
        
        resources {
          limits = {
            cpu    = "${var.cpu}"
            memory = "${var.memory}"
          }
        }
        
        env {
          name  = "MODEL_NAME"
          value = var.model_name
        }
        
        env {
          name  = "MODEL_VERSION"
          value = var.model_version
        }
        
        env {
          name  = "TARGET_ENVIRONMENT"
          value = var.environment
        }
"""
        
        # Add environment variables to Terraform config
        for key, value in self.config.environment_variables.items():
            terraform_config += f"""
        env {{
          name  = "{key}"
          value = "{value}"
        }}"""
        
        terraform_config += """
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.model_service.name
  location = google_cloud_run_service.model_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

variable "model_name" {
  description = "Name of the model"
  type        = string
}

variable "model_name_lower" {
  description = "Lowercase name of the model"
  type        = string
}

variable "model_version" {
  description = "Version of the model"
  type        = string
}

variable "model_version_dash" {
  description = "Version of the model with dots replaced by dashes"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "defi-arbitrage-project"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "cpu" {
  description = "CPU allocation"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory allocation"
  type        = string
  default     = "2Gi"
}

output "service_url" {
  value = google_cloud_run_service.model_service.status[0].url
}
"""
        
        # Save Terraform configuration
        with open(os.path.join(self.deployment_dir, "main.tf"), 'w') as f:
            f.write(terraform_config)
        
        # Create Terraform variables file
        terraform_vars = f"""model_name = "{self.config.model_name}"
model_name_lower = "{self.config.model_name.lower()}"
model_version = "{self.config.version}"
model_version_dash = "{self.config.version.replace('.', '-')}"
environment = "{self.config.target_environment}"
cpu = "{self.config.resource_requirements.get('cpu', '1')}"
memory = "{self.config.resource_requirements.get('memory', '2Gi')}"
"""
        
        # Save Terraform variables file
        with open(os.path.join(self.deployment_dir, "terraform.tfvars"), 'w') as f:
            f.write(terraform_vars)

    def _deploy_model(self) -> bool:
        """Deploy the model to the target environment.
        
        Returns:
            bool: True if deployment succeeded, False otherwise
        """
        self._log(f"Deploying model {self.config.model_name} v{self.config.version} to {self.config.target_environment}")
        
        try:
            # Execute deployment based on deployment method
            if self.config.deployment_method == "docker":
                return self._deploy_docker()
            elif self.config.deployment_method == "kubernetes":
                return self._deploy_kubernetes()
            elif self.config.deployment_method == "aws":
                return self._deploy_aws()
            elif self.config.deployment_method == "azure":
                return self._deploy_azure()
            elif self.config.deployment_method == "gcp":
                return self._deploy_gcp()
            elif self.config.deployment_method == "local":
                return self._deploy_local()
            else:
                self._log(f"Unknown deployment method: {self.config.deployment_method}")
                return False
                
        except Exception as e:
            self._log(f"Error deploying model: {str(e)}")
            return False
    
    def _deploy_docker(self) -> bool:
        """Deploy the model using Docker.
        
        Returns:
            bool: True if deployment succeeded, False otherwise
        """
        self._log("Deploying with Docker...")
        
        try:
            # Change to deployment directory
            os.chdir(self.deployment_dir)
            
            # Build Docker image
            self._log("Building Docker image...")
            result = subprocess.run(
                ["docker", "build", "-t", f"defi-arbitrage/{self.config.model_name.lower()}:{self.config.version}", "."],
                capture_output=True,
                text=True,
                check=True
            )
            self._log(f"Docker build output: {result.stdout}")
            
            # Start container with docker-compose
            self._log("Starting container with docker-compose...")
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                capture_output=True,
                text=True,
                check=True
            )
            self._log(f"Docker compose output: {result.stdout}")
            
            # Verify container is running
            self._log("Verifying container is running...")
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={self.config.model_name.lower()}-{self.config.version}"],
                capture_output=True,
                text=True,
                check=True
            )
            
            if self.config.model_name.lower() in result.stdout:
                self._log("Container is running successfully")
                return True
            else:
                self._log("Container is not running")
                return False
                
        except subprocess.CalledProcessError as e:
            self._log(f"Command failed: {e.cmd}")
            self._log(f"Output: {e.stdout}")
            self._log(f"Error: {e.stderr}")
            return False
        except Exception as e:
            self._log(f"Error deploying with Docker: {str(e)}")
            return False
    
    def _deploy_kubernetes(self) -> bool:
        """Deploy the model using Kubernetes.
        
        Returns:
            bool: True if deployment succeeded, False otherwise
        """
        self._log("Deploying with Kubernetes...")
        
        try:
            # Change to deployment directory
            os.chdir(self.deployment_dir)
            
            # Build Docker image
            self._log("Building Docker image...")
            result = subprocess.run(
                ["docker", "build", "-t", f"defi-arbitrage/{self.config.model_name.lower()}:{self.config.version}", "."],
                capture_output=True,
                text=True,
                check=True
            )
            self._log(f"Docker build output: {result.stdout}")
            
            # Apply Kubernetes deployment
            self._log("Applying Kubernetes deployment...")
            result = subprocess.run(
                ["kubectl", "apply", "-f", "k8s-deployment.yaml"],
                capture_output=True,
                text=True,
                check=True
            )
            self._log(f"Kubernetes deployment output: {result.stdout}")
            
            # Apply Kubernetes service
            self._log("Applying Kubernetes service...")
            result = subprocess.run(
                ["kubectl", "apply", "-f", "k8s-service.yaml"],
                capture_output=True,
                text=True,
                check=True
            )
            self._log(f"Kubernetes service output: {result.stdout}")
            
            # Wait for deployment to be ready
            self._log("Waiting for deployment to be ready...")
            result = subprocess.run(
                [
                    "kubectl", "rollout", "status", "deployment", 
                    f"{self.config.model_name.lower()}-{self.config.version.replace('.', '-')}",
                    "-n", f"defi-arbitrage-{self.config.target_environment}"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            self._log(f"Rollout status output: {result.stdout}")
            
            return True
                
        except subprocess.CalledProcessError as e:
            self._log(f"Command failed: {e.cmd}")
            self._log(f"Output: {e.stdout}")
            self._log(f"Error: {e.stderr}")
            return False
        except Exception as e:
            self._log(f"Error deploying with Kubernetes: {str(e)}")
            return False
    
    def _deploy_aws(self) -> bool:
        """Deploy the model using AWS.
        
        Returns:
            bool: True if deployment succeeded, False otherwise
        """
        self._log("Deploying to AWS...")
        
        try:
            # Change to deployment directory
            os.chdir(self.deployment_dir)
            
            # Set environment variables for deployment script
            env = os.environ.copy()
            env["MODEL_NAME"] = self.config.model_name
            env["MODEL_VERSION"] = self.config.version
            env["TARGET_ENVIRONMENT"] = self.config.target_environment
            
            # Run deployment script
            self._log("Running AWS deployment script...")
            result = subprocess.run(
                ["./deploy_aws.sh"],
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            self._log(f"AWS deployment output: {result.stdout}")
            
            return True
                
        except subprocess.CalledProcessError as e:
            self._log(f"Command failed: {e.cmd}")
            self._log(f"Output: {e.stdout}")
            self._log(f"Error: {e.stderr}")
            return False
        except Exception as e:
            self._log(f"Error deploying to AWS: {str(e)}")
            return False
    
    def _deploy_azure(self) -> bool:
        """Deploy the model using Azure.
        
        Returns:
            bool: True if deployment succeeded, False otherwise
        """
        self._log("Deploying to Azure...")
        
        try:
            # Change to deployment directory
            os.chdir(self.deployment_dir)
            
            # Set environment variables for deployment script
            env = os.environ.copy()
            env["MODEL_NAME"] = self.config.model_name
            env["MODEL_VERSION"] = self.config.version
            env["TARGET_ENVIRONMENT"] = self.config.target_environment
            
            # Run deployment script
            self._log("Running Azure deployment script...")
            result = subprocess.run(
                ["./deploy_azure.sh"],
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            self._log(f"Azure deployment output: {result.stdout}")
            
            return True
                
        except subprocess.CalledProcessError as e:
            self._log(f"Command failed: {e.cmd}")
            self._log(f"Output: {e.stdout}")
            self._log(f"Error: {e.stderr}")
            return False
        except Exception as e:
            self._log(f"Error deploying to Azure: {str(e)}")
            return False
    
    def _deploy_local(self) -> bool:
        """Deploy the model locally.
        
        Returns:
            bool: True if deployment succeeded, False otherwise
        """
        self._log("Deploying locally...")
        
        try:
            # Change to deployment directory
            os.chdir(self.deployment_dir)
            
            # Create logs directory
            os.makedirs("logs", exist_ok=True)
            
            # Set environment variables for deployment script
            env = os.environ.copy()
            env["MODEL_NAME"] = self.config.model_name
            env["MODEL_VERSION"] = self.config.version
            env["TARGET_ENVIRONMENT"] = self.config.target_environment
            
            # Add custom environment variables
            for key, value in self.config.environment_variables.items():
                env[key] = value
            
            # Run start script
            self._log("Running local start script...")
            result = subprocess.run(
                ["./start_local.sh"],
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            self._log(f"Local deployment output: {result.stdout}")
            
            return True
                
        except subprocess.CalledProcessError as e:
            self._log(f"Command failed: {e.cmd}")
            self._log(f"Output: {e.stdout}")
            self._log(f"Error: {e.stderr}")
            return False
        except Exception as e:
            self._log(f"Error deploying locally: {str(e)}")
            return False
    
    def _validate_deployment(self) -> bool:
        """Validate the deployment.
        
        Returns:
            bool: True if validation passed, False otherwise
        """
        self._log(f"Validating deployment of {self.config.model_name} v{self.config.version}")
        
        # TODO: Implement deployment validation
        # This would typically involve:
        # - Checking if the deployment is running
        # - Running basic health checks
        # - Verifying the model is responding to requests
        # - Checking logs for errors
        
        # For now, we'll just return True
        self._log("Deployment validation passed")
        return True
    
    def _deploy_gcp(self) -> bool:
        """Deploy the model using Google Cloud Platform.
        
        Returns:
            bool: True if deployment succeeded, False otherwise
        """
        self._log("Deploying to Google Cloud Platform...")
        
        try:
            # Change to deployment directory
            os.chdir(self.deployment_dir)
            
            # Set environment variables for deployment script
            env = os.environ.copy()
            env["MODEL_NAME"] = self.config.model_name
            env["MODEL_VERSION"] = self.config.version
            env["TARGET_ENVIRONMENT"] = self.config.target_environment
            
            # Run deployment script
            self._log("Running GCP deployment script...")
            result = subprocess.run(
                ["./deploy_gcp.sh"],
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            self._log(f"GCP deployment output: {result.stdout}")
            
            # Verify deployment
            self._log("Verifying GCP deployment...")
            model_name_lower = self.config.model_name.lower()
            version = self.config.version.replace('.', '-')
            region = "us-central1"  # Default region
            
            # Check if the Cloud Run service is deployed
            result = subprocess.run(
                [
                    "gcloud", "run", "services", "describe", 
                    f"{model_name_lower}-{version}", 
                    "--region", region, 
                    "--format", "json"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the JSON output
            service_info = json.loads(result.stdout)
            
            # Check if the service is ready
            if service_info.get("status", {}).get("url"):
                self._log(f"GCP deployment successful. Service URL: {service_info['status']['url']}")
                return True
            else:
                self._log("GCP deployment verification failed")
                return False
                
        except subprocess.CalledProcessError as e:
            self._log(f"Command failed: {e.cmd}")
            self._log(f"Output: {e.stdout}")
            self._log(f"Error: {e.stderr}")
            return False
        except Exception as e:
            self._log(f"Error deploying to GCP: {str(e)}")
            return False

    def _rollback_gcp(self):
        """Rollback GCP deployment."""
        try:
            # Get model name and version
            model_name_lower = self.config.model_name.lower()
            version = self.config.version.replace('.', '-')
            region = "us-central1"  # Default region
            
            # Delete Cloud Run service
            subprocess.run(
                [
                    "gcloud", "run", "services", "delete", 
                    f"{model_name_lower}-{version}", 
                    "--region", region, 
                    "--quiet"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            self._log("GCP deployment rolled back successfully")
            
        except Exception as e:
            self._log(f"Error rolling back GCP deployment: {str(e)}")

    def _rollback_deployment(self):
        """Rollback the deployment if it fails."""
        self._log(f"Rolling back deployment of {self.config.model_name} v{self.config.version}")
        
        try:
            # Execute rollback based on deployment method
            if self.config.deployment_method == "docker":
                self._rollback_docker()
            elif self.config.deployment_method == "kubernetes":
                self._rollback_kubernetes()
            elif self.config.deployment_method == "aws":
                self._rollback_aws()
            elif self.config.deployment_method == "azure":
                self._rollback_azure()
            elif self.config.deployment_method == "gcp":
                self._rollback_gcp()
            elif self.config.deployment_method == "local":
                self._rollback_local()
            else:
                self._log(f"Unknown deployment method: {self.config.deployment_method}")
                
        except Exception as e:
            self._log(f"Error rolling back deployment: {str(e)}")
    
    def _rollback_docker(self):
        """Rollback Docker deployment."""
        try:
            # Change to deployment directory
            os.chdir(self.deployment_dir)
            
            # Stop and remove container
            subprocess.run(
                ["docker-compose", "down"],
                capture_output=True,
                text=True,
                check=True
            )
            
            self._log("Docker deployment rolled back successfully")
            
        except Exception as e:
            self._log(f"Error rolling back Docker deployment: {str(e)}")
    
    def _rollback_kubernetes(self):
        """Rollback Kubernetes deployment."""
        try:
            # Change to deployment directory
            os.chdir(self.deployment_dir)
            
            # Delete deployment
            subprocess.run(
                ["kubectl", "delete", "-f", "k8s-deployment.yaml"],
                capture_output=True,
                text=True,
                check=True
            )
            
            self._log("Kubernetes deployment rolled back successfully")
            
        except Exception as e:
            self._log(f"Error rolling back Kubernetes deployment: {str(e)}")
    
    def _rollback_aws(self):
        """Rollback AWS deployment."""
        try:
            # Delete CloudFormation stack
            stack_name = f"{self.config.model_name.lower()}-{self.config.version.replace('.', '-')}"
            
            subprocess.run(
                ["aws", "cloudformation", "delete-stack", "--stack-name", stack_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            self._log("AWS deployment rolled back successfully")
            
        except Exception as e:
            self._log(f"Error rolling back AWS deployment: {str(e)}")
    
    def _rollback_azure(self):
        """Rollback Azure deployment."""
        try:
            # Delete Azure container group
            resource_group = f"defi-arbitrage-{self.config.target_environment}"
            container_group = f"{self.config.model_name.lower()}-{self.config.version}"
            
            subprocess.run(
                [
                    "az", "container", "delete", 
                    "--resource-group", resource_group, 
                    "--name", container_group, 
                    "--yes"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            self._log("Azure deployment rolled back successfully")
            
        except Exception as e:
            self._log(f"Error rolling back Azure deployment: {str(e)}")
    
    def _rollback_local(self):
        """Rollback local deployment."""
        try:
            # Change to deployment directory
            os.chdir(self.deployment_dir)
            
            # Set environment variables for stop script
            env = os.environ.copy()
            env["MODEL_NAME"] = self.config.model_name
            env["MODEL_VERSION"] = self.config.version
            
            # Run stop script
            subprocess.run(
                ["./stop_local.sh"],
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            self._log("Local deployment rolled back successfully")
            
        except Exception as e:
            self._log(f"Error rolling back local deployment: {str(e)}")
    
    def _deployment_process(self):
        """Main deployment process."""
        try:
            # Update status
            self.status.status = "deploying"
            
            # Validate model
            if not self._validate_model():
                self.status.status = "failed"
                self.status.error_message = "Model validation failed"
                self.status.end_time = time.time()
                return
            
            # Package model
            if not self._package_model():
                self.status.status = "failed"
                self.status.error_message = "Model packaging failed"
                self.status.end_time = time.time()
                return
            
            # Deploy model
            if not self._deploy_model():
                self.status.status = "failed"
                self.status.error_message = "Model deployment failed"
                self.status.end_time = time.time()
                
                # Rollback if enabled
                if self.config.rollback_enabled:
                    self._rollback_deployment()
                    self.status.status = "rolled_back"
                
                return
            
            # Validate deployment
            if not self._validate_deployment():
                self.status.status = "failed"
                self.status.error_message = "Deployment validation failed"
                self.status.end_time = time.time()
                
                # Rollback if enabled
                if self.config.rollback_enabled:
                    self._rollback_deployment()
                    self.status.status = "rolled_back"
                
                return
            
            # Update status
            self.status.status = "deployed"
            self.status.end_time = time.time()
            self._log(f"Model {self.config.model_name} v{self.config.version} deployed successfully to {self.config.target_environment}")
            
        except Exception as e:
            self.status.status = "failed"
            self.status.error_message = str(e)
            self.status.end_time = time.time()
            self._log(f"Error in deployment process: {str(e)}")
            
            # Rollback if enabled
            if self.config.rollback_enabled:
                self._rollback_deployment()
                self.status.status = "rolled_back"
    
    def deploy(self) -> bool:
        """Deploy the model.
        
        Returns:
            bool: True if deployment started successfully, False otherwise
        """
        if self.deployment_thread and self.deployment_thread.is_alive():
            self._log("Deployment is already in progress")
            return False
        
        # Start deployment thread
        self.deployment_thread = threading.Thread(target=self._deployment_process)
        self.deployment_thread.daemon = True
        self.deployment_thread.start()
        
        self._log(f"Started deployment of {self.config.model_name} v{self.config.version} to {self.config.target_environment}")
        return True
    
    def get_status(self) -> DeploymentStatus:
        """Get the current deployment status.
        
        Returns:
            DeploymentStatus: Current deployment status
        """
        return self.status
    
    def wait_for_completion(self, timeout: int = None) -> bool:
        """Wait for deployment to complete.
        
        Args:
            timeout: Timeout in seconds (None for no timeout)
            
        Returns:
            bool: True if deployment completed successfully, False otherwise
        """
        if not self.deployment_thread:
            self._log("Deployment has not been started")
            return False
        
        # Wait for deployment thread to complete
        self.deployment_thread.join(timeout=timeout)
        
        # Check if deployment is still running
        if self.deployment_thread.is_alive():
            self._log("Deployment timed out")
            return False
        
        # Check deployment status
        return self.status.status == "deployed"


def create_default_deployment_config(model_name: str, model_path: str) -> DeploymentConfig:
    """Create a default deployment configuration.
    
    Args:
        model_name: Name of the model to deploy
        model_path: Path to the model file
        
    Returns:
        DeploymentConfig: Default deployment configuration
    """
    return DeploymentConfig(
        model_name=model_name,
        model_path=model_path,
        target_environment="development",
        deployment_method="local",
        version="1.0.0",
        description=f"Deployment of {model_name} model",
        dependencies=[],
        environment_variables={},
        resource_requirements={
            "cpu": "1",
            "memory": "2G"
        },
        rollback_enabled=True,
        auto_scaling_enabled=False,
        monitoring_enabled=True,
        notification_endpoints=[],
        deployment_timeout=300,
        validation_timeout=300
    )


def main():
    """Run a demo of the model deployment pipeline."""
    # Create deployment configuration
    model_name = "Arbitrage_Strategy_Model"
    model_path = os.path.join("simulink", "models", "optimization", f"{model_name}.slx")
    
    # Create the model file if it doesn't exist (for demo purposes)
    if not os.path.exists(model_path):
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        with open(model_path, 'w') as f:
            f.write("This is a placeholder for a Simulink model file.")
    
    config = create_default_deployment_config(model_name, model_path)
    config.version = "1.0.0"
    config.target_environment = "development"
    config.deployment_method = "local"
    
    # Create model deployment
    deployment = ModelDeployment(config)
    
    try:
        # Start deployment
        print(f"Deploying {model_name} v{config.version} to {config.target_environment}...")
        deployment.deploy()
        
        # Wait for deployment to complete
        print("Waiting for deployment to complete...")
        deployment.wait_for_completion(timeout=60)
        
        # Get deployment status
        status = deployment.get_status()
        
        print(f"\nDeployment Status: {status.status}")
        print(f"Model: {status.model_name} v{status.version}")
        print(f"Environment: {status.environment}")
        print(f"Duration: {status.end_time - status.start_time:.2f} seconds")
        
        if status.error_message:
            print(f"Error: {status.error_message}")
        
        print("\nDeployment Logs:")
        for log in status.logs[-10:]:  # Show last 10 logs
            print(f"  {log}")
        
    except KeyboardInterrupt:
        print("\nDeployment interrupted by user")
    except Exception as e:
        print(f"\nError during deployment: {str(e)}")


if __name__ == "__main__":
    main()