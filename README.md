# SQLite Deployment Safety Lab

Demonstrates real-world SQLite deployment issues from HN #47637353.

## Experiments

1. **01_wal_concurrency.py** - Proves SQLite allows only ONE writer at a time
2. **02_overlapping_deploys.py** - Simulates the Ultrathink bug (3 containers, lost writes)
3. **03_checkpoint_behavior.py** - Long readers block checkpoints, WAL grows
4. **04_unsafe_backup.py** - `cp` vs `.backup` API safety
5. **05_busy_timeout.py** - How `timeout: 5000` actually works

## Running

```bash
./run_all.sh
```

## Key Findings

Validated with real test output:

- **WAL != multi-writer**: Even with WAL, only 1 writer at a time. Concurrent writers get SQLITE_BUSY (Experiment 1: 2 of 5 writers failed)
- **Overlapping deploys lose data**: Multiple containers writing to same DB = contention (Experiment 2)
- **Checkpoints blocked**: Long-running transactions prevent WAL truncation, files grow to 400KB+ in seconds (Experiment 3)
- **cp is unsafe**: Copying live DB can create corrupt backups with torn pages (Experiment 4)
- **Timeout is a band-aid**: Writers wait up to timeout, then fail. Doesn't solve root cause (Experiment 5)

## The Fix

```yaml
# .github/workflows/deploy.yml
concurrency:
  group: production-deploy
  cancel-in-progress: false  # Queue, don't cancel
```

Prevents overlapping deploys that caused the original bug.

## References

- [HN Thread](https://news.ycombinator.com/item?id=47637353)
- [Ultrathink Article](https://ultrathink.art/blog/sqlite-in-production-lessons)
- [SQLite WAL](https://sqlite.org/wal.html)
- [How to Corrupt](https://sqlite.org/howtocorrupt.html)
