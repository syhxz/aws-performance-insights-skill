---
name: aws-performance-insights
description: AWS Performance Insights database monitoring and analysis with multi-engine support. Query RDS/Aurora Performance Insights metrics for both MySQL and PostgreSQL, analyze database performance, identify top SQL statements (MySQL), wait events (MySQL), and resource bottlenecks. Automatically detects database engine and uses appropriate metrics. Use when analyzing database performance issues, slow queries, monitoring database metrics, or investigating RDS/Aurora Performance Insights data for MySQL or PostgreSQL engines.
---

# AWS Performance Insights Skill

Comprehensive AWS Performance Insights monitoring and analysis for RDS and Aurora databases with multi-engine support.

## Capabilities

### 1. Multi-Engine Performance Metrics
- **MySQL/Aurora MySQL**: CPU, Memory, I/O utilization metrics
- **PostgreSQL/Aurora PostgreSQL**: Database load and query activity metrics
- **Auto-Detection**: Automatically detects database engine and uses appropriate metrics
- Historical performance data retrieval and real-time monitoring

### 2. Top SQL Analysis (MySQL/Aurora MySQL)
- Identify top resource-consuming SQL statements
- Query execution statistics and patterns
- SQL digest and normalization analysis
- Performance comparison across time ranges

### 3. Wait Events Investigation (MySQL/Aurora MySQL)
- Database wait event analysis
- Lock contention identification
- I/O bottleneck detection
- Resource contention monitoring

### 4. PostgreSQL-Specific Monitoring
- Database load analysis (`db.load.avg`)
- PostgreSQL query activity metrics (SELECT, INSERT, UPDATE, DELETE)
- Connection pattern analysis
- Query calls per second tracking

### 5. Resource Utilization Reports
- Engine-specific performance metrics
- Multi-database comparative analysis
- Automated report generation
- Performance trend identification

## Usage

### Query Performance Metrics
```bash
python3 scripts/pi_metrics.py --db-resource-id <db-resource-id> --metric-type load --hours 24
```

### Analyze Top SQL Statements (🔧 FIXED)
```bash
# Get Top SQL with load percentages
python3 scripts/top_sql.py --db-resource-id <db-resource-id> --hours 2 --limit 10

# JSON output for programmatic use
python3 scripts/top_sql.py --db-resource-id <db-resource-id> --hours 1 --output-format json
```

### Generate Performance Report (🔧 FIXED)
```bash
# Text report
python3 scripts/performance_report.py --db-resource-id <db-resource-id> --hours 4 --output-format text

# JSON report
python3 scripts/performance_report.py --db-resource-id <db-resource-id> --output-format json
```

### Query Specific Metrics
```bash
# Database load metrics
python3 scripts/pi_metrics.py --db-resource-id <db-resource-id> --metric-type load --hours 1

# CPU metrics
python3 scripts/pi_metrics.py --db-resource-id <db-resource-id> --metric-type cpu --hours 2

# Memory metrics  
python3 scripts/pi_metrics.py --db-resource-id <db-resource-id> --metric-type memory --hours 1
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