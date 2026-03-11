# AWS Performance Insights Skill

A comprehensive OpenClaw skill for monitoring and analyzing AWS RDS and Aurora database performance using Performance Insights.

## Features

- **Multi-Engine Support**: Supports both MySQL/Aurora MySQL and PostgreSQL/Aurora PostgreSQL
- **Performance Metrics Query**: CPU, Memory, I/O, and connection metrics
- **Top SQL Analysis**: Identify resource-intensive SQL statements (MySQL/Aurora MySQL)
- **Wait Events Investigation**: Analyze database wait events and contention (MySQL/Aurora MySQL)
- **Comprehensive Reports**: Generate detailed performance analysis reports
- **Auto-Detection**: Automatically detects database engine and uses appropriate metrics

## Prerequisites

- AWS CLI v2 installed and configured
- Python 3.7 or higher
- boto3 library installed (usually pre-installed on AWS instances)
- Valid AWS credentials with Performance Insights permissions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/syhxz/aws-performance-insights-skill.git
cd aws-performance-insights-skill
```

2. Install Python dependencies (if needed):
```bash
pip3 install -r requirements.txt
```

3. Configure AWS credentials (choose one method):
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

### Query Performance Metrics
```bash
# CPU/Load metrics (works for all engines)
python3 scripts/pi_metrics.py \
  --db-resource-id my-database-instance \
  --metric-type cpu \
  --hours 24

# PostgreSQL query activity
python3 scripts/pi_metrics.py \
  --db-resource-id my-postgres-instance \
  --metric-type io \
  --hours 4

# Connection metrics
python3 scripts/pi_metrics.py \
  --db-resource-id my-database \
  --metric-type connections \
  --hours 2
```

### Analyze Top SQL Statements (MySQL/Aurora MySQL)
```bash
python3 scripts/top_sql.py \
  --db-resource-id my-mysql-instance \
  --limit 10 \
  --hours 4
```

### Investigate Wait Events (MySQL/Aurora MySQL)
```bash
python3 scripts/wait_events.py \
  --db-resource-id my-mysql-instance \
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

The skill automatically detects the database engine and uses appropriate metrics.

## Engine-Specific Features

### MySQL/Aurora MySQL
- ✅ CPU utilization metrics (db.CPU.total.pct, db.CPU.Innodb.pct)
- ✅ Memory metrics (db.Memory.total.pct, db.Memory.Innodb.pct)
- ✅ I/O metrics (db.IO.total.pct)
- ✅ Top SQL analysis (db.SQL.Innodb.avg_timer_wait.avg)
- ✅ Wait events analysis (db.wait_event.name.avg_timer_wait.avg)

### PostgreSQL/Aurora PostgreSQL
- ✅ Database load metrics (db.load.avg)
- ✅ PostgreSQL query metrics (db.SQL.postgresql.*.calls_per_sec.avg)
- ✅ Connection metrics (db.connections.avg)
- ⚠️ Top SQL analysis (limited - requires sufficient database activity)
- ⚠️ Wait events analysis (limited - requires sufficient database activity)

## Configuration

### Environment Variables
- `AWS_REGION`: AWS region (default: us-east-1)
- `AWS_PROFILE`: AWS profile to use
- `PI_DEFAULT_PERIOD`: Default metric period in seconds (default: 300)

### Performance Insights Requirements
- Performance Insights must be enabled on your RDS/Aurora database
- Default retention period is 7 days (can be extended to 731 days)
- For detailed SQL and wait event analysis, the database needs active workload

## Script Reference

### pi_metrics.py
Query specific performance metrics with automatic engine detection.

**Options:**
- `--metric-type`: cpu, memory, io, connections, throughput
- `--hours`: Number of hours to query (default: 1)
- `--period`: Metric period in seconds (default: 300)
- `--output-format`: table, json

**Engine Behavior:**
- **MySQL**: Uses engine-specific CPU, Memory, I/O metrics
- **PostgreSQL**: Uses database load and query activity metrics

### top_sql.py
Analyze top resource-consuming SQL statements.

**Compatibility:**
- ✅ **MySQL/Aurora MySQL**: Full SQL statement analysis
- ⚠️ **PostgreSQL/Aurora PostgreSQL**: Limited (requires active workload)

**Options:**
- `--limit`: Number of statements to retrieve (default: 10)
- `--hours`: Time period to analyze (default: 1)

### wait_events.py
Investigate database wait events and resource contention.

**Compatibility:**
- ✅ **MySQL/Aurora MySQL**: Detailed wait event analysis
- ⚠️ **PostgreSQL/Aurora PostgreSQL**: Limited (requires active workload)

**Options:**
- `--limit`: Number of wait events (default: 20)
- `--start-time`: Custom start time (ISO format)
- `--end-time`: Custom end time (ISO format)

### performance_report.py
Generate comprehensive performance analysis reports with engine detection.

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

3. **No SQL/Wait Events data (PostgreSQL)**
   - This is normal for low-activity databases
   - Wait events and SQL analysis require active database workload
   - Focus on load metrics (`db.load.avg`) and query activity metrics

4. **"Unknown group" errors**
   - Some dimension groups require active database workload
   - MySQL engines generally have better Performance Insights support
   - Use basic metrics for low-activity databases

### PostgreSQL-Specific Notes

- **Limited dimension support**: PostgreSQL Aurora may not provide detailed SQL statement or wait event breakdowns for low-activity databases
- **Focus on load metrics**: Use `db.load.avg` as the primary performance indicator
- **Query activity**: Monitor PostgreSQL-specific query metrics for activity patterns
- **Connections**: Use `db.connections.avg` to monitor connection patterns

See `references/troubleshooting.md` for detailed troubleshooting guide.

## Version History

### v1.1.0 (Latest)
- ✅ Added multi-engine support (MySQL + PostgreSQL)
- ✅ Automatic engine detection and metric selection
- ✅ Enhanced error handling for limited data scenarios
- ✅ Improved PostgreSQL Aurora compatibility

### v1.0.0
- Initial release with basic Performance Insights functionality

## Support

For issues and questions:
1. Check the troubleshooting guide in `references/`
2. Verify AWS credentials and permissions
3. Test with shorter time periods and basic queries
4. Review AWS Performance Insights documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test with both MySQL and PostgreSQL instances
4. Submit a pull request

## License

This skill is provided as-is for educational and operational use.