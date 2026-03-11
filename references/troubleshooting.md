# AWS Performance Insights Troubleshooting Guide

## Common Issues and Solutions

### 1. Performance Insights Not Enabled

**Error**: `InvalidParameterValue: Performance Insights is not enabled for this resource`

**Cause**: Performance Insights feature is not enabled on the database instance or cluster.

**Solution**:
```bash
# Enable Performance Insights on existing RDS instance
aws rds modify-db-instance \
  --db-instance-identifier <instance-name> \
  --enable-performance-insights \
  --performance-insights-retention-period 7

# Enable Performance Insights on Aurora cluster  
aws rds modify-db-cluster \
  --db-cluster-identifier <cluster-name> \
  --enable-performance-insights \
  --performance-insights-retention-period 7
```

**Prevention**: Always enable Performance Insights when creating new database instances.

### 2. Insufficient IAM Permissions

**Error**: `AccessDenied: User is not authorized to perform: pi:GetResourceMetrics`

**Cause**: The IAM user/role lacks necessary Performance Insights permissions.

**Solution**: Attach the following policy:
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

### 3. Invalid Resource ID

**Error**: `ResourceNotFound: Resource db-XXXXXX does not exist`

**Causes**:
- Incorrect resource ID format
- Database instance doesn't exist
- Wrong AWS region

**Solutions**:
```bash
# Get correct resource ID from instance name
aws rds describe-db-instances \
  --db-instance-identifier <instance-name> \
  --query 'DBInstances[0].DbiResourceId' \
  --output text

# Get correct resource ID from cluster name
aws rds describe-db-clusters \
  --db-cluster-identifier <cluster-name> \
  --query 'DBClusters[0].DbClusterResourceId' \
  --output text

# List all RDS instances in current region
aws rds describe-db-instances \
  --query 'DBInstances[*].[DBInstanceIdentifier,DbiResourceId]' \
  --output table
```

### 4. Time Range Issues

**Error**: `InvalidParameterValue: Start time cannot be more than 7 days ago`

**Cause**: Querying data outside the retention period or invalid time format.

**Solutions**:
- Check Performance Insights retention period (default 7 days, max 731 days)
- Use correct ISO 8601 time format: `2024-01-01T00:00:00Z`
- Ensure start time is before end time
- Query within the retention period

```bash
# Check retention period
aws rds describe-db-instances \
  --db-instance-identifier <instance-name> \
  --query 'DBInstances[0].PerformanceInsightsRetentionPeriod'
```

### 5. No Data Available

**Error**: `MetricList` is empty or contains no data points

**Causes**:
- Database had no activity during query period
- Metric doesn't apply to the database engine
- Performance Insights wasn't enabled during the time period

**Solutions**:
1. **Check database activity**:
   ```bash
   # Query connection metrics to verify activity
   python3 scripts/pi_metrics.py \
     --db-resource-id <resource-id> \
     --metric-type connections \
     --hours 1
   ```

2. **Verify metric compatibility**:
   - Some metrics are engine-specific (e.g., `db.Innodb.*` only for MySQL)
   - Check engine type: `aws rds describe-db-instances --db-instance-identifier <name> --query 'DBInstances[0].Engine'`

3. **Use different time range**:
   ```bash
   # Try recent time period
   python3 scripts/pi_metrics.py \
     --db-resource-id <resource-id> \
     --metric-type cpu \
     --hours 1
   ```

### 6. Rate Limiting

**Error**: `ThrottlingException: Rate exceeded`

**Cause**: Making too many API calls in short time period.

**Solutions**:
- Implement exponential backoff in scripts
- Reduce query frequency
- Use longer time periods with fewer data points
- Cache results when possible

```python
import time
import random

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
            raise
    raise Exception("Max retries exceeded")
```

### 7. Large Query Timeouts

**Error**: Request times out or takes very long

**Causes**:
- Querying large time ranges
- Requesting too many dimensions
- Complex grouping operations

**Solutions**:
1. **Reduce time range**:
   ```bash
   # Instead of 24 hours, try 1-4 hours
   python3 scripts/performance_report.py \
     --db-resource-id <resource-id> \
     --hours 2
   ```

2. **Limit results**:
   ```bash
   # Limit top SQL results
   python3 scripts/top_sql.py \
     --db-resource-id <resource-id> \
     --limit 5
   ```

3. **Use appropriate periods**:
   ```bash
   # Use longer periods for large time ranges
   python3 scripts/pi_metrics.py \
     --db-resource-id <resource-id> \
     --hours 24 \
     --period 3600  # 1 hour periods instead of 5 minutes
   ```

### 8. Authentication Issues

**Error**: Various credential-related errors

**Common Scenarios**:

1. **No credentials configured**:
   ```bash
   # Configure AWS credentials
   aws configure
   # OR set environment variables
   export AWS_ACCESS_KEY_ID=your-key
   export AWS_SECRET_ACCESS_KEY=your-secret
   export AWS_REGION=us-east-1
   ```

2. **Wrong profile**:
   ```bash
   # List available profiles
   aws configure list-profiles
   
   # Use specific profile
   python3 scripts/pi_metrics.py \
     --db-resource-id <resource-id> \
     --profile <profile-name>
   ```

3. **Cross-account access**:
   ```bash
   # Assume role for cross-account access
   aws sts assume-role \
     --role-arn arn:aws:iam::ACCOUNT:role/ROLE \
     --role-session-name pi-session
   ```

### 9. Engine-Specific Issues

#### MySQL/Aurora MySQL
- **Issue**: InnoDB metrics not available
- **Solution**: Verify InnoDB is the storage engine
  ```sql
  SHOW ENGINES;
  SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA='your_db';
  ```

#### PostgreSQL/Aurora PostgreSQL
- **Issue**: MySQL-specific metrics queried
- **Solution**: Use PostgreSQL-compatible metrics
  ```bash
  # Use generic metrics for PostgreSQL
  python3 scripts/pi_metrics.py \
    --db-resource-id <resource-id> \
    --metric-type cpu  # Avoid Innodb-specific metrics
  ```

### 10. Script Execution Issues

#### Python Dependencies
```bash
# Install required packages
pip3 install boto3 argparse datetime

# Check Python version (requires 3.7+)
python3 --version
```

#### Permission Errors
```bash
# Make scripts executable
chmod +x scripts/*.py

# Check file permissions
ls -la scripts/
```

#### Import Errors
```python
# Add error handling for missing modules
try:
    import boto3
except ImportError:
    print("boto3 not installed. Run: pip3 install boto3")
    sys.exit(1)
```

## Debugging Steps

### 1. Verify Setup
```bash
# Check AWS CLI configuration
aws sts get-caller-identity

# Test basic RDS access
aws rds describe-db-instances --max-items 1

# Verify Performance Insights is enabled
aws rds describe-db-instances \
  --db-instance-identifier <instance-name> \
  --query 'DBInstances[0].PerformanceInsightsEnabled'
```

### 2. Test Basic Query
```bash
# Simple CPU metrics query
aws pi get-resource-metrics \
  --service-type RDS \
  --identifier <db-resource-id> \
  --metric-queries '[{"Metric":"db.CPU.total.pct"}]' \
  --start-time "$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period-in-seconds 300
```

### 3. Enable Detailed Logging
```python
import logging
import boto3

# Enable boto3 debug logging
boto3.set_stream_logger('boto3', logging.DEBUG)
```

### 4. Validate Time Ranges
```bash
# Generate valid ISO timestamps
python3 -c "
from datetime import datetime, timedelta
end = datetime.utcnow()
start = end - timedelta(hours=1)
print(f'Start: {start.isoformat()}Z')
print(f'End: {end.isoformat()}Z')
"
```

## Performance Optimization Tips

### 1. Efficient Querying
- Use appropriate time periods (300s for detailed, 3600s for overview)
- Limit the number of dimensions and metrics per query
- Cache frequently accessed data locally

### 2. Batch Operations
- Group related metrics in single API calls
- Use pagination for large result sets
- Implement connection pooling for multiple queries

### 3. Error Recovery
- Implement retry logic with exponential backoff
- Handle partial failures gracefully
- Log errors for debugging

### 4. Resource Management
- Close database connections properly
- Use context managers for file operations
- Monitor script memory usage for large datasets

## Getting Help

### AWS Support Resources
- AWS Performance Insights Documentation
- AWS CLI Command Reference
- boto3 Documentation

### Community Resources
- AWS Forums
- Stack Overflow (tag: aws-performance-insights)
- AWS GitHub repositories

### Monitoring and Alerting
- Set up CloudWatch alarms for critical metrics
- Use AWS Systems Manager for automated responses
- Implement custom monitoring dashboards