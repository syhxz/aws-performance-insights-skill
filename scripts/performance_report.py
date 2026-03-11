#!/usr/bin/env python3
"""
AWS Performance Insights Comprehensive Performance Report Generator
Generate comprehensive database performance reports
"""

import argparse
import boto3
import json
from datetime import datetime, timedelta
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
                    'instance_class': 'cluster',
                    'allocated_storage': db_cluster.get('AllocatedStorage', 'N/A')
                }
        except self.rds_client.exceptions.DBClusterNotFoundFault:
            pass
            
        raise ValueError(f"Database {db_identifier} not found")
    
    def get_engine_performance_metrics(self, engine, start_time, end_time, db_resource_id):
        """Get engine-specific performance metrics"""
        metrics = {}
        
        if 'mysql' in engine.lower():
            # MySQL/Aurora MySQL metrics
            metric_configs = {
                'cpu': [
                    {'Metric': 'db.CPU.total.pct'},
                    {'Metric': 'db.CPU.Innodb.pct'}
                ],
                'memory': [
                    {'Metric': 'db.Memory.total.pct'},
                    {'Metric': 'db.Memory.Innodb.pct'}
                ],
                'io': [
                    {'Metric': 'db.IO.total.pct'}
                ]
            }
        elif 'postgres' in engine.lower():
            # PostgreSQL/Aurora PostgreSQL metrics
            metric_configs = {
                'cpu': [
                    {'Metric': 'db.load.avg'}
                ],
                'memory': [
                    {'Metric': 'db.connections.avg'}
                ],
                'io': [
                    {'Metric': 'db.SQL.postgresql.select.calls_per_sec.avg'}
                ]
            }
        else:
            # Generic metrics
            metric_configs = {
                'cpu': [
                    {'Metric': 'db.load.avg'}
                ],
                'memory': [
                    {'Metric': 'db.connections.avg'}
                ],
                'io': [
                    {'Metric': 'db.load.avg'}
                ]
            }
        
        # Query each metric type
        for metric_type, metric_queries in metric_configs.items():
            try:
                response = self.pi_client.get_resource_metrics(
                    ServiceType='RDS',
                    Identifier=db_resource_id,
                    MetricQueries=metric_queries,
                    StartTime=start_time,
                    EndTime=end_time,
                    PeriodInSeconds=300
                )
                metrics[metric_type] = response
            except Exception as e:
                metrics[metric_type] = {'error': str(e)}
        
        return metrics
    
    def get_performance_metrics(self, db_resource_id, start_time, end_time):
        """Get comprehensive performance metrics"""
        metrics = {}
        
        # CPU Metrics
        try:
            cpu_response = self.pi_client.get_resource_metrics(
                ServiceType='RDS',
                Identifier=db_resource_id,
                MetricQueries=[
                    {'Metric': 'db.CPU.total.pct'},
                    {'Metric': 'db.CPU.Innodb.pct'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                PeriodInSeconds=300
            )
            metrics['cpu'] = cpu_response
        except Exception as e:
            metrics['cpu'] = {'error': str(e)}
        
        # Memory Metrics
        try:
            memory_response = self.pi_client.get_resource_metrics(
                ServiceType='RDS',
                Identifier=db_resource_id,
                MetricQueries=[
                    {'Metric': 'db.Memory.total.pct'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                PeriodInSeconds=300
            )
            metrics['memory'] = memory_response
        except Exception as e:
            metrics['memory'] = {'error': str(e)}
        
        # I/O Metrics
        try:
            io_response = self.pi_client.get_resource_metrics(
                ServiceType='RDS',
                Identifier=db_resource_id,
                MetricQueries=[
                    {'Metric': 'db.IO.total.pct'}
                ],
                StartTime=start_time,
                EndTime=end_time,
                PeriodInSeconds=300
            )
            metrics['io'] = io_response
        except Exception as e:
            metrics['io'] = {'error': str(e)}
        
        return metrics
    
    def get_top_sql_summary(self, db_resource_id, engine, start_time, end_time, limit=5):
        """Get summary of top SQL statements"""
        try:
            if 'mysql' in engine.lower():
                metric = 'db.SQL.Innodb.avg_timer_wait.avg'
                group_by = {'Group': 'db.sql_tokenized.id'}
            elif 'postgres' in engine.lower():
                metric = 'db.load.avg'
                group_by = {'Group': 'db.sql.id'}
            else:
                metric = 'db.load.avg'
                group_by = {'Group': 'db.sql.id'}
            
            response = self.pi_client.describe_dimension_keys(
                ServiceType='RDS',
                Identifier=db_resource_id,
                Metric=metric,
                StartTime=start_time,
                EndTime=end_time,
                GroupBy=group_by,
                MaxResults=limit
            )
            return response
        except Exception as e:
            return {'error': str(e)}
    
    def get_wait_events_summary(self, db_resource_id, engine, start_time, end_time, limit=10):
        """Get summary of top wait events"""
        try:
            if 'mysql' in engine.lower():
                metric = 'db.wait_event.name.avg_timer_wait.avg'
            elif 'postgres' in engine.lower():
                metric = 'db.load.avg'
            else:
                metric = 'db.load.avg'
            
            response = self.pi_client.describe_dimension_keys(
                ServiceType='RDS',
                Identifier=db_resource_id,
                Metric=metric,
                StartTime=start_time,
                EndTime=end_time,
                GroupBy={'Group': 'db.wait_event.name'},
                MaxResults=limit
            )
            return response
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_averages(self, metric_data):
        """Calculate average values from metric data points"""
        if 'MetricList' not in metric_data or not metric_data['MetricList']:
            return {}
            
        averages = {}
        for metric in metric_data['MetricList']:
            metric_name = metric['Key']['Metric']
            data_points = metric.get('DataPoints', [])
            
            if data_points:
                values = [point['Value'] for point in data_points if 'Value' in point]
                if values:
                    averages[metric_name] = {
                        'avg': sum(values) / len(values),
                        'max': max(values),
                        'min': min(values),
                        'samples': len(values)
                    }
            else:
                averages[metric_name] = {'avg': 0, 'max': 0, 'min': 0, 'samples': 0}
        
        return averages
    
    def generate_report(self, db_info, metrics, top_sql, wait_events, start_time, end_time, output_format='markdown'):
        """Generate comprehensive performance report"""
        if output_format == 'json':
            report_data = {
                'database_info': db_info,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                },
                'metrics': metrics,
                'top_sql': top_sql,
                'wait_events': wait_events
            }
            return json.dumps(report_data, indent=2, default=str)
        
        # Markdown format
        report = []
        report.append("# AWS Performance Insights Report")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append(f"**Time Range:** {start_time} to {end_time}")
        report.append("")
        
        # Database Information
        report.append("## Database Information")
        report.append(f"- **Resource ID:** {db_info['resource_id']}")
        report.append(f"- **Engine:** {db_info['engine']}")
        report.append(f"- **Instance Class:** {db_info['instance_class']}")
        report.append(f"- **Allocated Storage:** {db_info['allocated_storage']}")
        report.append("")
        
        # Performance Metrics Summary
        report.append("## Performance Metrics Summary")
        
        for metric_type, metric_data in metrics.items():
            if 'error' in metric_data:
                report.append(f"### {metric_type.upper()}")
                report.append(f"Error retrieving {metric_type} metrics: {metric_data['error']}")
                report.append("")
                continue
                
            averages = self.calculate_averages(metric_data)
            if averages:
                report.append(f"### {metric_type.upper()}")
                for metric_name, stats in averages.items():
                    report.append(f"- **{metric_name}:**")
                    report.append(f"  - Average: {stats['avg']:.2f}%")
                    report.append(f"  - Maximum: {stats['max']:.2f}%")
                    report.append(f"  - Minimum: {stats['min']:.2f}%")
                    report.append(f"  - Samples: {stats['samples']}")
                report.append("")
        
        # Top SQL Statements
        report.append("## Top SQL Statements")
        if 'error' in top_sql:
            report.append(f"Error retrieving top SQL statements: {top_sql['error']}")
        elif 'Keys' in top_sql and top_sql['Keys']:
            for i, key in enumerate(top_sql['Keys'], 1):
                sql_id = key.get('Dimensions', {}).get('db.sql_tokenized.id', 'Unknown')
                total = key.get('Total', 0)
                report.append(f"{i}. **SQL ID:** {sql_id}")
                report.append(f"   **Total Resource Consumption:** {total:.2f}")
        else:
            report.append("No SQL statements data available")
        report.append("")
        
        # Top Wait Events
        report.append("## Top Wait Events")
        if 'error' in wait_events:
            report.append(f"Error retrieving wait events: {wait_events['error']}")
        elif 'Keys' in wait_events and wait_events['Keys']:
            for i, key in enumerate(wait_events['Keys'], 1):
                wait_event = key.get('Dimensions', {}).get('db.wait_event.name', 'Unknown')
                total = key.get('Total', 0)
                report.append(f"{i}. **Wait Event:** {wait_event}")
                report.append(f"   **Total Wait Time:** {total:.2f}")
        else:
            report.append("No wait events data available")
        report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        recommendations = self.generate_recommendations(metrics, top_sql, wait_events)
        for rec in recommendations:
            report.append(f"- {rec}")
        
        return '\n'.join(report)
    
    def generate_recommendations(self, metrics, top_sql, wait_events):
        """Generate performance recommendations based on analysis"""
        recommendations = []
        
        # CPU recommendations
        if 'cpu' in metrics and 'MetricList' in metrics['cpu']:
            cpu_averages = self.calculate_averages(metrics['cpu'])
            for metric_name, stats in cpu_averages.items():
                if stats['avg'] > 80:
                    recommendations.append(f"High CPU utilization detected ({stats['avg']:.1f}%). Consider optimizing SQL queries or scaling up instance.")
                elif stats['avg'] > 60:
                    recommendations.append(f"Moderate CPU utilization ({stats['avg']:.1f}%). Monitor during peak hours.")
        
        # Memory recommendations
        if 'memory' in metrics and 'MetricList' in metrics['memory']:
            memory_averages = self.calculate_averages(metrics['memory'])
            for metric_name, stats in memory_averages.items():
                if stats['avg'] > 90:
                    recommendations.append(f"High memory utilization ({stats['avg']:.1f}%). Consider increasing instance memory.")
        
        # I/O recommendations
        if 'io' in metrics and 'MetricList' in metrics['io']:
            io_averages = self.calculate_averages(metrics['io'])
            for metric_name, stats in io_averages.items():
                if stats['avg'] > 70:
                    recommendations.append(f"High I/O utilization ({stats['avg']:.1f}%). Consider using faster storage or optimizing queries.")
        
        # SQL recommendations
        if 'Keys' in top_sql and len(top_sql['Keys']) > 0:
            recommendations.append(f"Found {len(top_sql['Keys'])} resource-intensive SQL statements. Review and optimize top queries.")
        
        # Wait events recommendations
        if 'Keys' in wait_events and len(wait_events['Keys']) > 0:
            recommendations.append(f"Detected {len(wait_events['Keys'])} significant wait events. Investigate lock contention and I/O bottlenecks.")
        
        if not recommendations:
            recommendations.append("Performance metrics appear normal. Continue monitoring for trends.")
        
        return recommendations

def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive Performance Insights report')
    parser.add_argument('--db-resource-id', required=True, help='RDS resource ID or DB identifier')
    parser.add_argument('--hours', type=int, default=4, help='Number of hours to analyze (default: 4)')
    parser.add_argument('--start-time', help='Start time in ISO format (e.g., 2024-01-01T00:00:00Z)')
    parser.add_argument('--end-time', help='End time in ISO format (e.g., 2024-01-01T01:00:00Z)')
    parser.add_argument('--region', default=os.getenv('AWS_REGION', 'us-east-1'), help='AWS region')
    parser.add_argument('--profile', default=os.getenv('AWS_PROFILE'), help='AWS profile')
    parser.add_argument('--output-format', default='markdown', choices=['markdown', 'json'], 
                       help='Output format')
    parser.add_argument('--output-file', help='Save report to file')
    
    args = parser.parse_args()
    
    # Initialize report generator
    generator = PerformanceReportGenerator(region=args.region, profile=args.profile)
    
    # Handle DB identifier vs resource ID
    db_identifier = args.db_resource_id
    try:
        if db_identifier.startswith('db-'):
            # Already a resource ID, get minimal DB info
            db_info = {'resource_id': db_identifier, 'engine': 'unknown', 'instance_class': 'unknown', 'allocated_storage': 'unknown'}
        else:
            # DB identifier, resolve to resource ID and get full info
            db_info = generator.get_db_resource_id(db_identifier)
            print(f"Resolved DB identifier '{db_identifier}' to resource ID: {db_info['resource_id']}")
    except Exception as e:
        print(f"Error resolving DB identifier: {e}")
        sys.exit(1)
    
    # Define time range
    if args.start_time and args.end_time:
        start_time = datetime.fromisoformat(args.start_time.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(args.end_time.replace('Z', '+00:00'))
    else:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=args.hours)
    
    print(f"Generating performance report for {db_info['resource_id']}")
    print(f"Time range: {start_time} to {end_time}")
    
        # Replace old get_performance_metrics call
        metrics = generator.get_engine_performance_metrics(
            engine=db_info.get('engine', 'unknown'),
            start_time=start_time, 
            end_time=end_time,
            db_resource_id=db_info['resource_id']
        )
    
    print("Collecting top SQL statements...")
    top_sql = generator.get_top_sql_summary(
        db_info['resource_id'], 
        db_info.get('engine', 'unknown'),
        start_time, 
        end_time
    )
    
    print("Collecting wait events...")
    wait_events = generator.get_wait_events_summary(
        db_info['resource_id'],
        db_info.get('engine', 'unknown'), 
        start_time, 
        end_time
    )
    
    # Generate report
    print("Generating report...")
    report = generator.generate_report(db_info, metrics, top_sql, wait_events, start_time, end_time, args.output_format)
    
    # Output report
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output_file}")
    else:
        print("\n" + "="*50)
        print(report)

if __name__ == '__main__':
    main()