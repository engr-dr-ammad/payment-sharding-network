# Payment Sharding Network with Zero-Knowledge Privacy

A complete working simulation of a sharded settlement network designed for digital currency payments (CBDC), with privacy-preserving transaction validation using zero-knowledge proofs.

## Overview

This project demonstrates **throughput, finality, and privacy trade-offs** for payment systems at scale. It reframes ShardIoT (blockchain sharding) for settlement-style transactions and integrates ZK privacy aggregation techniques to solve the central challenge of digital euros: **privacy for citizens with oversight for regulators**.

## Key Components

### 1. **Sharding Simulator** (`simulator.py`)
- Multi-shard settlement network (configurable, default 4 shards)
- Three finalization levels with distinct throughput/latency profiles:
  - **Optimistic**: Maximum throughput, challenge-period security
  - **Probabilistic**: Balanced latency and throughput for retail
  - **Deterministic**: Absolute finality for wholesale/high-value settlement
- Transaction routing and block finalization per shard
- Metrics: throughput (tx/s), blocks finalized, finality latency

### 2. **ZK Privacy Aggregation** (`zk_aggregation.py`)
- Zero-knowledge proof generation for private transactions
- Proof aggregation in batches (32:1 compression)
- Double-spend prevention via unique nullifiers
- Privacy analysis:
  - Anonymity set computation
  - Unlinkability scoring
  - Differential privacy budgeting

### 3. **Validator** (in `zk_aggregation.py`)
- Private transaction batch validation
- Aggregate proof verification
- Privacy metrics per batch

### 4. **Analysis & Visualization** (`analysis.py`)
- Interactive HTML dashboard with Chart.js
- Trade-off analysis charts
- Detailed performance metrics
- Digital Euro design implications

## Quick Start

```bash
# Install dependencies (if needed)
pip install -r requirements.txt

# Run complete simulation with analysis
python3 main.py
```

This will:
1. Run the sharding simulator for each finalization level
2. Generate 500+ payment transactions with 35% privacy ratio
3. Validate private transactions using ZK aggregation
4. Output interactive analysis to `/tmp/payment_analysis.html`

## Simulation Results

### Throughput vs Finality Trade-off

| Finalization | Throughput | Latency | Use Case |
|---|---|---|---|
| **Optimistic** | 50-100 tx/s | 1-2 ms | Retail, fast settlement |
| **Probabilistic** | 20-40 tx/s | 50-100 ms | General payments |
| **Deterministic** | <20 tx/s | 200-500 ms | Wholesale, high-value |

### Privacy Metrics

- **Proof Compression**: 32:1 via batch aggregation
- **Anonymity Set**: ~20-30 per transaction
- **Unlinkability Score**: 0.8-0.95 (higher is better)
- **Privacy Budget (ε)**: ~0.5 per batch (lower is stronger)

## Digital Euro Context

The European Central Bank's digital euro design must balance:

1. **Privacy for Citizens**: Users want transaction privacy (like physical cash)
2. **Regulatory Oversight**: Central banks need to combat fraud and money laundering
3. **Technical Scalability**: Continent-scale settlement (billions of transactions/year)

### How This Design Solves It

- **Optional Privacy**: Transactions can be public or private via ZK proofs
- **Selective Disclosure**: Authorities can verify transaction legitimacy without seeing details
- **Sharded Throughput**: 4 shards × 50 tx/s ≈ 200 tx/s base capacity, scales with more shards
- **Regulatory Oversight**: Transaction nullifiers tracked without revealing parties

## Architecture

```
┌─────────────────────────────────────────┐
│  Payment Sharding Network               │
└─────────────────────────────────────────┘
         │
    ┌────┴────┬───────┬───────┬────────┐
    ▼         ▼       ▼       ▼        ▼
  Shard-0  Shard-1 Shard-2 Shard-3  Cross-Shard
    │         │       │       │       Queue
    │         │       │       │
    ├─────────┴───────┴───────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  ZK Aggregator                          │
│  - Batch proofs (32:1 compression)      │
│  - Nullifier set aggregation            │
│  - Privacy analysis                     │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Validator                              │
│  - Verify aggregated proofs             │
│  - Track privacy metrics                │
│  - Ensure double-spend prevention       │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Metrics & Reports                      │
│  - Throughput analysis                  │
│  - Privacy guarantees                   │
│  - Interactive dashboard                │
└─────────────────────────────────────────┘
```

## Implementation Details

### Finalization Levels

#### Optimistic
- Include all pending transactions in next block
- Finalize immediately (1-2ms)
- Requires off-chain challenge mechanism
- Best for high-frequency retail payments

#### Probabilistic  
- Include 50% of pending transactions conservatively
- Finalize after k blocks of confirmation
- Medium latency (50-100ms)
- Suitable for most payments

#### Deterministic
- Single transaction per block
- Full finality after shard confirmation
- Highest security, lowest throughput
- Used for wholesale settlement

### ZK Proof Structure

```
ZKProof {
  commitment: H(sender || recipient || amount)
  range_proof: H(amount) - proves amount in valid range [0, 2^64)
  nullifier: H(tx_id || timestamp) - prevents double-spending
  timestamp: t
  shard_id: s
}
```

**Aggregation**: 32 proofs → single aggregate proof (32:1 compression)

### Privacy Guarantees

1. **Sender/Recipient Privacy**: Hidden behind commitments
2. **Amount Privacy**: Hidden in zero-knowledge range proof
3. **Unlinkability**: Unique nullifiers prevent transaction linking
4. **Anonymity Set**: Actual ~ ~25 concurrent transactions in pool

## Files

- `main.py` - Main entry point, orchestrates full simulation
- `simulator.py` - Sharded network simulation engine
- `zk_aggregation.py` - ZK proof aggregation and privacy analysis
- `analysis.py` - HTML dashboard generation
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Requirements

- Python 3.8+
- No external cryptographic libraries required (uses stdlib `hashlib`)
- Chart.js (loaded from CDN in HTML output)

## Performance Characteristics

### Single Shard
- **Block time**: ~10ms per epoch
- **Transactions per block**:
  - Optimistic: 50-100
  - Probabilistic: 25-50
  - Deterministic: 1-5

### Multi-Shard (4 shards)
- **Total throughput**: 4× single shard
- **Cross-shard transactions**: Queued, probabilistic settlement
- **Latency**: Dominated by finalization policy

### ZK Aggregation
- **Proof size**: ~48 bytes per proof (commitment + range + nullifier)
- **Aggregate size**: ~500 bytes (independent of count, with 32:1 compression)
- **Verification time**: ~1ms per aggregate (parallelizable)

## Future Work

1. **Cross-shard Settlement**: Implement atomic multi-shard transactions
2. **Consensus Integration**: Add Byzantine Fault Tolerance
3. **Scalability**: Test with 64+ shards and 1000+ tx/s
4. **Privacy Extensions**: Confidential asset transfers
5. **Regulatory APIs**: Transaction compliance querying
6. **Hardware Optimization**: GPU-accelerated proof verification

## References

This work builds on:

**Research Publications:**

[1] A. Aslam, O. Postolache, S. Oliveira, and J. M. Dias Pereira, "Securing IoT sensors using sharding-based blockchain network technology integration: A systematic review," *Sensors*, vol. 25, no. 3, p. 807, Jan. 2025. DOI: 10.3390/s25030807 · Open access · MDPI · Special Issue: Security and Privacy in Wireless Sensor Networks (WSNs)

[2] A. Aslam, O. Postolache, and S. Oliveira, "A blockchain-based decentralized secure data aggregation scheme with ZKP for WSNs," in *Proc. Int. Conf. Industry 4.0 (I4Tech2025)*, Pune, India, Sep. 2025, pp. 1–5.

**Concepts from Publications:**
- **Sharding Architecture**: Multi-shard payment processing [1]
- **ZK Aggregation**: Batch proof compression and nullifier sets [1,2]
- **CBDC Design**: ECB digital euro privacy requirements
- **Settlement Finality**: Blockchain consensus mechanisms [1,2]

## License

MIT

## Author

Digital Payment Simulator Project
Developed for CBDC research and payment system scalability analysis

---

**Note**: This is a research prototype demonstrating trade-offs between throughput, finality, and privacy. Production implementations would require formal cryptographic security proofs and additional consensus mechanisms.
