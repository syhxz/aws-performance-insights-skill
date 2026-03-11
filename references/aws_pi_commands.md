# AWS Performance Insights CLI Commands Reference

## Core Commands

### Get Resource Metrics
```bash
aws pi get-resource-metrics \
  --service-type RDS \
  --identifier <db-resource-id> \
  --metric-queries '[{"Metric":"db.CPU.total.pct"}]' \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T01:00:00Z" \
  --period-in-seconds 300
```

### Describe Dimension Keys (Top SQL)
```bash
aws pi describe-dimension-keys \
  --service-type RDS \
  --identifier <db-resource-id> \
  --metric "db.SQL.Innodb.avg_timer_wait.avg" \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T01:00:00Z" \
  --group-by "db.sql_tokenized.id" \
  --max-results 10
```

### Get Dimension Key Details
```bash
aws pi get-dimension-key-details \
  --service-type RDS \
  --identifier <db-resource-id> \
  --group "db.sql_tokenized.id" \
  --group-identifier "<sql-id>" \
  --requested-dimensions '["db.sql_tokenized.statement"]'
```

## Common Metric Queries

### CPU Metrics
- `db.CPU.total.pct` - Total CPU utilization percentage
- `db.CPU.Innodb.pct` - InnoDB CPU utilization percentage
- `db.CPU.user.pct` - User CPU utilization percentage

### Memory Metrics
- `db.Memory.total.pct` - Total memory utilization percentage
- `db.Memory.Innodb.pct` - InnoDB memory utilization percentage

### I/O Metrics
- `db.IO.total.pct` - Total I/O utilization percentage
- `db.IO.read.pct` - Read I/O utilization percentage
- `db.IO.write.pct` - Write I/O utilization percentage

### Connection Metrics
- `db.Connections.Avg` - Average number of connections
- `db.Connections.Max` - Maximum connections

### Transaction Metrics
- `db.Transactions.Avg` - Average transactions per second
- `db.Transactions.total` - Total transactions

## Dimension Groups

### SQL Statements
- `db.sql_tokenized.id` - Normalized SQL statement ID
- `db.sql.id` - Raw SQL statement ID

### Wait Events
- `db.wait_event.name` - Wait event name
- `db.wait_event.type` - Wait event type category

### Users and Databases
- `db.User.name` - Database user
- `db.Database.name` - Database name

## Time Periods

### Common Periods (seconds)
- `60` - 1 minute
- `300` - 5 minutes (default)
- `3600` - 1 hour
- `86400` - 1 day

### Time Format
- Use ISO 8601 format: `2024-01-01T00:00:00Z`
- UTC timezone recommended

## Resource Identification

### Get Resource ID from Instance Name
```bash
aws rds describe-db-instances \
  --db-instance-identifier <instance-name> \
  --query 'DBInstances[0].DbiResourceId'
```

### Get Resource ID from Cluster Name
```bash
aws rds describe-db-clusters \
  --db-cluster-identifier <cluster-name> \
  --query 'DBClusters[0].DbClusterResourceId'
```

## Output Formats

### JSON Output
```bash
aws pi get-resource-metrics ... --output json
```

### Table Output
```bash
aws pi get-resource-metrics ... --output table
```

### Text Output
```bash
aws pi get-resource-metrics ... --output text
```

## Advanced Queries

### Query with Filters
```bash
aws pi describe-dimension-keys \
  --service-type RDS \
  --identifier <db-resource-id> \
  --metric "db.SQL.Innodb.avg_timer_wait.avg" \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T01:00:00Z" \
  --group-by "db.User.name" \
  --filter '{"db.Database.name":{"Equals":"production"}}'
```

### Multiple Metrics Query
```bash
aws pi get-resource-metrics \
  --service-type RDS \
  --identifier <db-resource-id> \
  --metric-queries '[
    {"Metric":"db.CPU.total.pct"},
    {"Metric":"db.Memory.total.pct"},
    {"Metric":"db.IO.total.pct"}
  ]' \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-01T01:00:00Z"
```

## Error Handling

### Common Error Codes
- `InvalidParameterValue` - Invalid parameter values
- `ResourceNotFound` - Database resource not found
- `AccessDenied` - Insufficient permissions
- `ThrottlingException` - Rate limit exceeded

### Troubleshooting Tips
1. Verify Performance Insights is enabled on the database
2. Check IAM permissions for Performance Insights actions
3. Ensure the database resource ID is correct
4. Verify the time range is valid (not too far in the past)
5. Check AWS region configuration

## IAM Permissions Required

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