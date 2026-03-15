#!/usr/bin/env python3
"""
MATLAB Cloud Worker Monitor & Cost Tracker
Monitor instance status, costs, and performance
Generated: June 15, 2025
"""

import boto3
import datetime
import json
import subprocess
import sys

class MATLABWorkerMonitor:
    def __init__(self):
        self.ec2 = boto3.client('ec2')
        self.cloudwatch = boto3.client('cloudwatch')
        
        # Cost rates (USD per hour)
        self.instance_costs = {
            'c5.4xlarge': 0.68,
            'c5.9xlarge': 1.53,
            'c5.2xlarge': 0.34,
            'c5.xlarge': 0.17
        }
    
    def get_matlab_instances(self):
        """Find all MATLAB worker instances"""
        try:
            response = self.ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:Name', 'Values': ['matlab-worker']},
                    {'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'stopping']}
                ]
            )
            
            instances = []
            for reservation in response['Reservations']:
                instances.extend(reservation['Instances'])
            
            return instances
        except Exception as e:
            print(f"❌ Error fetching instances: {e}")
            return []
    
    def calculate_costs(self, instance):
        """Calculate running costs for an instance"""
        launch_time = instance['LaunchTime'].replace(tzinfo=None)
        current_time = datetime.datetime.now()
        
        if instance['State']['Name'] == 'running':
            running_time = current_time - launch_time
        else:
            # For stopped instances, we'd need more detailed billing data
            running_time = current_time - launch_time
        
        hours_running = running_time.total_seconds() / 3600
        instance_type = instance['InstanceType']
        hourly_rate = self.instance_costs.get(instance_type, 0.50)  # Default rate
        
        estimated_cost = hours_running * hourly_rate
        daily_cost = hourly_rate * 24
        monthly_cost = daily_cost * 30
        
        return {
            'hours_running': hours_running,
            'hourly_rate': hourly_rate,
            'estimated_cost': estimated_cost,
            'daily_cost': daily_cost,
            'monthly_cost': monthly_cost
        }
    
    def get_instance_metrics(self, instance_id):
        """Get CloudWatch metrics for the instance"""
        try:
            end_time = datetime.datetime.now()
            start_time = end_time - datetime.timedelta(hours=1)
            
            # CPU Utilization
            cpu_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': instance_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average', 'Maximum']
            )
            
            cpu_avg = 0
            cpu_max = 0
            if cpu_response['Datapoints']:
                cpu_avg = sum(d['Average'] for d in cpu_response['Datapoints']) / len(cpu_response['Datapoints'])
                cpu_max = max(d['Maximum'] for d in cpu_response['Datapoints'])
            
            return {
                'cpu_average': cpu_avg,
                'cpu_maximum': cpu_max,
                'datapoints': len(cpu_response['Datapoints'])
            }
        except Exception as e:
            return {'error': str(e)}
    
    def monitor_status(self):
        """Main monitoring function"""
        print("📊 MATLAB Cloud Worker Status Monitor")
        print("=" * 50)
        
        instances = self.get_matlab_instances()
        
        if not instances:
            print("❌ No MATLAB worker instances found")
            print("💡 Run aws_setup_commands.sh to create one")
            return
        
        total_estimated_cost = 0
        
        for i, instance in enumerate(instances, 1):
            print(f"\n🖥️  Instance {i}:")
            print(f"   ID: {instance['InstanceId']}")
            print(f"   Type: {instance['InstanceType']}")
            print(f"   State: {instance['State']['Name']}")
            
            if 'PublicIpAddress' in instance:
                print(f"   Public IP: {instance['PublicIpAddress']}")
            
            print(f"   Launch Time: {instance['LaunchTime']}")
            
            # Cost calculation
            costs = self.calculate_costs(instance)
            print(f"   Running Time: {costs['hours_running']:.1f} hours")
            print(f"   Hourly Rate: ${costs['hourly_rate']:.2f}")
            print(f"   Estimated Cost: ${costs['estimated_cost']:.2f}")
            print(f"   Daily Cost (if 24/7): ${costs['daily_cost']:.2f}")
            print(f"   Monthly Cost (if 24/7): ${costs['monthly_cost']:.2f}")
            
            total_estimated_cost += costs['estimated_cost']
            
            # Performance metrics
            if instance['State']['Name'] == 'running':
                metrics = self.get_instance_metrics(instance['InstanceId'])
                if 'error' not in metrics:
                    print(f"   CPU Average (1h): {metrics['cpu_average']:.1f}%")
                    print(f"   CPU Maximum (1h): {metrics['cpu_maximum']:.1f}%")
                    
                    if metrics['cpu_average'] < 10:
                        print("   ⚠️  Low CPU usage - consider stopping when not in use")
                    elif metrics['cpu_average'] > 80:
                        print("   🔥 High CPU usage - good utilization!")
                
                # Show connection command
                if 'PublicIpAddress' in instance:
                    print(f"   SSH: ssh -i matlab-worker-key.pem ec2-user@{instance['PublicIpAddress']}")
        
        # Summary
        print(f"\n💰 Total Estimated Cost: ${total_estimated_cost:.2f}")
        
        # Cost warnings
        if total_estimated_cost > 50:
            print("⚠️  WARNING: High costs detected!")
            print("💡 Consider using spot instances for 70% savings")
        elif total_estimated_cost > 20:
            print("ℹ️  Moderate usage - monitor costs regularly")
        
        # AWS credits status (approximate)
        if total_estimated_cost < 100:
            print("✅ Within typical AWS student credit limits")
        else:
            print("⚠️  May exceed AWS student credits - check billing")
    
    def stop_all_instances(self):
        """Stop all running MATLAB instances"""
        instances = self.get_matlab_instances()
        running_instances = [i for i in instances if i['State']['Name'] == 'running']
        
        if not running_instances:
            print("ℹ️  No running instances to stop")
            return
        
        print(f"🛑 Stopping {len(running_instances)} instances...")
        
        for instance in running_instances:
            instance_id = instance['InstanceId']
            self.ec2.stop_instances(InstanceIds=[instance_id])
            print(f"   Stopping: {instance_id}")
        
        print("✅ Stop commands sent. Instances will shut down shortly.")
    
    def start_instances(self):
        """Start all stopped MATLAB instances"""
        instances = self.get_matlab_instances()
        stopped_instances = [i for i in instances if i['State']['Name'] == 'stopped']
        
        if not stopped_instances:
            print("ℹ️  No stopped instances to start")
            return
        
        print(f"🚀 Starting {len(stopped_instances)} instances...")
        
        for instance in stopped_instances:
            instance_id = instance['InstanceId']
            self.ec2.start_instances(InstanceIds=[instance_id])
            print(f"   Starting: {instance_id}")
        
        print("✅ Start commands sent. Getting new IP addresses...")
        
        # Wait a moment and show new IPs
        import time
        time.sleep(10)
        
        print("\n📍 New IP addresses:")
        updated_instances = self.get_matlab_instances()
        for instance in updated_instances:
            if instance['State']['Name'] == 'running' and 'PublicIpAddress' in instance:
                print(f"   {instance['InstanceId']}: {instance['PublicIpAddress']}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python monitor_matlab_worker.py [status|stop|start]")
        sys.exit(1)
    
    monitor = MATLABWorkerMonitor()
    command = sys.argv[1].lower()
    
    if command == 'status':
        monitor.monitor_status()
    elif command == 'stop':
        monitor.stop_all_instances()
    elif command == 'start':
        monitor.start_instances()
    else:
        print("Unknown command. Use: status, stop, or start")

if __name__ == "__main__":
    main()
