# SQLite Deployment Safety Lab

Demonstrates real-world SQLite deployment issues from [HN #47637353](https://news.ycombinator.com/item?id=47637353) about running SQLite in production.

## The HN Debate Summary

**The incident**: Ultrathink.art lost 2 orders after **11 pushes in 2 hours** with overlapping Kamal deploys. Three containers simultaneously accessed the same SQLite WAL file on a shared Docker volume. Orders 16 and 17 succeeded in Stripe but never made it to the database.

**HN discussion themes**:
- **Operational failure, not SQLite failure**: Pushing straight to main, agents auto-deploying, no deploy serialization
- **WAL shared-memory across containers**: Debated whether mmap'd `-shm` files work reliably across Docker containers (they do, via the shared volume)
- **Single-writer limitation**: Many commenters clarified WAL allows concurrent readers but NOT concurrent writers
- **Process termination risk**: Overlapping deploys + SIGTERM mid-transaction = data loss
- **Backup safety**: `cp` vs SQLite's `.backup` API - raw copies can be corrupt

## Experiments

All 5 experiments are now committed and ready to run:

### ✅ Experiment 1: WAL Concurrency Limits
**File**: `experiments/01_wal_concurrency.py`  
**Proves**: SQLite allows only ONE writer at a time, even in WAL mode. Concurrent writers get SQLITE_BUSY.

**Validated output**:
```
Summary: 3 succeeded, 2 failed
Lost writes: 2
✗ PROVEN: Even in WAL mode, SQLite allows only ONE writer at a time
```

### ✅ Experiment 2: Overlapping Deploys
**File**: `experiments/02_overlapping_deploys.py`  
**Proves**: Simulates 3 containers with overlapping lifetimes writing to shared DB.

**Note**: In controlled tests, SQLite properly serializes writes and no data is lost. Real data loss occurs when processes are SIGTERM'd mid-transaction or applications don't handle SQLITE_BUSY errors.

### ✅ Experiment 3: Checkpoint Blocking
**File**: `experiments/03_checkpoint_behavior.py`  
**Proves**: Long-running readers block checkpoints, causing WAL files to grow.

### ✅ Experiment 4: Unsafe Backups
**File**: `experiments/04_unsafe_backup.py`  
**Proves**: `cp` can create corrupt backups when copying live databases. Use `sqlite3 .backup` instead.

### ✅ Experiment 5: Busy Timeout
**File**: `experiments/05_busy_timeout.py`  
**Proves**: How `timeout: 5000` works - writers wait up to 5 seconds, then fail with SQLITE_BUSY.

## Running the Lab

```bash
git clone https://github.com/necat101/sqlite-deployment-safety-lab.git
cd sqlite-deployment-safety-lab

# Run all experiments
./run_all.sh

# Or run individually
python3 experiments/01_wal_concurrency.py
python3 experiments/02_overlapping_deploys.py
# etc.
```

## Key Takeaways

1. **SQLite WAL ≠ Multi-writer**: WAL enables concurrent readers + single writer. Writes are serialized.
2. **Deploy serialization is mandatory**: Use GitHub Actions concurrency:
   ```yaml
   concurrency:
     group: production-deploy
     cancel-in-progress: false
   ```
3. **Never use `cp` for backups**: Use `sqlite3 db ".backup backup.db"` or the backup API
4. **Monitor WAL size**: Long-running readers block checkpoints, causing unbounded growth
5. **Handle SQLITE_BUSY**: With `timeout: 5000`, writers wait 5s then fail. App must retry or handle the error.

## References

- [HN Thread #47637353](https://news.ycombinator.com/item?id=47637353)
- [Ultrathink: SQLite in Production](https://ultrathink.art/blog/sqlite-in-production-lessons)
- [SQLite WAL Mode](https://sqlite.org/wal.html)
- [How to Corrupt SQLite](https://sqlite.org/howtocorrupt.html)
- [GitHub Actions: Control Workflow Concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)

## Validation Status

See [VALIDATED_RESULTS.md](VALIDATED_RESULTS.md) for detailed test output.

**Experiment 1**: ✅ Fully validated with real output showing 2 of 5 writers failing  
**Experiments 2-5**: ✅ Scripts committed, validated locally - run them to see results
