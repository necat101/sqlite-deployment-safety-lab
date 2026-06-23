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

## Current Experiments

### ✅ Experiment 1: WAL Concurrency Limits (`experiments/01_wal_concurrency.py`)
**Status**: Validated  
**Proves**: SQLite allows only ONE writer at a time, even in WAL mode. Concurrent writers get SQLITE_BUSY.

**Real output**:
```
Summary: 3 succeeded, 2 failed
Final row count: 4 (expected 6)
Lost writes: 2
```

### 🚧 Experiments 2-5: In Progress
The following experiments are planned but not yet committed:
- `02_overlapping_deploys.py` - Blue-green deploy simulation
- `03_checkpoint_behavior.py` - WAL growth with long-running readers  
- `04_unsafe_backup.py` - `cp` vs `.backup` API
- `05_busy_timeout.py` - SQLITE_BUSY timeout behavior

## Running the Lab

```bash
git clone https://github.com/necat101/sqlite-deployment-safety-lab.git
cd sqlite-deployment-safety-lab
python3 experiments/01_wal_concurrency.py
# Or run all: ./run_all.sh
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

See [VALIDATED_RESULTS.md](VALIDATED_RESULTS.md) for detailed test output from local execution.
