#!/usr/bin/env python3
"""
AWS Performance Insights Metrics Query Script - Fixed Version
Query Performance Insights metrics for RDS and Aurora databases
"""

import argparse
import boto3
import json
from datetime import datetime, timedelta, timezone
import sys
import os

class PIMetricsQuery:
    def __init__(self, region='us-east-1', profile=None):
        """Initialize Performance Insights client"""
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        self.pi_client = session.client('pi', region_name=region)
        self.rds_client = session.client('rds', region_name=region)
        
    def get_db_resource_id(self, db_identifier):
        """Get RDS resource ID from DB instance identifier"""
        try:
            # Try DB instances first
            response = self.rds_client.describe_db_instances(DBInstanceIdentifier=db_identifier)
            if response['DBInstances']:
                db_instance = response['DBInstances'][0]
                return {
                    'resource_id': db_instance['DbiResourceId'],
                    'engine': db_instance['Engine'],
                    'engine_version': db_instance['EngineVersion'],
                    'instance_class': db_instance['DBInstanceClass']
                }
        except self.rds_client.exceptions.DBInstanceNotFoundFault:
            pass
            
        try:
            # Try DB clusters
            response = self.rds_client.describe_db_clusters(DBClusterIdentifier=db_identifier)
            if response['DBClusters']:
                db_cluster = response['DBClusters'][0]
                return {
                    'resource_id': db_cluster['DbClusterResourceId'],
                    'engine': db_cluster['Engine'],
                    'engine_version': db_cluster['EngineVersion']
                }
        except self.rds_client.exceptions.DBClusterNotFoundFault:
            pass
            
        raise ValueError(f"Database {db_identifier} not found")

    def get_engine_specific_metrics(self, engine, metric_type):
        """Get engine-specific metrics based on database engine"""
        
        # Aurora MySQL and MySQL metrics
        if 'mysql' in engine.lower() or 'aurora-mysql' in engine.lower():
            if metric_type == 'cpu':
                return [
                    {'Metric': 'os.cpuUtilization.total'},
                    {'Metric': 'os.cpuUtilization.user'},
                    {'Metric': 'os.cpuUtilization.system'},
                    {'Metric': 'db.load.avg'}
                ]
            elif metric_type == 'memory':
                return [
                    {'Metric': 'os.memory.total'},
                    {'Metric': 'os.memory.free'},
                    {'Metric': 'os.memory.active'},
                    {'Metric': 'os.memory.cached'}
                ]
            elif metric_type == 'io':
                return [
                    {'Metric': 'os.diskIO.auroraStorage.readThroughput'},
                    {'Metric': 'os.diskIO.auroraStorage.writeThroughput'},
                    {'Metric': 'os.diskIO.auroraStorage.readLatency'},
                    {'Metric': 'os.diskIO.auroraStorage.writeLatency'}
                ]
            elif metric_type == 'connections':
                return [
                    {'Metric': 'db.Users.Connections'},
                    {'Metric': 'db.Users.Threads_connected'},
                    {'Metric': 'db.Users.Threads_running'}
                ]
            elif metric_type == 'load':
                return [
                    {'Metric': 'db.load.avg'}
                ]
        
        # PostgreSQL metrics
        elif 'postgres' in engine.lower() or 'aurora-postgresql' in engine.lower():
            if metric_type == 'cpu':
                return [
                    {'Metric': 'os.cpuUtilization.total'},
                    {'Metric': 'db.load.avg'}
                ]
            elif metric_type == 'memory':
                return [
                    {'Metric': 'os.memory.total'},
                    {'Metric': 'os.memory.free'}
                ]
        
        # Fallback to basic metrics
        return self._get_generic_metrics(metric_type)
    
    def _get_generic_metrics(self, metric_type):
        """Get generic metrics that should work across engines"""
        if metric_type == 'load':
            return [{'Metric': 'db.load.avg'}]
        elif metric_type == 'cpu':
            return [
                {'Metric': 'os.cpuUtilization.total'},
                {'Metric': 'db.load.avg'}
            ]
        elif metric_type == 'memory':
            return [
                {'Metric': 'os.memory.total'},
                {'Metric': 'os.memory.free'}
            ]
        else:
            return [{'Metric': 'db.load.avg'}]

    def query_metrics(self, db_resource_id, metric_queries, start_time, end_time, period=300):
        """Query Performance Insights metrics"""
        try:
            response = self.pi_client.get_resource_metrics(
                ServiceType='RDS',
                Identifier=db_resource_id,
                MetricQueries=metric_queries,
                StartTime=start_time,
                EndTime=end_time,
                PeriodInSeconds=period
            )
            return response
        except Exception as e:
            print(f"Error querying metrics: {e}")
            return None

    def format_metrics_output(self, response, output_format='table'):
        """Format metrics output"""
        if not response or 'MetricList' not in response:
            print("No metrics data available")
            return
        
        if output_format == 'json':
            print(json.dumps(response, indent=2, default=str))
            return
        
        # Table format
        metric_list = response['MetricList']
        
        print(f"\nMetrics Query Results:")
        print(f"Time Range: {response.get('AlignedStartTime', 'N/A')} to {response.get('AlignedEndTime', 'N/A')}")
        print("=" * 100)
        
        for metric in metric_list:
            metric_name = metric['Key']['Metric']
            data_points = metric.get('DataPoints', [])
            
            print(f"\nMetric: {metric_name}")
            print("-" * 60)
            
            if not data_points:
                print("No data points available")
                continue
            
            # Calculate statistics
            values = [dp.get('Value', 0) for dp in data_points if 'Value' in dp]
            if values:
                avg_value = sum(values) / len(values)
                max_value = max(values)
                min_value = min(values)
                
                print(f"Average: {avg_value:.2f}")
                print(f"Maximum: {max_value:.2f}")
                print(f"Minimum: {min_value:.2f}")
                print(f"Data Points: {len(values)}")
            else:
                print("No valid data points")
            
            # Show recent data points
            if len(data_points) > 0:
                print("\nRecent Data Points:")
                recent_points = data_points[-5:] if len(data_points) > 5 else data_points
                for dp in recent_points:
                    timestamp = dp.get('Timestamp', 'N/A')
                    value = dp.get('Value', 'N/A')
                    print(f"  {timestamp}: {value}")

def main():
    parser = argparse.ArgumentParser(description='Query AWS Performance Insights metrics')
    parser.add_argument('--db-resource-id', required=True, 
                       help='RDS resource ID or DB instance/cluster identifier')
    parser.add_argument('--metric-type', 
                       choices=['cpu', 'memory', 'io', 'connections', 'load'], 
                       default='load',
                       help='Type of metrics to query (default: load)')
    parser.add_argument('--region', default='us-east-1', 
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--profile', 
                       help='AWS profile to use')
    parser.add_argument('--hours', type=int, default=1, 
                       help='Number of hours to query (default: 1)')
    parser.add_argument('--period', type=int, default=300, 
                       choices=[60, 300, 3600, 86400],
                       help='Period in seconds (default: 300)')
    parser.add_argument('--output-format', choices=['table', 'json'], default='table',
                       help='Output format (default: table)')
    
    args = parser.parse_args()
    
    try:
        # Initialize PI client
        pi_query = PIMetricsQuery(region=args.region, profile=args.profile)
        
        # Handle DB identifier vs resource ID
        db_resource_id = args.db_resource_id
        db_info = None
        
        if not db_resource_id.startswith('db-'):
            try:
                db_info = pi_query.get_db_resource_id(args.db_resource_id)
                db_resource_id = db_info['resource_id']
                print(f"Resolved DB identifier '{args.db_resource_id}' to resource ID: {db_resource_id}")
                print(f"Database Engine: {db_info['engine']} {db_info['engine_version']}")
            except Exception as e:
                print(f"Error resolving DB identifier: {e}")
                sys.exit(1)
        else:
            # Try to get engine info for resource ID
            db_info = {'resource_id': db_resource_id, 'engine': 'unknown', 'engine_version': 'unknown'}
        
        # Define time range
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=args.hours)
        
        # Define metric queries based on engine and type
        if db_info and db_info['engine'] != 'unknown':
            metric_queries = pi_query.get_engine_specific_metrics(db_info['engine'], args.metric_type)
        else:
            # Fallback to generic metrics
            metric_queries = pi_query._get_generic_metrics(args.metric_type)
        
        print(f"Querying {args.metric_type} metrics for {db_resource_id}")
        print(f"Time range: {start_time} to {end_time}")
        
        # Query metrics
        response = pi_query.query_metrics(
            db_resource_id=db_resource_id,
            metric_queries=metric_queries,
            start_time=start_time,
            end_time=end_time,
            period=args.period
        )
        
        if response:
            pi_query.format_metrics_output(response, args.output_format)
        else:
            print("Failed to retrieve metrics")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()