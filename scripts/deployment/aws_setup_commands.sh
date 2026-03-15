#!/bin/bash
# AWS Setup Commands for MATLAB Cloud Worker
# Generated: June 15, 2025

echo "🚀 Setting up AWS infrastructure for MATLAB Cloud Worker..."

# 1. Create security group for MATLAB
echo "📡 Creating security group..."
aws ec2 create-security-group \
    --group-name matlab-worker-sg \
    --description "MATLAB Cloud Worker Security Group"

# 2. Add SSH access (REPLACE YOUR-IP with your actual IP address)
echo "🔐 Configuring SSH access..."
echo "⚠️  IMPORTANT: Replace YOUR-IP with your actual IP address!"
read -p "Enter your public IP address: " USER_IP
aws ec2 authorize-security-group-ingress \
    --group-name matlab-worker-sg \
    --protocol tcp \
    --port 22 \
    --cidr "${USER_IP}/32"

# 3. Add MATLAB worker ports  
echo "🔌 Adding MATLAB worker ports..."
aws ec2 authorize-security-group-ingress \
    --group-name matlab-worker-sg \
    --protocol tcp \
    --port 27350-27364 \
    --cidr "${USER_IP}/32"

# 4. Create key pair (if you don't have one)
echo "🔑 Creating SSH key pair..."
aws ec2 create-key-pair \
    --key-name matlab-worker-key \
    --query 'KeyMaterial' \
    --output text > matlab-worker-key.pem
chmod 400 matlab-worker-key.pem

echo "✅ Key saved as matlab-worker-key.pem"

# 5. Launch EC2 instance
echo "🖥️  Launching EC2 instance (c5.4xlarge)..."
echo "💰 Estimated cost: $0.68/hour (~$16/day for 24h usage)"

INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type c5.4xlarge \
    --key-name matlab-worker-key \
    --security-groups matlab-worker-sg \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=matlab-worker}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "🎉 Instance launching: $INSTANCE_ID"

# 6. Wait for instance to be running
echo "⏳ Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# 7. Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "✅ Instance is running!"
echo "📍 Public IP: $PUBLIC_IP"
echo ""
echo "🎯 Next Steps:"
echo "1. Connect to instance: ssh -i matlab-worker-key.pem ec2-user@$PUBLIC_IP"
echo "2. Install MATLAB Parallel Server on the instance"
echo "3. Configure your local MATLAB to connect to: $PUBLIC_IP"
echo ""
echo "💾 Save this information:"
echo "   Instance ID: $INSTANCE_ID"
echo "   Public IP: $PUBLIC_IP"
echo "   Key File: matlab-worker-key.pem"
