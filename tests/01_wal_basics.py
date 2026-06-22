#!/usr/bin/env python3
"""
Test 1: WAL Mode Basics
Demonstrates how WAL mode works: separate -wal file, readers see consistent snapshots,
checkpointing behavior.
"""

import sqlite3
import os
import time

DB_PATH = "output/test_wal.db"

def cleanup():
    for ext in ['', '-wal', '-shm']:
        try:
            os.remove(DB_PATH + ext)
        except FileNotFoundError:
            pass

def test_wal_basics():
    print("=" * 70)
    print("TEST 1: WAL Mode Basics")
    print("=" * 70)
    
    cleanup()
    os.makedirs("output", exist_ok=True)
    
    # Create database and enable WAL
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, item TEXT, amount REAL)")
    conn.commit()
    
    print("\n1. Database created with WAL mode:")
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    print(f"   Journal mode: {mode}")
    
    # Check files exist
    print("\n2. Files on disk:")
    for f in [DB_PATH, DB_PATH + "-wal", DB_PATH + "-shm"]:
        exists = os.path.exists(f)
        size = os.path.getsize(f) if exists else 0
        print(f"   {os.path.basename(f)}: {exists} ({size} bytes)")
    
    # Insert some data
    print("\n3. Inserting orders (writers append to WAL)...")
    for i in range(5):
        conn.execute("INSERT INTO orders (item, amount) VALUES (?, ?)", 
                    (f"Item {i}", 10.0 + i))
    conn.commit()
    
    print("   Inserted 5 orders")
    
    # Check WAL file grew
    wal_size = os.path.getsize(DB_PATH + "-wal")
    print(f"   WAL file size: {wal_size} bytes")
    
    # Read data (readers read from WAL + main DB)
    print("\n4. Reading data (readers see consistent snapshot)...")
    count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    print(f"   Orders in database: {count}")
    
    # Checkpoint
    print("\n5. Running checkpoint (moves WAL data to main DB)...")
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    
    wal_size_after = os.path.getsize(DB_PATH + "-wal")
    db_size = os.path.getsize(DB_PATH)
    print(f"   WAL file size after checkpoint: {wal_size_after} bytes")
    print(f"   Main DB file size: {db_size} bytes")
    
    conn.close()
    
    print("\n✓ WAL mode basics demonstrated")
    print("  - Writers append to -wal file")
    print("  - Readers check WAL then main DB")
    print("  - Checkpoint moves data and truncates WAL")
    print()
    
    return True

if __name__ == "__main__":
    test_wal_basics()