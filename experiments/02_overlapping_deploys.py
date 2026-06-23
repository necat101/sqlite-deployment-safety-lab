#!/usr/bin/env python3
"""
Experiment 2: Overlapping Deploys Simulation
Reproduces the exact failure from the Ultrathink blog:
Multiple "containers" (processes) accessing same DB during blue-green deploy
"""

import sqlite3
import multiprocessing
import time
import os
import random

DB_PATH = "/tmp/test_overlapping_deploys.db"

def setup_db():
    if os.path.exists(DB_PATH):
        for ext in ["", "-wal", "-shm"]:
            try:
                os.remove(DB_PATH + ext)
            except:
                pass
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_num INTEGER,
            stripe_id TEXT,
            amount INTEGER,
            created_at REAL
        )
    """)
    conn.commit()
    conn.close()

def container_process(container_id, num_orders, results):
    """Simulates a container processing orders"""
    created_ids = []
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL")
        
        for i in range(num_orders):
            time.sleep(random.uniform(0.01, 0.05))
            
            try:
                stripe_id = f"pi_{container_id}_{i}_{int(time.time()*1000)}"
                cursor = conn.execute("""
                    INSERT INTO orders (order_num, stripe_id, amount, created_at)
                    VALUES (?, ?, ?, ?)
                """, (i, stripe_id, 1000 + i, time.time()))
                
                order_id = cursor.lastrowid
                created_ids.append(order_id)
                conn.commit()
                
            except sqlite3.OperationalError as e:
                results[f"container_{container_id}_errors"] = str(e)
                conn.rollback()
        
        conn.close()
        results[f"container_{container_id}"] = created_ids
        
    except Exception as e:
        results[f"container_{container_id}_exception"] = str(e)

def main():
    print("=" * 70)
    print("EXPERIMENT 2: Overlapping Deploys (The Ultrathink Bug)")
    print("=" * 70)
    print()
    print("Simulating: 3 containers with overlapping lifetimes")
    print("Each processes orders and writes to shared SQLite DB")
    print()
    
    setup_db()
    print("✓ Database initialized")
    print()
    
    manager = multiprocessing.Manager()
    results = manager.dict()
    processes = []
    
    print("Timeline:")
    print("  T+0.0s: Container 1 starts (10 orders)")
    p1 = multiprocessing.Process(target=container_process, args=(1, 10, results))
    processes.append(p1)
    p1.start()
    
    time.sleep(0.15)
    print("  T+0.15s: Container 2 starts (10 orders) - OVERLAP!")
    p2 = multiprocessing.Process(target=container_process, args=(2, 10, results))
    processes.append(p2)
    p2.start()
    
    time.sleep(0.15)
    print("  T+0.3s: Container 3 starts (10 orders) - TRIPLE OVERLAP!")
    p3 = multiprocessing.Process(target=container_process, args=(3, 10, results))
    processes.append(p3)
    p3.start()
    
    print("\nWaiting for all containers to finish...")
    for p in processes:
        p.join()
    
    print("✓ All containers finished\n")
    
    conn = sqlite3.connect(DB_PATH)
    db_rows = conn.execute("SELECT id FROM orders").fetchall()
    actual_count = len(db_rows)
    
    all_created = []
    for key in results:
        if key.startswith("container_") and not key.endswith(("_errors", "_exception")):
            all_created.extend(results[key])
    
    thought_count = len(all_created)
    
    print("Results:")
    print("-" * 70)
    print(f"Containers thought they created: {thought_count} orders")
    print(f"Actual rows in database: {actual_count} orders")
    print(f"Discrepancy: {thought_count - actual_count} orders")
    print()
    
    if actual_count < thought_count:
        print("✗ ORDERS LOST during overlapping deploys!")
    else:
        print("✓ No orders lost in this controlled run")
        print("  (SQLite properly serialized all writes)")
        print()
        print("Note: Real data loss occurs when:")
        print("  - Containers receive SIGTERM mid-transaction")
        print("  - Applications don't handle SQLITE_BUSY errors")
        print("  - Processes are killed before commit completes")
        print("  - Network partitions interrupt writes")
    
    print()
    seq = conn.execute("SELECT seq FROM sqlite_sequence WHERE name='orders'").fetchone()
    if seq:
        print(f"sqlite_sequence: {seq[0]}, MAX(id): {max([r[0] for r in db_rows]) if db_rows else 0}")
    
    conn.close()
    print("=" * 70)

if __name__ == "__main__":
    main()
