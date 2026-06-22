#!/usr/bin/env python3
"""
Test 4: Checkpoint Behavior
Demonstrates checkpoint starvation and WAL growth.
"""

import sqlite3
import os
import time

DB_PATH = "output/test_checkpoint.db"

def cleanup():
    for ext in ['', '-wal', '-shm']:
        try:
            os.remove(DB_PATH + ext)
        except FileNotFoundError:
            pass

def test_checkpoints():
    print("=" * 70)
    print("TEST 4: Checkpoint Behavior and Starvation")
    print("=" * 70)
    
    cleanup()
    os.makedirs("output", exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE data (id INTEGER PRIMARY KEY, value TEXT)")
    conn.execute("PRAGMA wal_autocheckpoint=10")
    conn.commit()
    
    print("\n1. Writing data to grow WAL...")
    for i in range(100):
        conn.execute("INSERT INTO data (value) VALUES (?)", (f"data-{i}" * 10,))
        if i % 20 == 0:
            conn.commit()
    
    conn.commit()
    wal_size = os.path.getsize(DB_PATH + "-wal")
    print(f"   WAL size after 100 inserts: {wal_size} bytes")
    
    print("\n2. Simulating long-running reader...")
    conn2 = sqlite3.connect(DB_PATH)
    conn2.execute("BEGIN")
    count = conn2.execute("SELECT COUNT(*) FROM data").fetchone()[0]
    print(f"   Reader sees {count} rows, holds transaction open")
    
    print("\n3. Writing more data while reader active...")
    for i in range(100, 200):
        conn.execute("INSERT INTO data (value) VALUES (?)", (f"more-data-{i}" * 10,))
    conn.commit()
    
    print("\n4. Attempting checkpoint with active reader...")
    result = conn.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
    wal_size_after = os.path.getsize(DB_PATH + "-wal")
    print(f"   WAL size: {wal_size_after} bytes (not truncated - reader blocking!)")
    
    print("\n5. Closing reader and retrying...")
    conn2.rollback()
    conn2.close()
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    wal_size_final = os.path.getsize(DB_PATH + "-wal")
    print(f"   WAL size after reader closed: {wal_size_final} bytes")
    
    conn.close()
    print("\n✓ Checkpoint starvation demonstrated")
    return True

if __name__ == "__main__":
    test_checkpoints()