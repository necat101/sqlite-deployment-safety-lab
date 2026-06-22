# Test Results

## Local Test Execution - 2026-06-22

### Test 1: WAL Basics ✓ PASS
- WAL file created: 8KB → 12KB with 5 inserts
- Checkpoint truncated WAL to 0 bytes
- Main DB grew to 8KB

### Test 4: Checkpoints ✓ PASS  
- WAL grew to 41KB with 100 inserts
- Long-running reader blocked checkpoint
- WAL remained at 41KB until reader closed
- After close: WAL truncated to 0 bytes

**Proves checkpoint starvation is real** - exactly as documented at sqlite.org/wal.html

### Remaining Tests
Tests 2, 3, 5, and 6 are in the repo and ready to run. They demonstrate:
- Concurrent writer contention
- Deploy overlap simulation
- Backup safety (cp vs .backup)
- SQLITE_BUSY handling

Run with: `python3 tests/<test_name>.py`

## Repository
https://github.com/necat101/sqlite-deployment-safety-lab