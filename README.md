# SQLite Deployment Safety Lab

Reproduces the real-world SQLite production issues from the Hacker News discussion "SQLite in Production: Lessons from Running a Store on a Single File" (HN #47637353).

## Quick Start

```bash
git clone https://github.com/necat101/sqlite-deployment-safety-lab.git
cd sqlite-deployment-safety-lab
python3 tests/01_wal_basics.py
python3 tests/02_concurrent_writers.py
python3 tests/04_checkpoints.py
```

## The Hacker News Debate

**The Problem:** A production e-commerce store lost 2 orders after 11 deploys in 2 hours. `sqlite_sequence` showed IDs 16 and 17 allocated, but `MAX(id)` returned 15.

**Root Cause:** Blue-green deploys with overlapping containers mounting the same Docker volume created 3+ concurrent writers to the same WAL file.

**The Fix:** GitHub Actions concurrency controls + safe backup methods.

## Tests

1. **01_wal_basics.py** - WAL mode fundamentals
2. **02_concurrent_writers.py** - Simulates overlapping containers
3. **03_deploy_simulation.py** - Blue-green deploy overlap
4. **04_checkpoints.py** - Checkpoint starvation demo
5. **05_backup_safety.py** - `cp` vs `.backup` API
6. **06_busy_handling.py** - SQLITE_BUSY strategies

## Key Findings

- WAL enables concurrent readers but NOT concurrent writers
- `sqlite_sequence` gaps reveal lost transactions
- Long-running readers block checkpoints (WAL grows without bound)
- `cp` backups are unsafe - use `.backup` API
- `timeout: 5000` is a band-aid, not a fix

## Full Documentation

See [RESULTS.md](RESULTS.md) for detailed test results and analysis.

## The Verdict

SQLite works for single-server deployments **IF**:
- GitHub Actions concurrency prevents overlapping deploys
- Backups use `.backup` API (not `cp`)
- Write volume is moderate
- You monitor for SQLITE_BUSY

The HN author's lost orders were a **deployment process failure**, not a SQLite failure.