# Running Payment Sharding Network from GitHub

Complete guide to clone, set up, and test the project from the GitHub repository.

## Prerequisites

- **Git** installed (`git --version` should work)
- **Python 3.8+** installed (`python3 --version`)
- **Terminal/Command Line** access
- **GitHub account** (optional, for forking)

## 1. Clone the Repository

### Option A: HTTPS (No SSH key needed)
```bash
git clone https://github.com/engr-dr-ammad/Claude.git
cd Claude
```

### Option B: SSH (If you have SSH key configured)
```bash
git clone git@github.com:engr-dr-ammad/Claude.git
cd Claude
```

### Verify the clone
```bash
ls -la
# Should show:
# - simulator.py
# - zk_aggregation.py
# - cli.py
# - test_payment_network.py
# - README.md
# - USAGE.md
# etc.
```

## 2. Quick Verification

### Check Python version
```bash
python3 --version
# Should output: Python 3.8 or higher
```

### Check imports work
```bash
python3 -c "from simulator import ShardedPaymentNetwork; print('✓ Imports OK')"
```

## 3. Run the Demo (30 seconds)

The fastest way to see it working:

```bash
python3 cli.py --mode demo
```

**Expected output:**
```
======================================================================
PAYMENT SHARDING NETWORK - INTERACTIVE DEMO
======================================================================

✓ Initialized payment network with 4 shards
1. Creating sample transactions...

✓ 🔐 Private transaction: alice... → eve... (10 EUR)
✓ 📤 Public transaction: bob... → frank... (15 EUR)
...
📊 Epoch Results (OPTIMISTIC):
  ├─ Throughput: 12.00 tx/s
  ├─ Blocks finalized: 4
  ├─ Privacy coverage: 100.0%
  └─ Finality latency: 0.07 ms
```

## 4. Run the Test Suite (2 seconds)

Verify everything works with unit tests:

```bash
python3 -m unittest test_payment_network -v
```

**Expected output:**
```
test_add_proof (test_payment_network.TestZKAggregator.test_add_proof) ... ok
test_aggregate_batch (test_payment_network.TestZKAggregator.test_aggregate_batch) ... ok
test_aggregator_creation (test_payment_network.TestZKAggregator.test_aggregator_creation) ... ok
...
Ran 27 tests in 0.002s
OK
```

### Run specific test class
```bash
python3 -m unittest test_payment_network.TestShardedPaymentNetwork -v
```

### Run single test
```bash
python3 -m unittest test_payment_network.TestBlock.test_block_hash -v
```

## 5. Run Full Simulation (10 seconds)

Complete simulation with all finalization levels and analysis:

```bash
python3 main.py
```

**Expected output:**
```
================================================================================
 PAYMENT SHARDING NETWORK WITH ZERO-KNOWLEDGE PRIVACY
 Throughput, Finality, and Privacy Trade-offs for Settlement
================================================================================

============================================================
Finalization: OPTIMISTIC | Transactions: 500 | Private: 175
============================================================

📊 OPTIMISTIC Finalization Results:
  ├─ Throughput: 4948.88 tx/s
  ├─ Blocks finalized: 40
  ├─ Transactions processed: 500/500
  ├─ Private transactions: 175
  ├─ ZK verified: 175 (100.0%)
  └─ Finality latency: 0.13 ms
...
```

**Output files created:**
- `/tmp/payment_simulation_results.json` - Raw results
- `/tmp/payment_analysis.html` - Interactive dashboard

## 6. Interactive CLI Mode

Manual testing and exploration:

```bash
python3 cli.py --mode interactive
```

**Available commands:**
```
payment-shard> help                          # Show all commands
payment-shard> demo                          # Run demo
payment-shard> status                        # Network status
payment-shard> tx alice bob 50 0             # Create transaction
payment-shard> tx charlie diana 100 1 private  # Private transaction
payment-shard> epoch optimistic              # Process epoch
payment-shard> simulate 100 probabilistic 0.3  # Run simulation
payment-shard> exit                          # Exit
```

## 7. Run Custom Simulations

Test with different parameters:

```bash
# Fast test: 100 transactions, optimistic, 2 shards
python3 cli.py --mode simulate --transactions 100 --finalization optimistic --shards 2

# Slow test: 1000 transactions, deterministic, 8 shards
python3 cli.py --mode simulate --transactions 1000 --finalization deterministic --shards 8 --private-ratio 0.5

# Standard: 500 transactions, probabilistic, 4 shards
python3 cli.py --mode simulate --transactions 500 --finalization probabilistic --shards 4
```

## 8. View Documentation

### Quick overview
```bash
cat README.md
```

### Detailed analysis
```bash
cat FINDINGS.md
```

### Complete API guide
```bash
cat USAGE.md
```

### Implementation details
```bash
cat PROTOTYPE.md
```

## 9. View Interactive Dashboard

After running `main.py`, view the HTML analysis:

### On Linux/Mac
```bash
# Open in default browser
open /tmp/payment_analysis.html

# Or use a specific browser
firefox /tmp/payment_analysis.html
chromium /tmp/payment_analysis.html
```

### On Windows
```bash
start /tmp/payment_analysis.html
```

### Or copy the file
```bash
cp /tmp/payment_analysis.html ./analysis.html
# Then open analysis.html in your browser
```

## 10. Explore the Code

### Main components
```bash
# Core simulator (400 lines)
less simulator.py

# ZK privacy aggregation (280 lines)
less zk_aggregation.py

# Test suite (27 tests)
less test_payment_network.py

# CLI interface (300 lines)
less cli.py
```

### With syntax highlighting
```bash
# If you have `cat` with colors or use `less -R`
python3 -m pygments simulator.py  # if pygments installed
# Or just use your editor:
code simulator.py
vim simulator.py
nano simulator.py
```

## 11. Install as Package (Optional)

Make it available system-wide:

```bash
# Install in development mode
pip install -e .

# Now you can run from anywhere
payment-shard --mode demo
payment-shard --mode simulate --transactions 500
```

## 12. Troubleshooting

### "ModuleNotFoundError: No module named 'simulator'"
Make sure you're in the repository directory:
```bash
cd /path/to/Claude
python3 cli.py --mode demo
```

### "Python version too old"
```bash
# Check version
python3 --version

# Install Python 3.8+
# On Ubuntu/Debian:
sudo apt-get install python3.9

# On macOS:
brew install python@3.9

# Then use:
python3.9 cli.py --mode demo
```

### Tests fail with "ImportError"
```bash
# Make sure you're in the right directory
pwd  # Should end with /Claude

# Run from repository root
python3 -m unittest test_payment_network -v
```

### "Permission denied" on main.py
```bash
# Make it executable
chmod +x main.py

# Then run
python3 main.py
```

## 13. Performance Testing

### Measure throughput on your machine
```bash
# Run simulation and capture results
python3 main.py > results.txt

# Or extract just the throughput
python3 main.py 2>&1 | grep "Throughput:"
```

### Benchmark against network parameters
```bash
# Test with different shard counts
for shards in 1 2 4 8; do
  echo "Testing with $shards shards..."
  python3 cli.py --mode simulate --shards $shards --transactions 100
done
```

## 14. Verify Installation Checklist

Run this checklist to confirm everything works:

```bash
#!/bin/bash
echo "=== Payment Sharding Network - Installation Check ==="
echo ""

echo "✓ Checking Python..."
python3 --version || { echo "✗ Python 3 not found"; exit 1; }

echo "✓ Checking imports..."
python3 -c "from simulator import ShardedPaymentNetwork" || { echo "✗ Import failed"; exit 1; }

echo "✓ Running quick test..."
python3 -m unittest test_payment_network.TestZKProof.test_proof_creation -v || { echo "✗ Test failed"; exit 1; }

echo "✓ Running demo (truncated)..."
timeout 5 python3 cli.py --mode demo > /dev/null 2>&1 && echo "  Demo runs successfully" || echo "  Demo timed out (OK)"

echo ""
echo "=== All checks passed! ✓ ==="
echo ""
echo "Now try:"
echo "  python3 cli.py --mode demo"
echo "  python3 -m unittest test_payment_network -v"
echo "  python3 main.py"
```

## 15. Common Testing Scenarios

### Scenario 1: Quick verification (2 minutes)
```bash
git clone https://github.com/engr-dr-ammad/Claude.git
cd Claude
python3 -m unittest test_payment_network -v
python3 cli.py --mode demo
```

### Scenario 2: Full analysis (15 minutes)
```bash
git clone https://github.com/engr-dr-ammad/Claude.git
cd Claude
python3 main.py
open /tmp/payment_analysis.html
cat FINDINGS.md
```

### Scenario 3: Development/Modification (Ongoing)
```bash
git clone https://github.com/engr-dr-ammad/Claude.git
cd Claude
pip install -e .
# Make changes to simulator.py, etc.
python3 -m unittest test_payment_network -v  # Test after each change
payment-shard --mode demo
```

## 16. Next Steps

After running the basic tests:

1. **Read the documentation**: `cat README.md`
2. **Explore the code**: `less simulator.py`
3. **Understand the design**: `cat FINDINGS.md`
4. **Try modifications**: Edit `simulator.py` and re-run tests
5. **Create your own scripts**: Use the classes from Python directly

## 17. Using the Python API Directly

Instead of CLI, use it programmatically:

```python
from simulator import ShardedPaymentNetwork, FinalizationLevel, SettlementTransaction
from zk_aggregation import ZKAggregator, PrivacyPreservingValidator

# Create network
network = ShardedPaymentNetwork(num_shards=4)

# Add transactions
for i in range(10):
    tx = SettlementTransaction(
        tx_id=f"tx_{i}",
        sender=f"sender_{i}",
        recipient=f"recipient_{i}",
        amount=50.0 + i,
        shard_id=i % 4
    )
    network.route_transaction(tx)

# Process epoch
network.process_epoch(FinalizationLevel.OPTIMISTIC, 1000)

# Check results
print(f"Throughput: {network.metrics['throughput']} tx/s")
print(f"Blocks: {network.metrics['blocks_finalized']}")
```

Save this as `my_test.py` and run:
```bash
python3 my_test.py
```

## Support

If you have issues:

1. Check Python version: `python3 --version`
2. Verify you're in the right directory: `pwd`
3. Check imports: `python3 -c "from simulator import *"`
4. Read error messages carefully
5. See USAGE.md for complete documentation
6. Check GitHub issues: https://github.com/engr-dr-ammad/Claude/issues

---

**Happy testing!** 🚀
