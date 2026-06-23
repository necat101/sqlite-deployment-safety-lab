#!/bin/bash
# Run all SQLite deployment safety experiments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPERIMENTS_DIR="$SCRIPT_DIR/experiments"
RESULTS_DIR="$SCRIPT_DIR/results"

mkdir -p "$RESULTS_DIR"

echo "=========================================="
echo "SQLite Deployment Safety Lab"
echo "=========================================="
echo ""
echo "Running all experiments..."
echo "Results will be saved to: $RESULTS_DIR"
echo ""

# Run each experiment and capture output
experiments=(
    "01_wal_concurrency.py"
    "02_overlapping_deploys.py"
    "03_checkpoint_behavior.py"
    "04_unsafe_backup.py"
    "05_busy_timeout.py"
)

for exp in "${experiments[@]}"; do
    if [ -f "$EXPERIMENTS_DIR/$exp" ]; then
        echo "=========================================="
        echo "Running: $exp"
        echo "=========================================="
        
        output_file="$RESULTS_DIR/${exp%.py}.txt"
        
        if python3 "$EXPERIMENTS_DIR/$exp" 2>&1 | tee "$output_file"; then
            echo "✓ Completed: $exp"
        else
            echo "✗ Failed: $exp"
        fi
        
        echo ""
        echo ""
        sleep 1
    else
        echo "⚠ Skipping $exp (not found)"
    fi
done

echo "=========================================="
echo "All experiments completed!"
echo "=========================================="
echo ""
echo "Results saved in: $RESULTS_DIR"
ls -lh "$RESULTS_DIR" 2>/dev/null || echo "No results yet"
echo ""
echo "Key findings:"
echo "1. WAL allows only ONE writer at a time"
echo "2. Overlapping deploys cause lost writes"
echo "3. Long readers block checkpoints → WAL growth"
echo "4. cp backups are unsafe, use sqlite3 .backup"
echo "5. busy_timeout delays but doesn't solve contention"
echo ""
echo "For GitHub Actions, add to your workflow:"
echo ""
echo "concurrency:"
echo "  group: production-deploy"
echo "  cancel-in-progress: false"
echo ""
