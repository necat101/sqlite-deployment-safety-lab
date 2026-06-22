#!/usr/bin/env python3
"""
Test 2: Concurrent Writers
Simulates multiple processes writing to same SQLite DB.
"""

import sqlite3
import os
import time
import multiprocessing
import random

DB_PATH = "output/test_concurrent.db"

def cleanup():
    for ext in ['', '-wal', '-shm']:
        try:
            os.remove(DB_PATH + ext)
        except FileNotFoundError:
            pass

def worker(worker_id, num_writes, results):
    conn = sqlite3.connect(DB_PATH, timeout=1.0)
    conn.execute("PRAGMA journal_mode=WAL")
    successes = 0
    busy_errors = 0
    for i in range(num_writes):
        try:
            conn.execute("INSERT INTO orders (worker_id, item, created_at) VALUES (?, ?, ?)",
                (worker_id, f"item-{worker_id}-{i}", time.time()))
            conn.commit()
            successes += 1
            time.sleep(random.uniform(0.001, 0.01))
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                busy_errors += 1
                conn.rollback()
    conn.close()
    results[worker_id] = {"successes": successes, "busy_errors": busy_errors}

def test_concurrent_writers():
    print("=" * 70)
    print("TEST 2: Concurrent Writers")
    print("=" * 70)
    cleanup()
    os.makedirs("output", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, worker_id INTEGER, item TEXT, created_at REAL)")
    conn.commit()
    conn.close()
    print("\n1. Starting 3 concurrent writers...")
    manager = multiprocessing.Manager()
    results = manager.dict()
    processes = []
    start_time = time.time()
    for i in range(3):
        p = multiprocessing.Process(target=worker, args=(i, 50, results))
        p.start()
        processes.append(p)
        time.sleep(0.1)
    for p in processes:
        p.join()
    duration = time.time() - start_time
    conn = sqlite3.connect(DB_PATH)
    total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    max_id = conn.execute("SELECT MAX(id) FROM orders").fetchone()[0]
    seq = conn.execute("SELECT seq FROM sqlite_sequence WHERE name='orders'").fetchone()
    seq_val = seq[0] if seq else 0
    print(f"\n2. Results: {total_orders} orders in {duration:.2f}s")
    print(f"   MAX(id): {max_id}, sqlite_sequence: {seq_val}")
    if seq_val > max_id:
        print(f"   ⚠️  GAP: {seq_val - max_id} IDs allocated but not committed")
    conn.close()
    print("\n✓ Test complete - demonstrates writer contention")
    return True

if __name__ == "__main__":
    test_concurrent_writers()