"""
ShardIoT reframed for payments: Throughput, finality, and ZK privacy trade-offs.
Simulates a sharded settlement network with privacy-preserving transaction validation.

Based on:
[1] A. Aslam, O. Postolache, S. Oliveira, and J. M. Dias Pereira,
    "Securing IoT sensors using sharding-based blockchain network technology
    integration: A systematic review," Sensors, vol. 25, no. 3, p. 807, Jan. 2025.
    DOI: 10.3390/s25030807 (Open access, MDPI)
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import random
import hashlib


class FinalizationLevel(Enum):
    """Trade-offs between throughput and finality."""
    OPTIMISTIC = 1  # Fast but needs challenge period
    PROBABILISTIC = 2  # Medium finality after k blocks
    DETERMINISTIC = 3  # Full finality but slower


@dataclass
class ZKProof:
    """Zero-knowledge proof for transaction validation."""
    commitment: str  # Pedersen commitment of transaction
    range_proof: str  # Proof amount is within valid range
    nullifier: str  # Prevent double-spend (can't link to transaction)
    timestamp: int
    shard_id: int

    def __hash__(self):
        return hash((self.commitment, self.range_proof, self.nullifier))


@dataclass
class SettlementTransaction:
    """Payment transaction with optional privacy."""
    tx_id: str
    sender: str
    recipient: str
    amount: float
    shard_id: int
    is_private: bool = False
    zk_proof: ZKProof = None
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))

    def __hash__(self):
        return hash(self.tx_id)


@dataclass
class Block:
    """Block in a shard."""
    block_num: int
    shard_id: int
    transactions: list[SettlementTransaction]
    parent_hash: str
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    merkle_root: str = ""

    def __post_init__(self):
        self.merkle_root = self._compute_merkle_root()

    def _compute_merkle_root(self) -> str:
        if not self.transactions:
            return hashlib.sha256(b"empty").hexdigest()
        tx_hashes = [hashlib.sha256(str(tx.tx_id).encode()).hexdigest() for tx in self.transactions]
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2:
                tx_hashes.append(tx_hashes[-1])
            tx_hashes = [
                hashlib.sha256((tx_hashes[i] + tx_hashes[i+1]).encode()).hexdigest()
                for i in range(0, len(tx_hashes), 2)
            ]
        return tx_hashes[0]

    def hash(self) -> str:
        content = f"{self.block_num}{self.shard_id}{self.merkle_root}{self.parent_hash}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class Shard:
    """Individual shard with its own transaction processing."""
    shard_id: int
    blocks: list[Block] = field(default_factory=list)
    pending_txs: list[SettlementTransaction] = field(default_factory=list)
    validator_set: set[str] = field(default_factory=set)
    zk_proofs: dict[str, ZKProof] = field(default_factory=dict)

    def add_transaction(self, tx: SettlementTransaction):
        """Queue transaction for processing."""
        self.pending_txs.append(tx)
        if tx.is_private and tx.zk_proof:
            self.zk_proofs[tx.tx_id] = tx.zk_proof

    def finalize_block(self, finalization: FinalizationLevel) -> Block:
        """Create and finalize a block based on finalization level."""
        parent_hash = self.blocks[-1].hash() if self.blocks else "genesis"
        block_num = len(self.blocks)

        if finalization == FinalizationLevel.OPTIMISTIC:
            # Include all pending, finalize immediately
            block = Block(block_num, self.shard_id, self.pending_txs.copy(), parent_hash)
        elif finalization == FinalizationLevel.PROBABILISTIC:
            # Include up to 50% of pending (conservative)
            txs = self.pending_txs[:max(1, len(self.pending_txs) // 2)]
            block = Block(block_num, self.shard_id, txs, parent_hash)
        else:  # DETERMINISTIC
            # Single tx per block for absolute finality
            txs = self.pending_txs[:1] if self.pending_txs else []
            block = Block(block_num, self.shard_id, txs, parent_hash)

        self.blocks.append(block)
        self.pending_txs = self.pending_txs[len(block.transactions):]
        return block

    def verify_privacy(self) -> int:
        """Count successfully verified private transactions."""
        verified = 0
        for tx in self.blocks[-1].transactions if self.blocks else []:
            if tx.is_private and tx.tx_id in self.zk_proofs:
                # Verify ZK proof (simplified check)
                proof = self.zk_proofs[tx.tx_id]
                if proof.commitment and proof.nullifier and proof.range_proof:
                    verified += 1
        return verified


class ShardedPaymentNetwork:
    """Multi-shard payment settlement with privacy and finality trade-offs."""

    def __init__(self, num_shards: int = 4):
        self.num_shards = num_shards
        self.shards = [Shard(shard_id=i) for i in range(num_shards)]
        self.cross_shard_queue = defaultdict(list)
        self.metrics = {
            'total_txs': 0,
            'blocks_finalized': 0,
            'private_txs': 0,
            'zk_verified': 0,
            'throughput': 0,
            'finality_time_ms': 0,
        }

    def route_transaction(self, tx: SettlementTransaction):
        """Route transaction to appropriate shard."""
        shard = self.shards[tx.shard_id % self.num_shards]
        shard.add_transaction(tx)
        self.metrics['total_txs'] += 1
        if tx.is_private:
            self.metrics['private_txs'] += 1

    def generate_zk_proof(self, tx: SettlementTransaction) -> ZKProof:
        """Generate ZK proof for private transaction."""
        commitment = hashlib.sha256(
            f"{tx.sender}{tx.recipient}{tx.amount}".encode()
        ).hexdigest()[:16]
        range_proof = hashlib.sha256(
            f"{tx.amount}".encode()
        ).hexdigest()[:16]
        nullifier = hashlib.sha256(
            f"{tx.tx_id}{tx.timestamp}".encode()
        ).hexdigest()[:16]

        return ZKProof(
            commitment=commitment,
            range_proof=range_proof,
            nullifier=nullifier,
            timestamp=tx.timestamp,
            shard_id=tx.shard_id
        )

    def process_epoch(self, finalization: FinalizationLevel, duration_ms: int):
        """Process one epoch with specified finalization level."""
        epoch_start = time.time()
        blocks_this_epoch = 0

        for shard in self.shards:
            if shard.pending_txs:
                block = shard.finalize_block(finalization)
                blocks_this_epoch += 1
                zk_verified = shard.verify_privacy()
                self.metrics['zk_verified'] += zk_verified
                self.metrics['blocks_finalized'] += 1

        epoch_time = (time.time() - epoch_start) * 1000
        self.metrics['finality_time_ms'] = epoch_time

        total_pending = sum(len(s.pending_txs) for s in self.shards)
        processed = self.metrics['total_txs'] - total_pending
        self.metrics['throughput'] = processed / (duration_ms / 1000) if duration_ms > 0 else 0

    def simulate_workload(self, num_txs: int, finalization: FinalizationLevel,
                         private_ratio: float = 0.3, duration_sec: float = 10.0):
        """Simulate payment traffic with privacy."""
        print(f"\n{'='*60}")
        print(f"Finalization: {finalization.name} | Transactions: {num_txs} | Private: {int(num_txs * private_ratio)}")
        print(f"{'='*60}")

        start_time = time.time()
        tx_ids_generated = 0

        while tx_ids_generated < num_txs and (time.time() - start_time) < duration_sec:
            # Generate transactions
            batch_size = min(50, num_txs - tx_ids_generated)
            for _ in range(batch_size):
                tx_id = f"tx_{int(time.time()*1000)}_{random.randint(0, 9999)}"
                is_private = random.random() < private_ratio
                shard_id = random.randint(0, self.num_shards - 1)

                tx = SettlementTransaction(
                    tx_id=tx_id,
                    sender=f"addr_{random.randint(1000, 9999)}",
                    recipient=f"addr_{random.randint(1000, 9999)}",
                    amount=round(random.uniform(0.1, 100.0), 2),
                    shard_id=shard_id,
                    is_private=is_private
                )

                if is_private:
                    tx.zk_proof = self.generate_zk_proof(tx)

                self.route_transaction(tx)
                tx_ids_generated += 1

            # Process epoch
            duration_ms = (time.time() - start_time) * 1000
            self.process_epoch(finalization, duration_ms)

            # Brief pause between batches
            time.sleep(0.01)

        return self._get_results(finalization)

    def _get_results(self, finalization: FinalizationLevel) -> dict:
        """Compute summary statistics."""
        total_pending = sum(len(s.pending_txs) for s in self.shards)
        total_processed = self.metrics['total_txs'] - total_pending

        return {
            'finalization': finalization.name,
            'total_transactions': self.metrics['total_txs'],
            'processed': total_processed,
            'pending': total_pending,
            'throughput_tps': self.metrics['throughput'],
            'blocks_finalized': self.metrics['blocks_finalized'],
            'private_transactions': self.metrics['private_txs'],
            'zk_verified': self.metrics['zk_verified'],
            'finality_latency_ms': self.metrics['finality_time_ms'],
            'privacy_ratio': (self.metrics['zk_verified'] / self.metrics['private_txs'] * 100)
                            if self.metrics['private_txs'] > 0 else 0,
            'shards': self.num_shards,
        }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PAYMENT SHARDING NETWORK SIMULATOR")
    print("Settlement transactions with ZK privacy and finality trade-offs")
    print("="*70)

    results = []

    # Test each finalization level
    for finalization in [FinalizationLevel.OPTIMISTIC,
                        FinalizationLevel.PROBABILISTIC,
                        FinalizationLevel.DETERMINISTIC]:
        network = ShardedPaymentNetwork(num_shards=4)
        result = network.simulate_workload(
            num_txs=500,
            finalization=finalization,
            private_ratio=0.35,
            duration_sec=8.0
        )
        results.append(result)

        print(f"\nResults Summary:")
        print(f"  Throughput: {result['throughput_tps']:.2f} tx/s")
        print(f"  Blocks finalized: {result['blocks_finalized']}")
        print(f"  Private transactions: {result['private_transactions']}")
        print(f"  ZK verified: {result['zk_verified']} ({result['privacy_ratio']:.1f}%)")
        print(f"  Finality latency: {result['finality_latency_ms']:.2f} ms")

    # Save results for visualization
    import json
    with open('/tmp/payment_simulation_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*70)
    print("Results saved to /tmp/payment_simulation_results.json")
    print("="*70)
