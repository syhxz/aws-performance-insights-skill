#!/usr/bin/env python3
"""
AWS Performance Insights Comprehensive Report Generator - Fixed Version
Generate detailed performance analysis reports
"""

import argparse
import boto3
import json
from datetime import datetime, timedelta, timezone
import sys
import os

class PerformanceReportGenerator:
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
                    'instance_class': db_instance['DBInstanceClass'],
                    'allocated_storage': db_instance['AllocatedStorage']
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
                    'engine_version': db_cluster['EngineVersion'],
                    'allocated_storage': db_cluster['AllocatedStorage']
                }
        except self.rds_client.exceptions.DBClusterNotFoundFault:
            pass
            
        raise ValueError(f"Database {db_identifier} not found")

    def get_db_load_metrics(self, db_resource_id, start_time, end_time):
        """Get database load metrics"""
        try:
            response = self.pi_client.get_resource_metrics(
                ServiceType='RDS',
                Identifier=db_resource_id,
                MetricQueries=[{'Metric': 'db.load.avg'}],
                StartTime=start_time,
                EndTime=end_time,
                PeriodInSeconds=300
            )
            return response.get('MetricList', [])
        except Exception as e:
            return {'error': str(e)}

    def get_top_sql(self, db_resource_id, start_time, end_time, limit=10):
        """Get top SQL statements"""
        try:
            response = self.pi_client.describe_dimension_keys(
                ServiceType='RDS',
                Identifier=db_resource_id,
                Metric='db.load.avg',
                StartTime=start_time,
                EndTime=end_time,
                GroupBy={'Group': 'db.sql_tokenized'},
                MaxResults=limit
            )
            return response.get('Keys', [])
        except Exception as e:
            return {'error': str(e)}

    def get_wait_events(self, db_resource_id, start_time, end_time, limit=10):
        """Get wait events"""
        try:
            response = self.pi_client.describe_dimension_keys(
                ServiceType='RDS',
                Identifier=db_resource_id,
                Metric='db.load.avg',
                StartTime=start_time,
                EndTime=end_time,
                GroupBy={'Group': 'db.wait_event'},
                MaxResults=limit
            )
            return response.get('Keys', [])
        except Exception as e:
            return {'error': str(e)}

    def get_user_activity(self, db_resource_id, start_time, end_time, limit=10):
        """Get database user activity"""
        try:
            response = self.pi_client.describe_dimension_keys(
                ServiceType='RDS',
                Identifier=db_resource_id,
                Metric='db.load.avg',
                StartTime=start_time,
                EndTime=end_time,
                GroupBy={'Group': 'db.user'},
                MaxResults=limit
            )
            return response.get('Keys', [])
        except Exception as e:
            return {'error': str(e)}

    def generate_report(self, db_resource_id, db_info, start_time, end_time, output_format='json'):
        """Generate comprehensive performance report"""
        
        print("Collecting database load metrics...")
        load_metrics = self.get_db_load_metrics(db_resource_id, start_time, end_time)
        
        print("Collecting top SQL statements...")
        top_sql = self.get_top_sql(db_resource_id, start_time, end_time)
        
        print("Collecting wait events...")
        wait_events = self.get_wait_events(db_resource_id, start_time, end_time)
        
        print("Collecting user activity...")
        user_activity = self.get_user_activity(db_resource_id, start_time, end_time)
        
        print("Generating report...")
        
        # Build report data
        report_data = {
            "database_info": {
                "resource_id": db_resource_id,
                "engine": db_info.get('engine', 'unknown'),
                "engine_version": db_info.get('engine_version', 'unknown'),
                "instance_class": db_info.get('instance_class', 'unknown'),
                "allocated_storage": db_info.get('allocated_storage', 0)
            },
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "metrics": {
                "load": load_metrics if not isinstance(load_metrics, dict) else load_metrics
            },
            "top_sql": top_sql if not isinstance(top_sql, dict) else top_sql,
            "wait_events": wait_events if not isinstance(wait_events, dict) else wait_events,
            "user_activity": user_activity if not isinstance(user_activity, dict) else user_activity
        }
        
        if output_format == 'json':
            return json.dumps(report_data, indent=2, default=str)
        else:
            return self._format_text_report(report_data)
    
    def _format_text_report(self, report_data):
        """Format report as readable text"""
        lines = []
        lines.append("=" * 80)
        lines.append("AWS PERFORMANCE INSIGHTS - COMPREHENSIVE REPORT")
        lines.append("=" * 80)
        
        # Database info
        db_info = report_data['database_info']
        lines.append(f"Database Engine: {db_info['engine']} {db_info['engine_version']}")
        lines.append(f"Resource ID: {db_info['resource_id']}")
        lines.append(f"Instance Class: {db_info['instance_class']}")
        lines.append(f"Storage: {db_info['allocated_storage']} GB")
        lines.append("")
        
        # Time range
        time_info = report_data['time_range']
        lines.append(f"Analysis Period: {time_info['start']} to {time_info['end']}")
        lines.append("")
        
        # Load metrics
        lines.append("📊 DATABASE LOAD METRICS")
        lines.append("-" * 40)
        load_metrics = report_data['metrics']['load']
        if isinstance(load_metrics, list) and load_metrics:
            data_points = load_metrics[0].get('DataPoints', [])
            values = [dp.get('Value', 0) for dp in data_points if 'Value' in dp]
            if values:
                lines.append(f"Average Load: {sum(values)/len(values):.2f}")
                lines.append(f"Peak Load: {max(values):.2f}")
                lines.append(f"Data Points: {len(values)}")
            else:
                lines.append("No load data available")
        elif isinstance(load_metrics, dict) and 'error' in load_metrics:
            lines.append(f"Error: {load_metrics['error']}")
        else:
            lines.append("No load data available")
        lines.append("")
        
        # Top SQL
        lines.append("🏆 TOP SQL STATEMENTS")
        lines.append("-" * 40)
        top_sql = report_data['top_sql']
        if isinstance(top_sql, list) and top_sql:
            for i, sql in enumerate(top_sql[:5], 1):
                dimensions = sql.get('Dimensions', {})
                sql_statement = dimensions.get('db.sql_tokenized.statement', 'N/A')
                load_contribution = sql.get('Total', 0)
                lines.append(f"{i}. Load: {load_contribution:.4f}")
                lines.append(f"   Statement: {sql_statement[:100]}{'...' if len(sql_statement) > 100 else ''}")
                lines.append("")
        elif isinstance(top_sql, dict) and 'error' in top_sql:
            lines.append(f"Error: {top_sql['error']}")
        else:
            lines.append("No SQL data available")
        lines.append("")
        
        # Wait Events
        lines.append("⏱️  TOP WAIT EVENTS")
        lines.append("-" * 40)
        wait_events = report_data['wait_events']
        if isinstance(wait_events, list) and wait_events:
            for i, event in enumerate(wait_events[:5], 1):
                dimensions = event.get('Dimensions', {})
                event_name = dimensions.get('db.wait_event.name', 'N/A')
                event_type = dimensions.get('db.wait_event.type', 'N/A')
                wait_contribution = event.get('Total', 0)
                lines.append(f"{i}. {event_name} ({event_type})")
                lines.append(f"   Wait Time: {wait_contribution:.4f}")
                lines.append("")
        elif isinstance(wait_events, dict) and 'error' in wait_events:
            lines.append(f"Error: {wait_events['error']}")
        else:
            lines.append("No wait event data available")
        lines.append("")
        
        # User Activity
        lines.append("👤 USER ACTIVITY")
        lines.append("-" * 40)
        user_activity = report_data['user_activity']
        if isinstance(user_activity, list) and user_activity:
            for i, user in enumerate(user_activity, 1):
                dimensions = user.get('Dimensions', {})
                user_name = dimensions.get('db.user.name', 'N/A')
                load_contribution = user.get('Total', 0)
                lines.append(f"{i}. User: {user_name}")
                lines.append(f"   Load: {load_contribution:.4f}")
                lines.append("")
        elif isinstance(user_activity, dict) and 'error' in user_activity:
            lines.append(f"Error: {user_activity['error']}")
        else:
            lines.append("No user activity data available")
        
        return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive Performance Insights report')
    parser.add_argument('--db-resource-id', required=True, 
                       help='RDS resource ID or DB instance/cluster identifier')
    parser.add_argument('--region', default='us-east-1', 
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--profile', 
                       help='AWS profile to use')
    parser.add_argument('--hours', type=int, default=1, 
                       help='Number of hours to analyze (default: 1)')
    parser.add_argument('--start-time', 
                       help='Start time in ISO format (e.g., 2024-01-01T00:00:00Z)')
    parser.add_argument('--end-time', 
                       help='End time in ISO format (e.g., 2024-01-01T01:00:00Z)')
    parser.add_argument('--output-format', choices=['json', 'text'], default='json',
                       help='Output format (default: json)')
    
    args = parser.parse_args()
    
    try:
        # Initialize report generator
        generator = PerformanceReportGenerator(region=args.region, profile=args.profile)
        
        # Handle DB identifier vs resource ID
        db_resource_id = args.db_resource_id
        db_info = None
        
        if not db_resource_id.startswith('db-'):
            try:
                db_info = generator.get_db_resource_id(args.db_resource_id)
                db_resource_id = db_info['resource_id']
                print(f"Resolved DB identifier '{args.db_resource_id}' to resource ID: {db_resource_id}")
            except Exception as e:
                print(f"Error resolving DB identifier: {e}")
                sys.exit(1)
        else:
            db_info = {'resource_id': db_resource_id, 'engine': 'unknown'}
        
        # Define time range
        if args.start_time and args.end_time:
            start_time = datetime.fromisoformat(args.start_time.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(args.end_time.replace('Z', '+00:00'))
        else:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=args.hours)
        
        # Generate report
        report = generator.generate_report(db_resource_id, db_info, start_time, end_time, args.output_format)
        print("\n" + "=" * 50)
        print(report)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()