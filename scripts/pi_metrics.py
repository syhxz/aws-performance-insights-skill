#!/usr/bin/env python3
"""
AWS Performance Insights Metrics Query Script
Query Performance Insights metrics for RDS and Aurora databases
"""

import argparse
import boto3
import json
from datetime import datetime, timedelta
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
                return response['DBInstances'][0]['DbiResourceId']
        except self.rds_client.exceptions.DBInstanceNotFoundFault:
            pass
            
        try:
            # Try DB clusters
            response = self.rds_client.describe_db_clusters(DBClusterIdentifier=db_identifier)
            if response['DBClusters']:
                return response['DBClusters'][0]['DbClusterResourceId']
        except self.rds_client.exceptions.DBClusterNotFoundFault:
            pass
            
        raise ValueError(f"Database {db_identifier} not found")
    
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
            print(f"Error querying metrics: {str(e)}")
            return None
    
    def format_metric_results(self, response, output_format='table'):
        """Format metric query results"""
        if not response or 'MetricList' not in response:
            return "No metrics data available"
            
        if output_format == 'json':
            return json.dumps(response, indent=2, default=str)
            
        # Table format
        results = []
        for metric in response['MetricList']:
            metric_name = metric['Key']['Metric']
            results.append(f"\n=== {metric_name} ===")
            
            if 'DataPoints' in metric:
                for point in metric['DataPoints']:
                    timestamp = point['Timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    value = point.get('Value', 'N/A')
                    results.append(f"{timestamp}: {value}")
            else:
                results.append("No data points available")
                
        return '\n'.join(results)

def main():
    parser = argparse.ArgumentParser(description='Query AWS Performance Insights metrics')
    parser.add_argument('--db-resource-id', required=True, help='RDS resource ID or DB identifier')
    parser.add_argument('--metric-type', default='cpu', 
                       choices=['cpu', 'memory', 'io', 'connections', 'throughput'],
                       help='Type of metrics to query')
    parser.add_argument('--hours', type=int, default=1, help='Number of hours to query (default: 1)')
    parser.add_argument('--period', type=int, default=300, help='Period in seconds (default: 300)')
    parser.add_argument('--region', default=os.getenv('AWS_REGION', 'us-east-1'), help='AWS region')
    parser.add_argument('--profile', default=os.getenv('AWS_PROFILE'), help='AWS profile')
    parser.add_argument('--output-format', default='table', choices=['table', 'json'], 
                       help='Output format')
    
    args = parser.parse_args()
    
    # Initialize PI client
    pi_query = PIMetricsQuery(region=args.region, profile=args.profile)
    
    # Handle DB identifier vs resource ID
    db_resource_id = args.db_resource_id
    if not db_resource_id.startswith('db-'):
        try:
            db_resource_id = pi_query.get_db_resource_id(args.db_resource_id)
            print(f"Resolved DB identifier '{args.db_resource_id}' to resource ID: {db_resource_id}")
        except Exception as e:
            print(f"Error resolving DB identifier: {e}")
            sys.exit(1)
    
    # Define time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=args.hours)
    
    # Define metric queries based on type
    metric_queries = []
    
    if args.metric_type == 'cpu':
        metric_queries = [
            {
                'Metric': 'db.CPU.Innodb.pct',
                'GroupBy': {'Group': 'db.SQL_ID.Innodb.select.avg_timer_wait.avg'}
            },
            {
                'Metric': 'db.CPU.total.pct'
            }
        ]
    elif args.metric_type == 'memory':
        metric_queries = [
            {
                'Metric': 'db.Memory.total.pct'
            }
        ]
    elif args.metric_type == 'io':
        metric_queries = [
            {
                'Metric': 'db.IO.total.pct'
            }
        ]
    elif args.metric_type == 'connections':
        metric_queries = [
            {
                'Metric': 'db.Connections.Avg'
            }
        ]
    elif args.metric_type == 'throughput':
        metric_queries = [
            {
                'Metric': 'db.Transactions.Avg'
            }
        ]
    
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
        formatted_results = pi_query.format_metric_results(response, args.output_format)
        print(formatted_results)
    else:
        print("Failed to retrieve metrics")
        sys.exit(1)

if __name__ == '__main__':
    main()