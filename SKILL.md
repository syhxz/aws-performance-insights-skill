---
name: aws-performance-insights
description: AWS Performance Insights database monitoring and analysis. Query RDS/Aurora Performance Insights metrics, analyze database performance, identify top SQL statements, wait events, and resource bottlenecks. Use when analyzing database performance issues, slow queries, monitoring database metrics, or investigating RDS/Aurora Performance Insights data.
---

# AWS Performance Insights Skill

Comprehensive AWS Performance Insights monitoring and analysis for RDS and Aurora databases.

## Capabilities

### 1. Performance Metrics Query
- CPU, Memory, and I/O utilization metrics
- Database load and throughput analysis
- Historical performance data retrieval
- Real-time performance monitoring

### 2. Top SQL Analysis
- Identify top resource-consuming SQL statements
- Query execution statistics and patterns
- SQL digest and normalization analysis
- Performance comparison across time ranges

### 3. Wait Events Investigation
- Database wait event analysis
- Lock contention identification
- I/O bottleneck detection
- Resource contention monitoring

### 4. Resource Utilization Reports
- Database connection analysis
- Buffer cache efficiency metrics
- Disk I/O patterns and statistics
- Memory usage optimization insights

## Usage

### Query Performance Metrics
```bash
python scripts/pi_metrics.py --db-resource-id <db-resource-id> --metric-type cpu --hours 24
```

### Analyze Top SQL Statements
```bash
python scripts/top_sql.py --db-resource-id <db-resource-id> --limit 10 --period 3600
```

### Investigate Wait Events
```bash
python scripts/wait_events.py --db-resource-id <db-resource-id> --start-time "2024-01-01T00:00:00Z"
```

### Generate Performance Report
```bash
python scripts/performance_report.py --db-resource-id <db-resource-id> --output-format json
```

## Configuration

### Environment Variables
- `AWS_REGION`: AWS region (default: us-east-1)
- `AWS_PROFILE`: AWS profile to use (optional)
- `PI_DEFAULT_PERIOD`: Default metric period in seconds (default: 300)

### Authentication
Uses standard AWS credential chain:
1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
2. AWS profile credentials
3. IAM roles (EC2/ECS/Lambda)
4. AWS SSO

### Required IAM Permissions
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "pi:GetResourceMetrics",
                "pi:DescribeDimensionKeys",
                "pi:GetDimensionKeyDetails",
                "rds:DescribeDBInstances",
                "rds:DescribeDBClusters"
            ],
            "Resource": "*"
        }
    ]
}
```

## References

- **AWS CLI Commands**: See [references/aws_pi_commands.md](references/aws_pi_commands.md)
- **Metric Definitions**: See [references/pi_metrics_reference.md](references/pi_metrics_reference.md)
- **Troubleshooting Guide**: See [references/troubleshooting.md](references/troubleshooting.md)

## Requirements

- AWS CLI v2
- Python 3.7+
- boto3 library
- Valid AWS credentials with Performance Insights access