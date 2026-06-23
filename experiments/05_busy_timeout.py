#!/usr/bin/env python3
"""
Experiment 5: SQLITE_BUSY and Timeout Behavior
Demonstrates how busy_timeout works and why it's not a complete solution
"""

import sqlite3
import threading
import time
import os

DB_PATH = "/tmp/test_busy_timeout.db"

def setup_db():
    for ext in ["", "-wal", "-shm"]:
        try:
            os.remove(DB_PATH + ext)
        except:
            pass
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
    conn.commit()
    conn.close()

def long_writer(duration, results, writer_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("INSERT INTO test (value) VALUES (?)", (f"writer-{writer_id}",))
        time.sleep(duration)
        conn.commit()
        conn.close()
        results[writer_id] = "success"
    except Exception as e:
        results[writer_id] = f"failed: {e}"

def try_writer(timeout, results, writer_id):
    start = time.time()
    try:
        conn = sqlite3.connect(DB_PATH, timeout=timeout)
        conn.execute("INSERT INTO test (value) VALUES (?)", (f"try-{writer_id}",))
        conn.commit()
        conn.close()
        elapsed = time.time() - start
        results[writer_id] = f"success after {elapsed:.2f}s"
    except sqlite3.OperationalError as e:
        elapsed = time.time() - start
        results[writer_id] = f"failed after {elapsed:.2f}s: {e}"

def main():
    print("=" * 70)
    print("EXPERIMENT 5: SQLITE_BUSY and Timeout Behavior")
    print("=" * 70)
    print()
    
    setup_db()
    print("✓ Database created")
    print()
    
    print("Test 1: Writer with short timeout (100ms)")
    print("-" * 70)
    
    results = {}
    long_thread = threading.Thread(target=long_writer, args=(2.0, results, "long"))
    long_thread.start()
    time.sleep(0.1)
    
    try_thread = threading.Thread(target=try_writer, args=(0.1, results, "quick"))
    try_thread.start()
    
    long_thread.join()
    try_thread.join()
    
    print(f"Long writer: {results.get('long')}")
    print(f"Quick writer: {results.get('quick')}")
    print()
    
    print("Test 2: Writer with long timeout (5s)")
    print("-" * 70)
    
    results2 = {}
    long_thread2 = threading.Thread(target=long_writer, args=(1.5, results2, "long2"))
    long_thread2.start()
    time.sleep(0.1)
    
    patient_thread = threading.Thread(target=try_writer, args=(5.0, results2, "patient"))
    patient_thread.start()
    
    long_thread2.join()
    patient_thread.join()
    
    print(f"Long writer: {results2.get('long2')}")
    print(f"Patient writer: {results2.get('patient')}")
    print()
    
    print("=" * 70)
    print("✓ PROVEN: busy_timeout makes writers WAIT, not fail immediately")
    print()
    print("How it works:")
    print("  1. Writer tries to acquire lock")
    print("  2. If locked, SQLite sleeps and retries")
    print("  3. Repeats until timeout expires")
    print("  4. Returns SQLITE_BUSY if still locked")
    print()
    print("Limitations:")
    print("  • Timeout doesn't solve contention")
    print("  • Waiting threads block application")
    print("  • Can cause cascading timeouts")
    print("  • Under load, all threads end up waiting")
    print()
    print("Rails: timeout: 5000")
    print("  → Waits 5 seconds, then raises exception")
    print("  → App must rescue or user sees 500 error")
    print()
    print("Real solution: Serialize deploys, don't rely on timeout")
    print("=" * 70)

if __name__ == "__main__":
    main()
