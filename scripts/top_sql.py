#!/usr/bin/env python3
"""
AWS Performance Insights Top SQL Analysis Script
Identify top resource-consuming SQL statements
"""

import argparse
import boto3
import json
from datetime import datetime, timedelta
import sys
import os

class TopSQLAnalyzer:
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
    
    def get_engine_sql_metrics(self, engine):
        """Get engine-specific SQL metrics for top SQL analysis"""
        if 'mysql' in engine.lower():
            return {
                'metric': 'db.SQL.Innodb.avg_timer_wait.avg',
                'group_by': {'Group': 'db.sql_tokenized.id'}
            }
        elif 'postgres' in engine.lower():
            # For PostgreSQL, use load metrics grouped by wait events as SQL info is limited
            return {
                'metric': 'db.load.avg', 
                'group_by': {'Group': 'db.wait_event.name'}
            }
        else:
            # Generic fallback
            return {
                'metric': 'db.load.avg',
                'group_by': {'Group': 'db.wait_event.name'}
            }
    
    def get_top_sql_statements(self, db_resource_id, engine, start_time, end_time, limit=10):
        """Get top SQL statements by resource consumption"""
        try:
            # Get engine-specific SQL metrics
            sql_config = self.get_engine_sql_metrics(engine)
            
            # Query dimension keys for SQL statements
            response = self.pi_client.describe_dimension_keys(
                ServiceType='RDS',
                Identifier=db_resource_id,
                Metric=sql_config['metric'],
                StartTime=start_time,
                EndTime=end_time,
                GroupBy=sql_config['group_by'],
                MaxResults=limit
            )
            return response
        except Exception as e:
            print(f"Error querying top SQL statements: {str(e)}")
            return None
    
    def get_sql_details(self, db_resource_id, sql_ids):
        """Get detailed information for specific SQL IDs"""
        try:
            response = self.pi_client.get_dimension_key_details(
                ServiceType='RDS',
                Identifier=db_resource_id,
                Group='db.sql_tokenized.id',
                GroupIdentifier=sql_ids[0] if sql_ids else '',
                RequestedDimensions=['db.sql_tokenized.statement']
            )
            return response
        except Exception as e:
            print(f"Error getting SQL details: {str(e)}")
            return None
    
    def format_top_sql_results(self, response, output_format='table'):
        """Format top SQL analysis results"""
        if not response or 'Keys' not in response:
            return "No SQL data available"
            
        if output_format == 'json':
            return json.dumps(response, indent=2, default=str)
            
        # Table format
        results = []
        results.append("=== TOP SQL STATEMENTS ===\n")
        
        for i, key in enumerate(response['Keys'], 1):
            sql_id = key.get('Dimensions', {}).get('db.sql_tokenized.id', 'Unknown')
            total = key.get('Total', 0)
            
            results.append(f"{i}. SQL ID: {sql_id}")
            results.append(f"   Total Resource Consumption: {total:.2f}")
            
            if 'Partitions' in key:
                results.append("   Time-based breakdown:")
                for partition in key['Partitions']:
                    timestamp = partition.get('Keys', [{}])[0].get('Timestamp', 'Unknown')
                    value = partition.get('Keys', [{}])[0].get('Value', 0)
                    results.append(f"     {timestamp}: {value:.2f}")
            
            results.append("")  # Empty line between SQL statements
                
        return '\n'.join(results)

def main():
    parser = argparse.ArgumentParser(description='Analyze top SQL statements in Performance Insights')
    parser.add_argument('--db-resource-id', required=True, help='RDS resource ID or DB identifier')
    parser.add_argument('--limit', type=int, default=10, help='Number of top SQL statements to retrieve (default: 10)')
    parser.add_argument('--hours', type=int, default=1, help='Number of hours to analyze (default: 1)')
    parser.add_argument('--period', type=int, default=3600, help='Period in seconds (default: 3600)')
    parser.add_argument('--region', default=os.getenv('AWS_REGION', 'us-east-1'), help='AWS region')
    parser.add_argument('--profile', default=os.getenv('AWS_PROFILE'), help='AWS profile')
    parser.add_argument('--output-format', default='table', choices=['table', 'json'], 
                       help='Output format')
    parser.add_argument('--metric', default='db.SQL.Innodb.avg_timer_wait.avg',
                       help='Metric to use for ranking SQL statements')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = TopSQLAnalyzer(region=args.region, profile=args.profile)
    
    # Handle DB identifier vs resource ID
    db_resource_id = args.db_resource_id
    db_info = None
    engine = 'unknown'
    
    if not db_resource_id.startswith('db-'):
        try:
            db_info = analyzer.get_db_resource_id(args.db_resource_id)
            db_resource_id = db_info['resource_id']
            engine = db_info['engine']
            print(f"Resolved DB identifier '{args.db_resource_id}' to resource ID: {db_resource_id}")
            print(f"Database Engine: {engine} {db_info['engine_version']}")
        except Exception as e:
            print(f"Error resolving DB identifier: {e}")
            sys.exit(1)
    else:
        print(f"Using resource ID: {db_resource_id}")
        print("Warning: Engine type unknown, using generic SQL analysis")
    
    # Define time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=args.hours)
    
    print(f"Analyzing top {args.limit} SQL statements for {db_resource_id}")
    print(f"Time range: {start_time} to {end_time}")
    
    # Get top SQL statements
    response = analyzer.get_top_sql_statements(
        db_resource_id=db_resource_id,
        engine=engine,
        start_time=start_time,
        end_time=end_time,
        limit=args.limit
    )
    
    if response:
        formatted_results = analyzer.format_top_sql_results(response, args.output_format)
        print(formatted_results)
    else:
        print("Failed to retrieve top SQL statements")
        sys.exit(1)

if __name__ == '__main__':
    main()