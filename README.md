# AWS Performance Insights Skill

A comprehensive OpenClaw skill for monitoring and analyzing AWS RDS and Aurora database performance using Performance Insights.

## Features

- **Performance Metrics Query**: CPU, Memory, I/O, and connection metrics
- **Top SQL Analysis**: Identify resource-intensive SQL statements
- **Wait Events Investigation**: Analyze database wait events and contention
- **Comprehensive Reports**: Generate detailed performance analysis reports

## Prerequisites

- AWS CLI v2 installed and configured
- Python 3.7 or higher
- boto3 library installed
- Valid AWS credentials with Performance Insights permissions

## Installation

1. Install Python dependencies:
```bash
pip3 install -r requirements.txt
```

2. Configure AWS credentials (choose one method):
```bash
# Method 1: AWS CLI
aws configure

# Method 2: Environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=us-east-1

# Method 3: IAM roles (for EC2/ECS/Lambda)
# No configuration needed - uses instance role
```

## Required IAM Permissions

The following IAM policy is required:

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

## Usage Examples

### Query CPU Metrics
```bash
python3 scripts/pi_metrics.py \
  --db-resource-id db-ABC123DEF456GHI789JKL \
  --metric-type cpu \
  --hours 24
```

### Analyze Top SQL Statements
```bash
python3 scripts/top_sql.py \
  --db-resource-id my-database-instance \
  --limit 10 \
  --hours 4
```

### Investigate Wait Events
```bash
python3 scripts/wait_events.py \
  --db-resource-id db-ABC123DEF456GHI789JKL \
  --hours 2 \
  --limit 15
```

### Generate Performance Report
```bash
python3 scripts/performance_report.py \
  --db-resource-id my-database-instance \
  --hours 6 \
  --output-format markdown \
  --output-file report.md
```

## Database Identification

You can use either:
- **DB Resource ID**: `db-ABC123DEF456GHI789JKL` (17-character identifier)
- **DB Instance Name**: `my-database-instance` (automatically resolved to resource ID)

## Configuration

### Environment Variables
- `AWS_REGION`: AWS region (default: us-east-1)
- `AWS_PROFILE`: AWS profile to use
- `PI_DEFAULT_PERIOD`: Default metric period in seconds (default: 300)

### Performance Insights Requirements
- Performance Insights must be enabled on your RDS/Aurora database
- Default retention period is 7 days (can be extended to 731 days)

## Script Reference

### pi_metrics.py
Query specific performance metrics (CPU, memory, I/O, connections, throughput).

**Options:**
- `--metric-type`: cpu, memory, io, connections, throughput
- `--hours`: Number of hours to query (default: 1)
- `--period`: Metric period in seconds (default: 300)
- `--output-format`: table, json

### top_sql.py
Analyze top resource-consuming SQL statements.

**Options:**
- `--limit`: Number of statements to retrieve (default: 10)
- `--hours`: Time period to analyze (default: 1)
- `--metric`: Ranking metric (default: avg_timer_wait)

### wait_events.py
Investigate database wait events and resource contention.

**Options:**
- `--limit`: Number of wait events (default: 20)
- `--start-time`: Custom start time (ISO format)
- `--end-time`: Custom end time (ISO format)

### performance_report.py
Generate comprehensive performance analysis reports.

**Options:**
- `--hours`: Analysis period (default: 4)
- `--output-format`: markdown, json
- `--output-file`: Save to file

## Troubleshooting

### Common Issues

1. **Performance Insights not enabled**
   ```bash
   aws rds modify-db-instance \
     --db-instance-identifier <name> \
     --enable-performance-insights
   ```

2. **Resource ID not found**
   ```bash
   aws rds describe-db-instances \
     --db-instance-identifier <name> \
     --query 'DBInstances[0].DbiResourceId'
   ```

3. **No data available**
   - Check if database had activity during query period
   - Verify Performance Insights was enabled during time range
   - Use shorter time periods for initial testing

See `references/troubleshooting.md` for detailed troubleshooting guide.

## Support

For issues and questions:
1. Check the troubleshooting guide in `references/`
2. Verify AWS credentials and permissions
3. Test with shorter time periods and basic queries
4. Review AWS Performance Insights documentation

## License

This skill is provided as-is for educational and operational use.