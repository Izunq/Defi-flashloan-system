#!/usr/bin/env python3
"""
MATLAB Cloud Worker Quick Setup Script
Automated setup for Local MATLAB + Cloud Worker hybrid architecture
"""

import boto3
import json
import time
import subprocess
import os
from pathlib import Path

class MATLABCloudWorkerSetup:
    def __init__(self):
        self.setup_info = {
            "instance_type": "c5.4xlarge",  # 16 vCPU, 32 GB RAM
            "region": "us-east-1",  # Cheapest region typically
            "matlab_version": "R2024b",
            "estimated_hourly_cost": 0.68,
            "spot_instance_savings": "~70%"
        }
        
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        print("🔍 Checking Prerequisites...")
        
        checks = {
            "AWS CLI": self._check_aws_cli(),
            "MATLAB Local": self._check_matlab_local(),
            "SSH Key": self._check_ssh_key(),
            "AWS Credentials": self._check_aws_credentials()
        }
        
        for check, status in checks.items():
            print(f"   {check}: {'✅ PASS' if status else '❌ NEEDS SETUP'}")
            
        return all(checks.values())
    
    def _check_aws_cli(self):
        """Check if AWS CLI is installed"""
        try:
            result = subprocess.run(['aws', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _check_matlab_local(self):
        """Check if MATLAB is installed locally"""
        # Check common MATLAB installation paths on Windows
        matlab_paths = [
            r"C:\Program Files\MATLAB",
            r"C:\Program Files (x86)\MATLAB",
            "C:\\MATLAB"
        ]
        
        for path in matlab_paths:
            if os.path.exists(path):
                return True
        return False
    
    def _check_ssh_key(self):
        """Check if SSH key exists"""
        ssh_dir = Path.home() / ".ssh"
        return ssh_dir.exists() and any(ssh_dir.glob("*.pem"))
    
    def _check_aws_credentials(self):
        """Check if AWS credentials are configured"""
        try:
            boto3.client('sts').get_caller_identity()
            return True
        except:
            return False
    
    def estimate_costs(self):
        """Calculate cost estimates for different usage patterns"""
        print("\n💰 Cost Estimation:")
        
        patterns = {
            "Light Usage (2 hours/day)": 2 * 30,
            "Medium Usage (4 hours/day)": 4 * 30,
            "Heavy Usage (8 hours/day)": 8 * 30,
            "24/7 Development": 24 * 30
        }
        
        for pattern, hours_per_month in patterns.items():
            on_demand_cost = hours_per_month * self.setup_info["estimated_hourly_cost"]
            spot_cost = on_demand_cost * 0.3  # 70% savings typical
            
            print(f"   {pattern}:")
            print(f"     On-Demand: ${on_demand_cost:.2f}/month")
            print(f"     Spot Instance: ${spot_cost:.2f}/month")
            print(f"     Your AWS Credits: {'✅ COVERED' if on_demand_cost < 100 else '⚠️ MONITOR'}")
    
    def generate_aws_setup_commands(self):
        """Generate AWS CLI commands for setup"""
        commands = [
            "# 1. Create security group for MATLAB",
            "aws ec2 create-security-group --group-name matlab-worker-sg --description 'MATLAB Cloud Worker Security Group'",
            "",
            "# 2. Add SSH access (replace YOUR-IP with your actual IP)",
            "aws ec2 authorize-security-group-ingress --group-name matlab-worker-sg --protocol tcp --port 22 --cidr YOUR-IP/32",
            "",
            "# 3. Add MATLAB worker ports",
            "aws ec2 authorize-security-group-ingress --group-name matlab-worker-sg --protocol tcp --port 27350-27364 --cidr YOUR-IP/32",
            "",
            "# 4. Create key pair (if you don't have one)",
            "aws ec2 create-key-pair --key-name matlab-worker-key --query 'KeyMaterial' --output text > matlab-worker-key.pem",
            "chmod 400 matlab-worker-key.pem",
            "",
            "# 5. Launch EC2 instance",
            f"aws ec2 run-instances --image-id ami-0c02fb55956c7d316 --count 1 --instance-type {self.setup_info['instance_type']} --key-name matlab-worker-key --security-groups matlab-worker-sg"
        ]
        
        return commands
    
    def generate_matlab_config(self):
        """Generate MATLAB configuration script"""
        matlab_script = """
% MATLAB Cloud Worker Configuration Script
% Run this in your local MATLAB after setting up the EC2 instance

fprintf('🚀 Setting up MATLAB Cloud Worker Connection...\\n');

% Replace with your EC2 instance IP
EC2_IP = 'YOUR-EC2-INSTANCE-IP';  % Get this from AWS console
KEY_FILE = 'C:\\path\\to\\matlab-worker-key.pem';  % Update path

try
    % Create cluster profile
    c = parcluster('generic');
    
    % Configure connection
    c.Host = EC2_IP;
    c.NumWorkers = 16;  % Match your EC2 instance vCPUs
    c.OperatingSystem = 'unix';
    c.Username = 'ec2-user';
    c.IdentityFile = KEY_FILE;
    
    % Set job storage location
    c.JobStorageLocation = 'C:\\temp\\matlab_jobs';
    if ~exist(c.JobStorageLocation, 'dir')
        mkdir(c.JobStorageLocation);
    end
    
    % Save profile
    c.saveProfile('CloudWorker');
    
    fprintf('✅ Cloud worker profile created successfully!\\n');
    fprintf('   Profile name: CloudWorker\\n');
    fprintf('   Host: %s\\n', EC2_IP);
    fprintf('   Workers: %d\\n', c.NumWorkers);
    
    % Test connection
    fprintf('🔍 Testing connection...\\n');
    parpool(c, 2);  % Start with 2 workers for testing
    
    % Simple test job
    tic;
    result = parfor_test();
    test_time = toc;
    
    fprintf('✅ Connection test successful!\\n');
    fprintf('   Test completed in %.2f seconds\\n', test_time);
    
    delete(gcp('nocreate'));  % Close pool
    
catch ME
    fprintf('❌ Setup failed: %s\\n', ME.message);
    fprintf('🔧 Check your EC2 instance and network settings\\n');
end

function result = parfor_test()
    % Simple parallel test function
    result = zeros(1000, 1);
    parfor i = 1:1000
        result(i) = sum(rand(100, 100), 'all');
    end
end
"""
        return matlab_script
    
    def create_monitoring_script(self):
        """Create a monitoring script for the cloud worker"""
        monitor_script = """
#!/usr/bin/env python3
'''
MATLAB Cloud Worker Monitor
Check instance status, costs, and performance
'''

import boto3
import datetime

def monitor_matlab_worker():
    ec2 = boto3.client('ec2')
    
    # Get instance information
    response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Name', 'Values': ['matlab-worker']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )
    
    if not response['Reservations']:
        print("❌ No running MATLAB worker instances found")
        return
    
    instance = response['Reservations'][0]['Instances'][0]
    
    print("📊 MATLAB Cloud Worker Status:")
    print(f"   Instance ID: {instance['InstanceId']}")
    print(f"   Type: {instance['InstanceType']}")
    print(f"   State: {instance['State']['Name']}")
    print(f"   Public IP: {instance.get('PublicIpAddress', 'N/A')}")
    print(f"   Launch Time: {instance['LaunchTime']}")
    
    # Calculate running time and estimated cost
    launch_time = instance['LaunchTime'].replace(tzinfo=None)
    running_time = datetime.datetime.now() - launch_time
    hours_running = running_time.total_seconds() / 3600
    estimated_cost = hours_running * 0.68  # c5.4xlarge on-demand rate
    
    print(f"   Running Time: {hours_running:.1f} hours")
    print(f"   Estimated Cost: ${estimated_cost:.2f}")
    
    if estimated_cost > 20:
        print("⚠️  WARNING: High usage detected. Consider using spot instances.")

if __name__ == "__main__":
    monitor_matlab_worker()
"""
        return monitor_script
    
    def run_full_setup(self):
        """Run the complete setup process"""
        print("🚀 MATLAB Cloud Worker Setup Assistant")
        print("=" * 50)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Please install missing prerequisites first")
            self.show_prerequisite_help()
            return
        
        # Show cost estimates
        self.estimate_costs()
        
        # Generate setup files
        print("\n📝 Generating Setup Files...")
        
        # AWS setup commands
        with open('aws_setup_commands.sh', 'w') as f:
            f.write('\n'.join(self.generate_aws_setup_commands()))
        print("   ✅ aws_setup_commands.sh created")
        
        # MATLAB configuration
        with open('matlab_cloud_config.m', 'w') as f:
            f.write(self.generate_matlab_config())
        print("   ✅ matlab_cloud_config.m created")
        
        # Monitoring script
        with open('monitor_matlab_worker.py', 'w') as f:
            f.write(self.create_monitoring_script())
        print("   ✅ monitor_matlab_worker.py created")
        
        # Next steps
        print("\n🎯 Next Steps:")
        print("1. Run: chmod +x aws_setup_commands.sh")
        print("2. Edit aws_setup_commands.sh to add your IP address")
        print("3. Run: ./aws_setup_commands.sh")
        print("4. Get EC2 instance IP from AWS console")
        print("5. Edit matlab_cloud_config.m with instance IP and key path")
        print("6. Run matlab_cloud_config.m in your local MATLAB")
        print("7. Test with: parpool('CloudWorker')")
        
        print("\n🎉 Setup files generated! Ready for implementation.")
    
    def show_prerequisite_help(self):
        """Show help for installing prerequisites"""
        print("\n📋 Prerequisites Installation Guide:")
        print("\n1. AWS CLI:")
        print("   Download: https://aws.amazon.com/cli/")
        print("   Or run: pip install awscli")
        
        print("\n2. Configure AWS:")
        print("   Run: aws configure")
        print("   Enter your AWS access key and secret")
        
        print("\n3. MATLAB License:")
        print("   Ensure your campus license includes Parallel Computing Toolbox")

def main():
    setup = MATLABCloudWorkerSetup()
    setup.run_full_setup()

if __name__ == "__main__":
    main()
