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
                db_instance = response['DBInstances'][0]
                return {
                    'resource_id': db_instance['DbiResourceId'],
                    'engine': db_instance['Engine'],
                    'engine_version': db_instance['EngineVersion']
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
        if 'mysql' in engine.lower():
            return self._get_mysql_metrics(metric_type)
        elif 'postgres' in engine.lower():
            return self._get_postgresql_metrics(metric_type)
        else:
            # Default to generic metrics
            return self._get_generic_metrics(metric_type)
    
    def _get_mysql_metrics(self, metric_type):
        """Get MySQL/Aurora MySQL specific metrics"""
        if metric_type == 'cpu':
            return [
                {'Metric': 'db.CPU.total.pct'},
                {'Metric': 'db.CPU.Innodb.pct'}
            ]
        elif metric_type == 'memory':
            return [
                {'Metric': 'db.Memory.total.pct'},
                {'Metric': 'db.Memory.Innodb.pct'}
            ]
        elif metric_type == 'io':
            return [
                {'Metric': 'db.IO.total.pct'},
                {'Metric': 'db.IO.read.pct'},
                {'Metric': 'db.IO.write.pct'}
            ]
        elif metric_type == 'connections':
            return [
                {'Metric': 'db.Connections.Avg'},
                {'Metric': 'db.Connections.Max'}
            ]
        elif metric_type == 'throughput':
            return [
                {'Metric': 'db.Transactions.Avg'},
                {'Metric': 'db.Queries.Avg'}
            ]
        else:
            return [{'Metric': 'db.load.avg'}]
    
    def _get_postgresql_metrics(self, metric_type):
        """Get PostgreSQL/Aurora PostgreSQL specific metrics"""
        if metric_type == 'cpu':
            return [
                {'Metric': 'db.load.avg'}
            ]
        elif metric_type == 'memory':
            return [
                {'Metric': 'db.connections.avg'}
            ]
        elif metric_type == 'io':
            return [
                {'Metric': 'db.SQL.postgresql.select.calls_per_sec.avg'},
                {'Metric': 'db.SQL.postgresql.insert.calls_per_sec.avg'}
            ]
        elif metric_type == 'connections':
            return [
                {'Metric': 'db.connections.avg'}
            ]
        elif metric_type == 'throughput':
            return [
                {'Metric': 'db.SQL.postgresql.update.calls_per_sec.avg'},
                {'Metric': 'db.SQL.postgresql.delete.calls_per_sec.avg'}
            ]
        else:
            return [{'Metric': 'db.load.avg'}]
    
    def _get_generic_metrics(self, metric_type):
        """Get generic metrics that work across engines"""
        if metric_type == 'cpu':
            return [{'Metric': 'db.load.avg'}]
        elif metric_type == 'connections':
            return [{'Metric': 'db.connections.avg'}]
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
        try:
            # This is a bit more complex for resource IDs, we'll use generic metrics
            db_info = {'resource_id': db_resource_id, 'engine': 'unknown', 'engine_version': 'unknown'}
        except Exception:
            db_info = {'resource_id': db_resource_id, 'engine': 'unknown', 'engine_version': 'unknown'}
    
    # Define time range
    end_time = datetime.utcnow()
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
        formatted_results = pi_query.format_metric_results(response, args.output_format)
        print(formatted_results)
    else:
        print("Failed to retrieve metrics")
        sys.exit(1)

if __name__ == '__main__':
    main()