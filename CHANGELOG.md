# AWS Performance Insights Skill - Changelog

## Version 1.1.0 - 2026-03-18

### 🔧 Bug Fixes
- **Fixed Python compatibility**: Updated shebang to use `python3` instead of `python`
- **Fixed datetime deprecation**: Replaced `datetime.utcnow()` with `datetime.now(timezone.utc)`
- **Fixed indentation errors**: Corrected syntax errors in performance_report.py
- **Fixed metric name formats**: Updated to use correct Performance Insights metric names for Aurora MySQL

### ✨ New Features
- **Enhanced Top SQL Analysis**: Added comprehensive SQL statement analysis with load percentage
- **Improved Wait Event Analysis**: Better categorization and percentage breakdown of wait events
- **Better Error Handling**: More descriptive error messages and graceful fallbacks
- **Enhanced Output Formatting**: Improved readability for both text and JSON output formats

### 🎯 Improvements
- **Database Engine Detection**: Automatic detection of Aurora MySQL vs PostgreSQL for appropriate metrics
- **Load Metrics Display**: Added average, peak, and minimum load statistics
- **SQL Statement Formatting**: Truncated long SQL statements for better display
- **Time Range Flexibility**: Support for both relative (--hours) and absolute (--start-time/--end-time) time ranges

### 📋 Files Modified
1. **scripts/top_sql.py**: Complete rewrite for better Aurora MySQL support
2. **scripts/pi_metrics.py**: Fixed metric queries and engine-specific logic
3. **scripts/performance_report.py**: Fixed syntax errors and improved report generation

### 🧪 Tested With
- Aurora MySQL 8.0.mysql_aurora.3.10.3
- Instance type: db.r7g.large
- Performance Insights enabled with 465-day retention

### 🔍 Verification
All scripts now successfully:
- ✅ Resolve DB identifiers to resource IDs
- ✅ Query Performance Insights metrics correctly
- ✅ Display Top SQL statements with load percentages
- ✅ Show wait events analysis
- ✅ Generate comprehensive reports

### 💡 Usage Examples
```bash
# Get Top SQL for the last 2 hours
python3 scripts/top_sql.py --db-resource-id your-db-instance --hours 2 --limit 10

# Query load metrics
python3 scripts/pi_metrics.py --db-resource-id your-db-instance --metric-type load --hours 1

# Generate comprehensive report
python3 scripts/performance_report.py --db-resource-id your-db-instance --hours 4 --output-format text
```

### 🚀 Next Steps
- Consider adding support for custom metric filters
- Add trend analysis capabilities
- Implement alerting thresholds for performance metrics