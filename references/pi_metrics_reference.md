# Performance Insights Metrics Reference

## Core Metrics

### CPU Metrics
| Metric Name | Description | Unit | Typical Range |
|-------------|-------------|------|---------------|
| `db.CPU.total.pct` | Total CPU utilization across all processes | Percentage | 0-100% |
| `db.CPU.Innodb.pct` | CPU utilization by InnoDB storage engine | Percentage | 0-100% |
| `db.CPU.user.pct` | CPU utilization by user processes | Percentage | 0-100% |
| `db.CPU.sys.pct` | CPU utilization by system processes | Percentage | 0-100% |
| `db.CPU.wait.pct` | CPU wait time percentage | Percentage | 0-100% |
| `db.CPU.irq.pct` | CPU interrupt time percentage | Percentage | 0-100% |

### Memory Metrics
| Metric Name | Description | Unit | Typical Range |
|-------------|-------------|------|---------------|
| `db.Memory.total.pct` | Total memory utilization | Percentage | 0-100% |
| `db.Memory.Innodb.pct` | Memory used by InnoDB storage engine | Percentage | 0-100% |
| `db.Memory.bufferPool.pct` | InnoDB buffer pool utilization | Percentage | 60-95% |
| `db.Memory.freeable.total` | Freeable memory amount | Bytes | Variable |
| `db.Memory.cached.total` | Cached memory amount | Bytes | Variable |

### I/O Metrics
| Metric Name | Description | Unit | Typical Range |
|-------------|-------------|------|---------------|
| `db.IO.total.pct` | Total I/O utilization | Percentage | 0-100% |
| `db.IO.read.pct` | Read I/O utilization | Percentage | 0-100% |
| `db.IO.write.pct` | Write I/O utilization | Percentage | 0-100% |
| `db.IO.await.avg` | Average I/O wait time | Milliseconds | 1-50ms |
| `db.IO.util.avg` | Average I/O utilization | Percentage | 0-100% |

### Connection and Session Metrics
| Metric Name | Description | Unit | Typical Range |
|-------------|-------------|------|---------------|
| `db.Connections.Avg` | Average number of connections | Count | 0-max_connections |
| `db.Connections.Max` | Maximum connections used | Count | 0-max_connections |
| `db.Sessions.active.avg` | Average active sessions | Count | 0-connections |
| `db.Sessions.total.avg` | Average total sessions | Count | 0-connections |

### Transaction and Throughput Metrics
| Metric Name | Description | Unit | Typical Range |
|-------------|-------------|------|---------------|
| `db.Transactions.Avg` | Average transactions per second | Count/sec | Variable |
| `db.Transactions.total` | Total transactions | Count | Cumulative |
| `db.Queries.Avg` | Average queries per second | Count/sec | Variable |
| `db.Queries.total` | Total queries executed | Count | Cumulative |

## SQL Performance Metrics

### Statement-Level Metrics
| Metric Name | Description | Unit |
|-------------|-------------|------|
| `db.SQL.Innodb.avg_timer_wait.avg` | Average wait time per SQL statement | Microseconds |
| `db.SQL.Innodb.sum_timer_wait.avg` | Total wait time per SQL statement | Microseconds |
| `db.SQL.Innodb.count_star.avg` | Execution count per SQL statement | Count |
| `db.SQL.Innodb.sum_lock_time.avg` | Total lock time per SQL statement | Microseconds |
| `db.SQL.Innodb.sum_rows_examined.avg` | Total rows examined per statement | Count |
| `db.SQL.Innodb.sum_rows_sent.avg` | Total rows sent per statement | Count |

### Query Cache Metrics (MySQL)
| Metric Name | Description | Unit |
|-------------|-------------|------|
| `db.Cache.query.hitRatio.avg` | Query cache hit ratio | Percentage |
| `db.Cache.query.inserts.avg` | Query cache inserts per second | Count/sec |
| `db.Cache.query.prunes.avg` | Query cache prunes per second | Count/sec |

## Wait Event Metrics

### Common Wait Event Categories

#### I/O Wait Events
- `io/file/sql/binlog` - Binary log I/O operations
- `io/file/sql/relay_log` - Relay log I/O operations  
- `io/file/innodb/innodb_data_file` - InnoDB data file I/O
- `io/file/innodb/innodb_log_file` - InnoDB log file I/O
- `io/file/myisam/dfile` - MyISAM data file I/O

#### Lock Wait Events
- `synch/mutex/innodb/buf_pool_mutex` - Buffer pool mutex contention
- `synch/mutex/innodb/log_sys_mutex` - Log system mutex contention
- `synch/rwlock/innodb/index_tree_rw_lock` - Index tree lock contention
- `synch/mutex/sql/TABLE_SHARE::LOCK_ha_data` - Table share lock contention

#### CPU and Processing Events
- `stage/sql/executing` - SQL execution stage
- `stage/sql/Sending data` - Data transmission stage
- `stage/sql/Sorting result` - Result sorting stage
- `stage/sql/Creating sort index` - Sort index creation

#### Network Wait Events
- `idle` - Connection idle time
- `stage/sql/Reading from net` - Network read operations
- `stage/sql/Writing to net` - Network write operations

## Engine-Specific Metrics

### InnoDB Metrics (MySQL)
| Metric Name | Description |
|-------------|-------------|
| `db.Innodb.buffer_pool_pages_data.avg` | Data pages in buffer pool |
| `db.Innodb.buffer_pool_pages_dirty.avg` | Dirty pages in buffer pool |
| `db.Innodb.buffer_pool_pages_free.avg` | Free pages in buffer pool |
| `db.Innodb.buffer_pool_read_requests.avg` | Buffer pool read requests |
| `db.Innodb.buffer_pool_reads.avg` | Physical reads to buffer pool |
| `db.Innodb.log_waits.avg` | Log buffer waits |
| `db.Innodb.log_writes.avg` | Log writes |

### Aurora-Specific Metrics
| Metric Name | Description |
|-------------|-------------|
| `db.Aurora.binarylog_replica_lag.avg` | Binary log replica lag |
| `db.Aurora.replica_lag.avg` | Aurora replica lag |
| `db.Aurora.storage_net_throughput.avg` | Storage network throughput |

## Performance Thresholds and Benchmarks

### Critical Thresholds
| Metric | Warning | Critical | Notes |
|--------|---------|----------|-------|
| CPU Utilization | >70% | >85% | Sustained high CPU indicates resource constraint |
| Memory Utilization | >80% | >90% | High memory usage can lead to swapping |
| I/O Utilization | >70% | >85% | High I/O can cause query slowdowns |
| Buffer Pool Hit Ratio | <95% | <90% | Low hit ratio indicates insufficient buffer pool |
| Average Connection Time | >100ms | >500ms | Long connection times indicate contention |
| Lock Wait Time | >10ms | >100ms | High lock waits indicate contention issues |

### Optimization Targets
- **CPU**: Keep average utilization below 70% with peaks under 85%
- **Memory**: Maintain buffer pool hit ratio above 95%
- **I/O**: Target average I/O wait times under 10ms
- **Connections**: Keep connection utilization under 80% of max_connections
- **Queries**: Aim for average query response time under 100ms

## Metric Aggregation Methods

### Statistical Functions
- **Average (avg)**: Mean value over time period
- **Maximum (max)**: Peak value during time period  
- **Total (total)**: Sum of all values
- **Count (count)**: Number of occurrences

### Time-Based Aggregation
- **Point-in-time**: Single measurement at specific timestamp
- **Period average**: Average over specified time period (e.g., 5-minute intervals)
- **Rolling average**: Moving average over sliding time window
- **Peak analysis**: Maximum values during specified periods

## Troubleshooting with Metrics

### High CPU Scenarios
1. Check `db.SQL.Innodb.avg_timer_wait.avg` for expensive queries
2. Review `db.CPU.user.pct` vs `db.CPU.sys.pct` ratio
3. Analyze wait events for CPU-bound operations

### Memory Issues
1. Monitor `db.Memory.bufferPool.pct` utilization
2. Check for memory pressure via `db.Memory.freeable.total`
3. Review connection count vs available memory

### I/O Bottlenecks
1. Examine `db.IO.await.avg` for disk latency
2. Check read vs write I/O patterns
3. Analyze storage-related wait events

### Lock Contention
1. Review lock-related wait events
2. Check `db.SQL.Innodb.sum_lock_time.avg` for problematic queries
3. Monitor transaction duration and frequency