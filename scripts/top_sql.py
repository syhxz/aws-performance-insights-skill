#!/usr/bin/env python3
"""
AWS Performance Insights Top SQL Analysis Script
Identify top resource-consuming SQL statements - Fixed Version
"""

import argparse
import boto3
import json
from datetime import datetime, timedelta, timezone
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

    def get_top_sql(self, db_resource_id, start_time, end_time, limit=10):
        """Get top SQL statements by database load"""
        try:
            response = self.pi_client.describe_dimension_keys(
                ServiceType='RDS',
                Identifier=db_resource_id,
                Metric='db.load.avg',
                StartTime=start_time,
                EndTime=end_time,
                GroupBy={
                    'Group': 'db.sql_tokenized'
                },
                MaxResults=limit
            )
            return response.get('Keys', [])
        except Exception as e:
            print(f"Error getting top SQL: {e}")
            return []

    def get_wait_events(self, db_resource_id, start_time, end_time, limit=10):
        """Get top wait events"""
        try:
            response = self.pi_client.describe_dimension_keys(
                ServiceType='RDS',
                Identifier=db_resource_id,
                Metric='db.load.avg',
                StartTime=start_time,
                EndTime=end_time,
                GroupBy={
                    'Group': 'db.wait_event'
                },
                MaxResults=limit
            )
            return response.get('Keys', [])
        except Exception as e:
            print(f"Error getting wait events: {e}")
            return []

    def get_db_load_metrics(self, db_resource_id, start_time, end_time):
        """Get database load metrics"""
        try:
            response = self.pi_client.get_resource_metrics(
                ServiceType='RDS',
                Identifier=db_resource_id,
                MetricQueries=[
                    {
                        'Metric': 'db.load.avg'
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                PeriodInSeconds=300
            )
            return response.get('MetricList', [])
        except Exception as e:
            print(f"Error getting load metrics: {e}")
            return []

    def format_sql_statement(self, statement, max_length=100):
        """Format SQL statement for display"""
        if not statement:
            return "N/A"
        
        # Clean up the statement
        statement = statement.strip()
        if len(statement) > max_length:
            return statement[:max_length] + "..."
        return statement

    def generate_report(self, db_resource_id, db_info, start_time, end_time, limit=10):
        """Generate comprehensive Top SQL report"""
        print("=" * 80)
        print("AWS PERFORMANCE INSIGHTS - TOP SQL ANALYSIS")
        print("=" * 80)
        
        if db_info:
            print(f"Database: {db_info.get('engine', 'Unknown')} {db_info.get('engine_version', '')}")
            print(f"Resource ID: {db_resource_id}")
            if 'instance_class' in db_info:
                print(f"Instance Class: {db_info['instance_class']}")
        
        print(f"Analysis Period: {start_time} to {end_time}")
        print(f"Duration: {(end_time - start_time).total_seconds() / 3600:.1f} hours")
        print()

        # Get database load
        print("📊 DATABASE LOAD OVERVIEW")
        print("-" * 40)
        load_metrics = self.get_db_load_metrics(db_resource_id, start_time, end_time)
        if load_metrics and load_metrics[0].get('DataPoints'):
            data_points = load_metrics[0]['DataPoints']
            values = [dp.get('Value', 0) for dp in data_points if 'Value' in dp]
            if values:
                avg_load = sum(values) / len(values)
                max_load = max(values)
                print(f"Average Load: {avg_load:.2f}")
                print(f"Peak Load: {max_load:.2f}")
            else:
                print("No load data available")
        else:
            print("No load data available")
        print()

        # Get Top SQL
        print("🏆 TOP SQL STATEMENTS")
        print("-" * 40)
        top_sql = self.get_top_sql(db_resource_id, start_time, end_time, limit)
        
        if top_sql:
            total_load = sum(sql.get('Total', 0) for sql in top_sql)
            
            for i, sql in enumerate(top_sql, 1):
                dimensions = sql.get('Dimensions', {})
                sql_statement = dimensions.get('db.sql_tokenized.statement', 'N/A')
                sql_id = dimensions.get('db.sql_tokenized.id', 'N/A')
                load_contribution = sql.get('Total', 0)
                percentage = (load_contribution / total_load * 100) if total_load > 0 else 0
                
                print(f"{i}. SQL ID: {sql_id}")
                print(f"   Load: {load_contribution:.4f} ({percentage:.1f}%)")
                print(f"   Statement: {self.format_sql_statement(sql_statement, 120)}")
                print()
        else:
            print("No SQL statements found")
        print()

        # Get Wait Events
        print("⏱️  TOP WAIT EVENTS")
        print("-" * 40)
        wait_events = self.get_wait_events(db_resource_id, start_time, end_time, limit)
        
        if wait_events:
            total_wait = sum(event.get('Total', 0) for event in wait_events)
            
            for i, event in enumerate(wait_events, 1):
                dimensions = event.get('Dimensions', {})
                event_name = dimensions.get('db.wait_event.name', 'N/A')
                event_type = dimensions.get('db.wait_event.type', 'N/A')
                wait_contribution = event.get('Total', 0)
                percentage = (wait_contribution / total_wait * 100) if total_wait > 0 else 0
                
                print(f"{i}. {event_name} ({event_type})")
                print(f"   Wait Time: {wait_contribution:.4f} ({percentage:.1f}%)")
                print()
        else:
            print("No wait events found")

def main():
    parser = argparse.ArgumentParser(description='Analyze top SQL statements using AWS Performance Insights')
    parser.add_argument('--db-resource-id', required=True, 
                       help='RDS resource ID or DB instance/cluster identifier')
    parser.add_argument('--region', default='us-east-1', 
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--profile', 
                       help='AWS profile to use')
    parser.add_argument('--hours', type=int, default=1, 
                       help='Number of hours to analyze (default: 1)')
    parser.add_argument('--limit', type=int, default=10, 
                       help='Maximum number of results to return (default: 10)')
    parser.add_argument('--output-format', choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = TopSQLAnalyzer(region=args.region, profile=args.profile)
        
        # Handle DB identifier vs resource ID
        db_resource_id = args.db_resource_id
        db_info = None
        
        if not db_resource_id.startswith('db-'):
            try:
                db_info = analyzer.get_db_resource_id(args.db_resource_id)
                db_resource_id = db_info['resource_id']
                print(f"Resolved DB identifier '{args.db_resource_id}' to resource ID: {db_resource_id}")
            except Exception as e:
                print(f"Error resolving DB identifier: {e}")
                sys.exit(1)
        
        # Define time range  
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=args.hours)
        
        if args.output_format == 'json':
            # JSON output
            top_sql = analyzer.get_top_sql(db_resource_id, start_time, end_time, args.limit)
            wait_events = analyzer.get_wait_events(db_resource_id, start_time, end_time, args.limit)
            load_metrics = analyzer.get_db_load_metrics(db_resource_id, start_time, end_time)
            
            result = {
                'database_info': db_info,
                'analysis_period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'top_sql': top_sql,
                'wait_events': wait_events,
                'load_metrics': load_metrics
            }
            print(json.dumps(result, indent=2, default=str))
        else:
            # Text report
            analyzer.generate_report(db_resource_id, db_info, start_time, end_time, args.limit)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()