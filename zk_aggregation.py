"""
Zero-knowledge proof aggregation for privacy-preserving payment validation.
Reuses aggregation techniques for batch verification and privacy guarantees.

Based on:
[1] A. Aslam, O. Postolache, S. Oliveira, and J. M. Dias Pereira,
    "Securing IoT sensors using sharding-based blockchain network technology
    integration: A systematic review," Sensors, vol. 25, no. 3, p. 807, Jan. 2025.
    DOI: 10.3390/s25030807 (Open access, MDPI)
[2] A. Aslam, O. Postolache, and S. Oliveira,
    "A blockchain-based decentralized secure data aggregation scheme with ZKP
    for WSNs," Proc. I4Tech2025, Pune, India, Sep. 2025, pp. 1–5.

Adapted from IoT sensor data aggregation to payment transaction privacy.
"""

import hashlib
from dataclasses import dataclass
from typing import List, Dict
import json


@dataclass
class AggregateProof:
    """Aggregated ZK proof for batch verification."""
    proof_id: str
    num_proofs: int
    root_commitment: str
    aggregate_nullifier_set: str
    timestamp: int
    verified_count: int = 0

    def to_dict(self) -> dict:
        return {
            'proof_id': self.proof_id,
            'num_proofs': self.num_proofs,
            'root_commitment': self.root_commitment,
            'verified_count': self.verified_count,
            'compression_ratio': f"{self.num_proofs / max(1, self.verified_count):.2f}x"
                                if self.verified_count > 0 else "0x"
        }


class ZKAggregator:
    """Aggregate multiple ZK proofs for efficient batch validation."""

    def __init__(self):
        self.proofs: Dict[str, AggregateProof] = {}
        self.batch_size = 32  # Number of proofs per aggregate
        self.stats = {
            'total_proofs': 0,
            'aggregated_proofs': 0,
            'unique_nullifiers': set(),
            'compression_achieved': 0,
        }

    def add_proof(self, tx_id: str, proof: 'ZKProof'):
        """Queue proof for aggregation."""
        self.stats['total_proofs'] += 1
        self.stats['unique_nullifiers'].add(proof.nullifier)

    def aggregate_batch(self, proofs: List, batch_id: str) -> AggregateProof:
        """Aggregate a batch of ZK proofs."""
        if not proofs:
            return None

        # Compute Merkle tree of commitments
        commitments = [p.commitment for p in proofs]
        root = self._merkle_tree_root(commitments)

        # Aggregate nullifiers to prevent double-spending
        nullifiers = [p.nullifier for p in proofs]
        nullifier_set_hash = hashlib.sha256(
            ''.join(sorted(nullifiers)).encode()
        ).hexdigest()

        aggregate = AggregateProof(
            proof_id=batch_id,
            num_proofs=len(proofs),
            root_commitment=root,
            aggregate_nullifier_set=nullifier_set_hash,
            timestamp=proofs[0].timestamp if proofs else 0,
            verified_count=len([p for p in proofs if p.commitment])
        )

        self.proofs[batch_id] = aggregate
        self.stats['aggregated_proofs'] += 1
        self.stats['compression_achieved'] += len(proofs) - 1

        return aggregate

    def _merkle_tree_root(self, items: List[str]) -> str:
        """Compute Merkle root for list of items."""
        if not items:
            return hashlib.sha256(b"empty").hexdigest()

        hashes = [hashlib.sha256(item.encode()).hexdigest() for item in items]
        while len(hashes) > 1:
            if len(hashes) % 2:
                hashes.append(hashes[-1])
            hashes = [
                hashlib.sha256((hashes[i] + hashes[i+1]).encode()).hexdigest()
                for i in range(0, len(hashes), 2)
            ]
        return hashes[0]

    def verify_aggregate(self, agg_proof: AggregateProof) -> bool:
        """Verify aggregated proof (simplified verification)."""
        return (agg_proof.root_commitment and
                agg_proof.aggregate_nullifier_set and
                agg_proof.verified_count > 0)

    def get_compression_stats(self) -> dict:
        """Statistics on ZK proof aggregation."""
        return {
            'total_proofs': self.stats['total_proofs'],
            'aggregated_batches': self.stats['aggregated_proofs'],
            'unique_nullifiers': len(self.stats['unique_nullifiers']),
            'compression_gained': self.stats['compression_achieved'],
            'average_batch_size': (
                self.stats['total_proofs'] / max(1, self.stats['aggregated_proofs'])
            ),
            'privacy_set_size': len(self.stats['unique_nullifiers']),
        }


class PrivacyAnalyzer:
    """Analyze privacy guarantees and anonymity sets."""

    @staticmethod
    def anonymity_set_size(num_transactions: int, num_proofs: int) -> float:
        """Estimate anonymity set from transaction pool."""
        if num_proofs == 0:
            return 1.0
        return num_transactions / num_proofs

    @staticmethod
    def privacy_budget(batch_size: int, epsilon: float = 0.5) -> float:
        """Differential privacy budget for batch."""
        # log(batch_size) privacy loss per ZK proof aggregation
        import math
        return math.log(batch_size + 1) if batch_size > 0 else 0

    @staticmethod
    def unlinkability_score(num_nullifiers: int, num_transactions: int) -> float:
        """Score from 0-1 for transaction unlinkability."""
        if num_transactions == 0:
            return 0.0
        # Each unique nullifier increases unlinkability
        return min(1.0, num_nullifiers / num_transactions)


class PrivacyPreservingValidator:
    """Validate transactions with privacy preservation."""

    def __init__(self, aggregator: ZKAggregator):
        self.aggregator = aggregator
        self.analyzer = PrivacyAnalyzer()
        self.validation_log: List[Dict] = []

    def validate_private_tx_batch(self, transactions: List, batch_id: str) -> dict:
        """Validate batch of private transactions."""
        zk_proofs = [tx.zk_proof for tx in transactions if tx.is_private and tx.zk_proof]

        if not zk_proofs:
            return {'valid': False, 'reason': 'no_proofs'}

        # Aggregate proofs
        agg_proof = self.aggregator.aggregate_batch(zk_proofs, batch_id)

        # Verify aggregate
        is_valid = self.aggregator.verify_aggregate(agg_proof)

        # Analyze privacy
        anonymity = self.analyzer.anonymity_set_size(len(transactions), len(zk_proofs))
        unlinkability = self.analyzer.unlinkability_score(
            len(self.aggregator.stats['unique_nullifiers']),
            len(transactions)
        )
        privacy_budget = self.analyzer.privacy_budget(len(zk_proofs))

        result = {
            'valid': is_valid,
            'batch_id': batch_id,
            'proofs_aggregated': len(zk_proofs),
            'anonymity_set': round(anonymity, 2),
            'unlinkability_score': round(unlinkability, 3),
            'privacy_budget_used': round(privacy_budget, 4),
            'compression_ratio': f"{len(zk_proofs)}:1" if agg_proof else "0:1",
        }

        self.validation_log.append(result)
        return result

    def get_privacy_report(self) -> dict:
        """Generate privacy analysis report."""
        if not self.validation_log:
            return {'error': 'no_validations'}

        return {
            'total_batches_validated': len(self.validation_log),
            'successful_validations': sum(1 for v in self.validation_log if v['valid']),
            'average_anonymity': round(
                sum(v.get('anonymity_set', 0) for v in self.validation_log) / len(self.validation_log), 2
            ),
            'average_unlinkability': round(
                sum(v.get('unlinkability_score', 0) for v in self.validation_log) / len(self.validation_log), 3
            ),
            'aggregation_compression': self.aggregator.get_compression_stats(),
        }


# Example usage and analysis
if __name__ == "__main__":
    from simulator import SettlementTransaction, ZKProof
    import random

    print("\n" + "="*70)
    print("ZK PRIVACY AGGREGATION FOR PAYMENT VALIDATION")
    print("="*70)

    aggregator = ZKAggregator()
    validator = PrivacyPreservingValidator(aggregator)

    # Simulate batches of transactions
    for batch_num in range(3):
        transactions = []
        for i in range(32):
            tx = SettlementTransaction(
                tx_id=f"tx_batch{batch_num}_{i}",
                sender=f"addr_{random.randint(1000, 9999)}",
                recipient=f"addr_{random.randint(1000, 9999)}",
                amount=round(random.uniform(1, 100), 2),
                shard_id=batch_num % 4,
                is_private=True
            )
            # Create ZK proof
            tx.zk_proof = ZKProof(
                commitment=hashlib.sha256(f"{tx.tx_id}".encode()).hexdigest()[:16],
                range_proof=hashlib.sha256(f"{tx.amount}".encode()).hexdigest()[:16],
                nullifier=hashlib.sha256(f"{tx.tx_id}_null".encode()).hexdigest()[:16],
                timestamp=tx.timestamp,
                shard_id=tx.shard_id
            )
            transactions.append(tx)

        result = validator.validate_private_tx_batch(transactions, f"batch_{batch_num}")

        print(f"\nBatch {batch_num} Validation:")
        for key, value in result.items():
            print(f"  {key}: {value}")

    # Final privacy report
    print("\n" + "="*70)
    print("PRIVACY ANALYSIS REPORT")
    print("="*70)
    report = validator.get_privacy_report()
    for section, data in report.items():
        if section != 'aggregation_compression':
            print(f"{section}: {data}")
        else:
            print(f"\n{section}:")
            for key, value in data.items():
                print(f"  {key}: {value}")
