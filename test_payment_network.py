"""
Unit tests for payment sharding network with ZK privacy.
"""

import unittest
from simulator import (
    SettlementTransaction, Block, Shard, ShardedPaymentNetwork,
    FinalizationLevel, ZKProof
)
from zk_aggregation import ZKAggregator, PrivacyPreservingValidator
import hashlib
import random


class TestZKProof(unittest.TestCase):
    """Test zero-knowledge proof generation."""

    def test_proof_creation(self):
        """ZK proof should have all required fields."""
        proof = ZKProof(
            commitment="abc123",
            range_proof="def456",
            nullifier="ghi789",
            timestamp=1000,
            shard_id=0
        )
        self.assertEqual(proof.commitment, "abc123")
        self.assertEqual(proof.range_proof, "def456")
        self.assertEqual(proof.nullifier, "ghi789")
        self.assertTrue(hasattr(proof, 'timestamp'))
        self.assertTrue(hasattr(proof, 'shard_id'))

    def test_proof_hash(self):
        """ZK proofs should be hashable."""
        proof1 = ZKProof("c1", "r1", "n1", 1000, 0)
        proof2 = ZKProof("c1", "r1", "n1", 1000, 0)
        self.assertEqual(hash(proof1), hash(proof2))


class TestSettlementTransaction(unittest.TestCase):
    """Test settlement transaction creation and validation."""

    def test_transaction_creation(self):
        """Transaction should be created with all fields."""
        tx = SettlementTransaction(
            tx_id="tx_001",
            sender="addr_1000",
            recipient="addr_2000",
            amount=50.0,
            shard_id=0
        )
        self.assertEqual(tx.tx_id, "tx_001")
        self.assertEqual(tx.amount, 50.0)
        self.assertFalse(tx.is_private)
        self.assertIsNone(tx.zk_proof)

    def test_private_transaction(self):
        """Private transactions should have ZK proofs."""
        proof = ZKProof("c", "r", "n", 1000, 0)
        tx = SettlementTransaction(
            tx_id="tx_private_001",
            sender="addr_1000",
            recipient="addr_2000",
            amount=50.0,
            shard_id=0,
            is_private=True,
            zk_proof=proof
        )
        self.assertTrue(tx.is_private)
        self.assertIsNotNone(tx.zk_proof)
        self.assertEqual(tx.zk_proof.commitment, "c")

    def test_transaction_hashable(self):
        """Transactions should be hashable."""
        tx1 = SettlementTransaction("tx_1", "a", "b", 10, 0)
        tx2 = SettlementTransaction("tx_1", "a", "b", 10, 0)
        self.assertEqual(hash(tx1), hash(tx2))


class TestBlock(unittest.TestCase):
    """Test block creation and merkle root calculation."""

    def test_empty_block(self):
        """Empty block should have valid merkle root."""
        block = Block(
            block_num=0,
            shard_id=0,
            transactions=[],
            parent_hash="genesis"
        )
        self.assertEqual(block.block_num, 0)
        self.assertIsNotNone(block.merkle_root)
        self.assertNotEqual(block.merkle_root, "")

    def test_block_with_transactions(self):
        """Block with transactions should compute merkle root."""
        tx1 = SettlementTransaction("tx_1", "a", "b", 10, 0)
        tx2 = SettlementTransaction("tx_2", "c", "d", 20, 0)
        block = Block(
            block_num=1,
            shard_id=0,
            transactions=[tx1, tx2],
            parent_hash="hash_0"
        )
        self.assertEqual(len(block.transactions), 2)
        self.assertIsNotNone(block.merkle_root)
        # Same transactions should produce same merkle root
        block2 = Block(1, 0, [tx1, tx2], "hash_0")
        self.assertEqual(block.merkle_root, block2.merkle_root)

    def test_block_hash(self):
        """Block hash should be deterministic."""
        tx = SettlementTransaction("tx_1", "a", "b", 10, 0)
        block1 = Block(1, 0, [tx], "hash_0")
        block2 = Block(1, 0, [tx], "hash_0")
        self.assertEqual(block1.hash(), block2.hash())


class TestShard(unittest.TestCase):
    """Test shard processing and finalization."""

    def test_shard_creation(self):
        """Shard should initialize with empty state."""
        shard = Shard(shard_id=0)
        self.assertEqual(shard.shard_id, 0)
        self.assertEqual(len(shard.blocks), 0)
        self.assertEqual(len(shard.pending_txs), 0)

    def test_add_transaction(self):
        """Transactions should be added to pending queue."""
        shard = Shard(shard_id=0)
        tx = SettlementTransaction("tx_1", "a", "b", 10, 0)
        shard.add_transaction(tx)
        self.assertEqual(len(shard.pending_txs), 1)
        self.assertEqual(shard.pending_txs[0].tx_id, "tx_1")

    def test_finalize_optimistic_block(self):
        """Optimistic finalization should include all pending."""
        shard = Shard(shard_id=0)
        for i in range(5):
            tx = SettlementTransaction(f"tx_{i}", "a", "b", 10, 0)
            shard.add_transaction(tx)

        block = shard.finalize_block(FinalizationLevel.OPTIMISTIC)
        self.assertEqual(len(block.transactions), 5)
        self.assertEqual(len(shard.pending_txs), 0)

    def test_finalize_probabilistic_block(self):
        """Probabilistic finalization should include ~50%."""
        shard = Shard(shard_id=0)
        for i in range(10):
            tx = SettlementTransaction(f"tx_{i}", "a", "b", 10, 0)
            shard.add_transaction(tx)

        block = shard.finalize_block(FinalizationLevel.PROBABILISTIC)
        # Should include roughly 50%
        self.assertGreater(len(block.transactions), 0)
        self.assertLess(len(block.transactions), 10)

    def test_finalize_deterministic_block(self):
        """Deterministic finalization should include single tx."""
        shard = Shard(shard_id=0)
        for i in range(5):
            tx = SettlementTransaction(f"tx_{i}", "a", "b", 10, 0)
            shard.add_transaction(tx)

        block = shard.finalize_block(FinalizationLevel.DETERMINISTIC)
        self.assertLessEqual(len(block.transactions), 1)


class TestShardedPaymentNetwork(unittest.TestCase):
    """Test multi-shard network operations."""

    def test_network_creation(self):
        """Network should create correct number of shards."""
        network = ShardedPaymentNetwork(num_shards=4)
        self.assertEqual(len(network.shards), 4)
        self.assertEqual(network.num_shards, 4)

    def test_route_transaction(self):
        """Transactions should be routed to correct shard."""
        network = ShardedPaymentNetwork(num_shards=4)
        tx = SettlementTransaction("tx_1", "a", "b", 10, shard_id=2)
        network.route_transaction(tx)
        self.assertEqual(network.metrics['total_txs'], 1)

    def test_generate_zk_proof(self):
        """Network should generate valid ZK proofs."""
        network = ShardedPaymentNetwork(num_shards=4)
        tx = SettlementTransaction("tx_1", "a", "b", 10, shard_id=0)
        proof = network.generate_zk_proof(tx)

        self.assertIsNotNone(proof.commitment)
        self.assertIsNotNone(proof.range_proof)
        self.assertIsNotNone(proof.nullifier)
        self.assertEqual(proof.shard_id, 0)

    def test_process_epoch_optimistic(self):
        """Epoch processing should work for optimistic finalization."""
        network = ShardedPaymentNetwork(num_shards=4)
        for i in range(10):
            tx = SettlementTransaction(f"tx_{i}", "a", "b", 10, shard_id=i % 4)
            network.route_transaction(tx)

        network.process_epoch(FinalizationLevel.OPTIMISTIC, 1000)
        self.assertGreater(network.metrics['blocks_finalized'], 0)


class TestZKAggregator(unittest.TestCase):
    """Test zero-knowledge proof aggregation."""

    def test_aggregator_creation(self):
        """Aggregator should initialize."""
        agg = ZKAggregator()
        self.assertEqual(agg.stats['total_proofs'], 0)
        self.assertEqual(agg.stats['aggregated_proofs'], 0)

    def test_add_proof(self):
        """Proofs should be added to aggregator."""
        agg = ZKAggregator()
        proof = ZKProof("c", "r", "n1", 1000, 0)
        agg.add_proof("tx_1", proof)
        self.assertEqual(agg.stats['total_proofs'], 1)

    def test_aggregate_batch(self):
        """Batch of proofs should aggregate to single proof."""
        agg = ZKAggregator()
        proofs = [
            ZKProof(f"c{i}", f"r{i}", f"n{i}", 1000, 0)
            for i in range(32)
        ]
        agg_proof = agg.aggregate_batch(proofs, "batch_0")
        self.assertIsNotNone(agg_proof)
        self.assertEqual(agg_proof.num_proofs, 32)
        self.assertEqual(agg_proof.verified_count, 32)

    def test_verify_aggregate(self):
        """Valid aggregate should verify."""
        agg = ZKAggregator()
        proofs = [
            ZKProof(f"c{i}", f"r{i}", f"n{i}", 1000, 0)
            for i in range(10)
        ]
        agg_proof = agg.aggregate_batch(proofs, "batch_0")
        self.assertTrue(agg.verify_aggregate(agg_proof))

    def test_compression_stats(self):
        """Aggregator should report compression statistics."""
        agg = ZKAggregator()
        proofs = [ZKProof(f"c{i}", f"r{i}", f"n{i}", 1000, 0) for i in range(32)]
        for i in range(len(proofs)):
            agg.add_proof(f"tx_{i}", proofs[i])
        agg.aggregate_batch(proofs, "batch_0")

        stats = agg.get_compression_stats()
        self.assertIn('aggregated_batches', stats)
        self.assertGreater(stats['compression_gained'], 0)


class TestPrivacyPreservingValidator(unittest.TestCase):
    """Test private transaction validation."""

    def test_validator_creation(self):
        """Validator should initialize with aggregator."""
        agg = ZKAggregator()
        validator = PrivacyPreservingValidator(agg)
        self.assertEqual(len(validator.validation_log), 0)

    def test_validate_batch(self):
        """Validator should validate batch of private transactions."""
        agg = ZKAggregator()
        validator = PrivacyPreservingValidator(agg)

        txs = []
        for i in range(5):
            tx = SettlementTransaction(f"tx_{i}", "a", "b", 10, 0, is_private=True)
            tx.zk_proof = ZKProof(f"c{i}", f"r{i}", f"n{i}", 1000, 0)
            txs.append(tx)

        result = validator.validate_private_tx_batch(txs, "batch_0")
        self.assertTrue(result['valid'])
        self.assertEqual(result['proofs_aggregated'], 5)

    def test_privacy_report(self):
        """Validator should generate privacy report."""
        agg = ZKAggregator()
        validator = PrivacyPreservingValidator(agg)

        for batch_num in range(3):
            txs = []
            for i in range(8):
                tx = SettlementTransaction(
                    f"tx_{batch_num}_{i}", "a", "b", 10, 0, is_private=True
                )
                tx.zk_proof = ZKProof(f"c{i}", f"r{i}", f"n{i}", 1000, 0)
                txs.append(tx)
            validator.validate_private_tx_batch(txs, f"batch_{batch_num}")

        report = validator.get_privacy_report()
        self.assertEqual(report['total_batches_validated'], 3)
        self.assertGreater(report['successful_validations'], 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete system."""

    def test_full_simulation_optimistic(self):
        """Full simulation with optimistic finalization."""
        network = ShardedPaymentNetwork(num_shards=2)

        # Generate transactions
        for i in range(20):
            tx = SettlementTransaction(
                f"tx_{i}", f"addr_{1000+i}", f"addr_{2000+i}",
                amount=random.uniform(1, 100),
                shard_id=i % 2,
                is_private=(i % 3 == 0)
            )
            if tx.is_private:
                tx.zk_proof = network.generate_zk_proof(tx)
            network.route_transaction(tx)

        # Process epoch
        network.process_epoch(FinalizationLevel.OPTIMISTIC, 1000)

        # Verify results
        self.assertGreater(network.metrics['blocks_finalized'], 0)
        self.assertGreater(network.metrics['throughput'], 0)

    def test_full_simulation_all_levels(self):
        """Run simulation for all finalization levels."""
        results = []
        for finalization in [FinalizationLevel.OPTIMISTIC,
                            FinalizationLevel.PROBABILISTIC,
                            FinalizationLevel.DETERMINISTIC]:
            network = ShardedPaymentNetwork(num_shards=2)

            for i in range(50):
                tx = SettlementTransaction(
                    f"tx_{i}", f"addr_{1000+i}", f"addr_{2000+i}",
                    amount=random.uniform(1, 100),
                    shard_id=i % 2
                )
                network.route_transaction(tx)

            network.process_epoch(finalization, 5000)
            results.append({
                'finalization': finalization.name,
                'throughput': network.metrics['throughput'],
                'blocks': network.metrics['blocks_finalized']
            })

        # Optimistic should have highest throughput
        opt = [r for r in results if r['finalization'] == 'OPTIMISTIC'][0]
        det = [r for r in results if r['finalization'] == 'DETERMINISTIC'][0]
        self.assertGreater(opt['throughput'], det['throughput'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
