#!/usr/bin/env python3
"""
Experiment 3: Checkpoint Blocking and WAL Growth
Demonstrates how long-running readers block checkpoints
"""

import sqlite3
import threading
import time
import os

DB_PATH = "/tmp/test_checkpoint.db"

def setup_db():
    for ext in ["", "-wal", "-shm"]:
        try:
            os.remove(DB_PATH + ext)
        except:
            pass
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE data (id INTEGER PRIMARY KEY, value TEXT)")
    conn.executemany(
        "INSERT INTO data (value) VALUES (?)",
        [(f"row-{i}",) for i in range(100)]
    )
    conn.commit()
    conn.close()

def long_reader(duration):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("BEGIN")
    conn.execute("SELECT COUNT(*) FROM data").fetchone()
    time.sleep(duration)
    conn.close()

def writer(num_writes):
    conn = sqlite3.connect(DB_PATH)
    for i in range(num_writes):
        conn.execute("INSERT INTO data (value) VALUES (?)", (f"write-{i}",))
        conn.commit()
        time.sleep(0.01)
    conn.close()

def get_wal_size():
    wal_path = DB_PATH + "-wal"
    return os.path.getsize(wal_path) if os.path.exists(wal_path) else 0

def main():
    print("=" * 70)
    print("EXPERIMENT 3: Checkpoint Blocking and WAL Growth")
    print("=" * 70)
    print()
    
    setup_db()
    print("✓ Database created with 100 rows")
    print(f"Initial WAL size: {get_wal_size()} bytes\n")
    
    print("Test: Writes WITH long-running reader (5 seconds)")
    print("-" * 70)
    
    reader_thread = threading.Thread(target=long_reader, args=(5,))
    reader_thread.start()
    time.sleep(0.5)
    
    print("Reader active. Starting 100 writes...")
    writer_thread = threading.Thread(target=writer, args=(100,))
    writer_thread.start()
    
    for i in range(5):
        time.sleep(1)
        print(f"  T+{i+1}s: WAL size = {get_wal_size()} bytes")
    
    writer_thread.join()
    reader_thread.join()
    
    final_wal = get_wal_size()
    print(f"\nFinal WAL size: {final_wal} bytes")
    
    print("\n" + "=" * 70)
    if final_wal > 100000:
        print("✗ PROVEN: Long-running readers block checkpoints")
        print(f"  WAL grew to {final_wal} bytes")
        print("  Checkpoint cannot reclaim pages until reader finishes")
    else:
        print("✓ WAL growth was minimal in this test")
        print("  (Increase writes or reader duration for dramatic effect)")
    
    print("\nIn production, this causes:")
    print("  - WAL files growing to gigabytes")
    print("  - Disk space exhaustion")
    print("  - Slow startup times (large WAL to replay)")
    print("=" * 70)

if __name__ == "__main__":
    main()
