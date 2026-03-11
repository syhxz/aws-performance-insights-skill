#!/usr/bin/env python3
"""
AWS Performance Insights Wait Events Analysis Script
Analyze database wait events and resource contention
"""

import argparse
import boto3
import json
from datetime import datetime, timedelta
import sys
import os

class WaitEventsAnalyzer:
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
    
    def get_engine_wait_metrics(self, engine):
        """Get engine-specific wait event metrics"""
        if 'mysql' in engine.lower():
            return {
                'metric': 'db.wait_event.name.avg_timer_wait.avg',
                'group_by': {'Group': 'db.wait_event.name'}
            }
        elif 'postgres' in engine.lower():
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
    
    def get_wait_events(self, db_resource_id, engine, start_time, end_time, limit=20):
        """Get top wait events by resource consumption"""
        try:
            # Get engine-specific wait event metrics
            wait_config = self.get_engine_wait_metrics(engine)
            
            # Query dimension keys for wait events
            response = self.pi_client.describe_dimension_keys(
                ServiceType='RDS',
                Identifier=db_resource_id,
                Metric=wait_config['metric'],
                StartTime=start_time,
                EndTime=end_time,
                GroupBy=wait_config['group_by'],
                MaxResults=limit
            )
            return response
        except Exception as e:
            print(f"Error querying wait events: {str(e)}")
            return None
    
    def get_wait_event_details(self, db_resource_id, wait_event_names):
        """Get detailed information for specific wait events"""
        try:
            if not wait_event_names:
                return None
                
            response = self.pi_client.get_dimension_key_details(
                ServiceType='RDS',
                Identifier=db_resource_id,
                Group='db.wait_event.name',
                GroupIdentifier=wait_event_names[0],
                RequestedDimensions=['db.wait_event.type']
            )
            return response
        except Exception as e:
            print(f"Error getting wait event details: {str(e)}")
            return None
    
    def categorize_wait_event(self, wait_event_name):
        """Categorize wait events by type"""
        if not wait_event_name:
            return "Unknown"
            
        wait_event_name = wait_event_name.lower()
        
        if 'lock' in wait_event_name or 'latch' in wait_event_name:
            return "Lock/Latch Contention"
        elif 'io' in wait_event_name or 'read' in wait_event_name or 'write' in wait_event_name:
            return "I/O Operations"
        elif 'cpu' in wait_event_name or 'active' in wait_event_name:
            return "CPU/Processing"
        elif 'network' in wait_event_name or 'socket' in wait_event_name:
            return "Network"
        elif 'log' in wait_event_name or 'redo' in wait_event_name:
            return "Transaction Log"
        else:
            return "Other"
    
    def format_wait_events_results(self, response, output_format='table'):
        """Format wait events analysis results"""
        if not response or 'Keys' not in response:
            return "No wait events data available"
            
        if output_format == 'json':
            return json.dumps(response, indent=2, default=str)
            
        # Table format
        results = []
        results.append("=== TOP WAIT EVENTS ===\n")
        
        # Group by category
        categories = {}
        
        for i, key in enumerate(response['Keys'], 1):
            wait_event_name = key.get('Dimensions', {}).get('db.wait_event.name', 'Unknown')
            total = key.get('Total', 0)
            category = self.categorize_wait_event(wait_event_name)
            
            if category not in categories:
                categories[category] = []
                
            categories[category].append({
                'rank': i,
                'name': wait_event_name,
                'total': total,
                'partitions': key.get('Partitions', [])
            })
        
        # Display results by category
        for category, events in categories.items():
            results.append(f"## {category.upper()} ##")
            
            for event in events:
                results.append(f"{event['rank']}. {event['name']}")
                results.append(f"   Total Wait Time: {event['total']:.2f}")
                
                if event['partitions']:
                    results.append("   Time-based breakdown:")
                    for partition in event['partitions']:
                        timestamp = partition.get('Keys', [{}])[0].get('Timestamp', 'Unknown')
                        value = partition.get('Keys', [{}])[0].get('Value', 0)
                        results.append(f"     {timestamp}: {value:.2f}")
                
                results.append("")  # Empty line between events
            
            results.append("")  # Empty line between categories
                
        return '\n'.join(results)

def main():
    parser = argparse.ArgumentParser(description='Analyze wait events in Performance Insights')
    parser.add_argument('--db-resource-id', required=True, help='RDS resource ID or DB identifier')
    parser.add_argument('--limit', type=int, default=20, help='Number of top wait events to retrieve (default: 20)')
    parser.add_argument('--hours', type=int, default=1, help='Number of hours to analyze (default: 1)')
    parser.add_argument('--start-time', help='Start time in ISO format (e.g., 2024-01-01T00:00:00Z)')
    parser.add_argument('--end-time', help='End time in ISO format (e.g., 2024-01-01T01:00:00Z)')
    parser.add_argument('--region', default=os.getenv('AWS_REGION', 'us-east-1'), help='AWS region')
    parser.add_argument('--profile', default=os.getenv('AWS_PROFILE'), help='AWS profile')
    parser.add_argument('--output-format', default='table', choices=['table', 'json'], 
                       help='Output format')
    parser.add_argument('--metric', default='db.wait_event.name.avg_timer_wait.avg',
                       help='Metric to use for ranking wait events')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = WaitEventsAnalyzer(region=args.region, profile=args.profile)
    
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
        print("Warning: Engine type unknown, using generic wait event analysis")
    
    # Define time range
    if args.start_time and args.end_time:
        start_time = datetime.fromisoformat(args.start_time.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(args.end_time.replace('Z', '+00:00'))
    else:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=args.hours)
    
    print(f"Analyzing top {args.limit} wait events for {db_resource_id}")
    print(f"Time range: {start_time} to {end_time}")
    
    # Get wait events
    response = analyzer.get_wait_events(
        db_resource_id=db_resource_id,
        engine=engine,
        start_time=start_time,
        end_time=end_time,
        limit=args.limit
    )
    
    if response:
        formatted_results = analyzer.format_wait_events_results(response, args.output_format)
        print(formatted_results)
    else:
        print("Failed to retrieve wait events")
        sys.exit(1)

if __name__ == '__main__':
    main()