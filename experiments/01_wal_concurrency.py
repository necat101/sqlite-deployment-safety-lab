#!/usr/bin/env python3
"""
Experiment 1: WAL Concurrency Limits
Demonstrates that SQLite allows only ONE writer at a time, even in WAL mode.
"""

import sqlite3
import threading
import time
import os

DB_PATH = "/tmp/test_wal_concurrency.db"

def setup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, data TEXT)")
    conn.execute("INSERT INTO orders (data) VALUES ('initial')")
    conn.commit()
    conn.close()

def writer_thread(thread_id, results):
    try:
        conn = sqlite3.connect(DB_PATH, timeout=1.0)
        conn.execute("PRAGMA journal_mode=WAL")
        start = time.time()
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("INSERT INTO orders (data) VALUES (?)", (f"thread-{thread_id}",))
        time.sleep(0.5)
        conn.commit()
        elapsed = time.time() - start
        conn.close()
        results[thread_id] = {"status": "success", "time": elapsed}
    except sqlite3.OperationalError as e:
        results[thread_id] = {"status": "failed", "error": str(e)}

def main():
    print("=" * 70)
    print("EXPERIMENT 1: WAL Concurrency - Single Writer Limitation")
    print("=" * 70)
    print()
    
    setup_db()
    print("✓ Database created with WAL mode")
    print()
    
    print("Starting 5 concurrent writers (each holds lock for 0.5s)...")
    results = {}
    threads = []
    
    start_time = time.time()
    for i in range(5):
        t = threading.Thread(target=writer_thread, args=(i, results))
        threads.append(t)
        t.start()
        time.sleep(0.05)
    
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    print(f"\nResults after {total_time:.2f}s:")
    print("-" * 70)
    
    success_count = 0
    failed_count = 0
    
    for i in range(5):
        result = results.get(i, {})
        if result.get("status") == "success":
            success_count += 1
            print(f"  Thread {i}: ✓ SUCCESS in {result['time']:.2f}s")
        else:
            failed_count += 1
            print(f"  Thread {i}: ✗ FAILED - {result.get('error', 'unknown')}")
    
    print(f"\nSummary: {success_count} succeeded, {failed_count} failed")
    
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    conn.close()
    
    print(f"Final row count: {count} (expected 6: 1 initial + 5 inserts)")
    print(f"Lost writes: {6 - count}")
    
    if failed_count > 0:
        print("\n✗ PROVEN: Concurrent writers contend for exclusive lock")
        print("  Even in WAL mode, SQLite allows only ONE writer at a time")
        print("  Other writers get SQLITE_BUSY or wait for timeout")
    else:
        print("\n✓ All writers succeeded (they were serialized by SQLite)")
    
    print("\nThis is why overlapping deploys are dangerous:")
    print("- Deploy A starts writing")
    print("- Deploy B starts while A is still draining")
    print("- Both try to write → contention → potential data loss")
    print("=" * 70)

if __name__ == "__main__":
    main()
