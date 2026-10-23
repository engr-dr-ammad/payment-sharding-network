#!/usr/bin/env python3
"""
Command-line interface for Payment Sharding Network.
Interactive demo and testing tool.
"""

import sys
import json
import argparse
from typing import Optional
from simulator import ShardedPaymentNetwork, FinalizationLevel, SettlementTransaction
from zk_aggregation import ZKAggregator, PrivacyPreservingValidator


class PaymentShardingCLI:
    """Interactive CLI for payment sharding network."""

    def __init__(self):
        self.network: Optional[ShardedPaymentNetwork] = None
        self.validator: Optional[PrivacyPreservingValidator] = None

    def init_network(self, num_shards: int = 4) -> None:
        """Initialize a new payment network."""
        self.network = ShardedPaymentNetwork(num_shards=num_shards)
        aggregator = ZKAggregator()
        self.validator = PrivacyPreservingValidator(aggregator)
        print(f"✓ Initialized payment network with {num_shards} shards")

    def create_transaction(self, sender: str, recipient: str, amount: float,
                          shard_id: int, is_private: bool = False) -> None:
        """Create and route a settlement transaction."""
        if not self.network:
            print("❌ Network not initialized. Run 'init' first.")
            return

        tx = SettlementTransaction(
            tx_id=f"tx_{int(__import__('time').time() * 1000)}",
            sender=sender,
            recipient=recipient,
            amount=amount,
            shard_id=min(shard_id, self.network.num_shards - 1),
            is_private=is_private
        )

        if is_private:
            tx.zk_proof = self.network.generate_zk_proof(tx)

        self.network.route_transaction(tx)
        status = "🔐 Private" if is_private else "📤 Public"
        print(f"✓ {status} transaction: {sender[:8]}... → {recipient[:8]}... ({amount} EUR)")

    def process_epoch(self, finalization_name: str) -> dict:
        """Process one epoch with specified finalization."""
        if not self.network:
            print("❌ Network not initialized.")
            return {}

        try:
            finalization = FinalizationLevel[finalization_name.upper()]
        except KeyError:
            print(f"❌ Invalid finalization: {finalization_name}")
            print(f"   Options: {', '.join([f.name for f in FinalizationLevel])}")
            return {}

        self.network.process_epoch(finalization, 1000)
        result = self.network._get_results(finalization)

        print(f"\n📊 Epoch Results ({finalization.name}):")
        print(f"  ├─ Throughput: {result['throughput_tps']:.2f} tx/s")
        print(f"  ├─ Blocks finalized: {result['blocks_finalized']}")
        print(f"  ├─ Transactions processed: {result['processed']}/{result['total_transactions']}")
        print(f"  ├─ Privacy coverage: {result['privacy_ratio']:.1f}%")
        print(f"  └─ Finality latency: {result['finality_latency_ms']:.2f} ms\n")

        return result

    def show_network_status(self) -> None:
        """Display network status."""
        if not self.network:
            print("❌ Network not initialized.")
            return

        print(f"\n📡 Network Status:")
        print(f"  ├─ Shards: {self.network.num_shards}")
        print(f"  ├─ Total transactions: {self.network.metrics['total_txs']}")
        print(f"  ├─ Private transactions: {self.network.metrics['private_txs']}")
        print(f"  ├─ Blocks finalized: {self.network.metrics['blocks_finalized']}")
        print(f"  └─ ZK verified: {self.network.metrics['zk_verified']}\n")

        for i, shard in enumerate(self.network.shards):
            pending = len(shard.pending_txs)
            blocks = len(shard.blocks)
            print(f"  Shard {i}: {blocks} blocks, {pending} pending txs")

    def simulate_workload(self, num_txs: int, finalization: str,
                         private_ratio: float = 0.3) -> dict:
        """Run a complete workload simulation."""
        if not self.network:
            self.init_network()

        try:
            fin = FinalizationLevel[finalization.upper()]
        except KeyError:
            print(f"❌ Invalid finalization level: {finalization}")
            return {}

        print(f"\n{'='*60}")
        print(f"Simulating {num_txs} transactions")
        print(f"Finalization: {fin.name}")
        print(f"Privacy ratio: {private_ratio:.0%}")
        print(f"{'='*60}\n")

        return self.network.simulate_workload(
            num_txs=num_txs,
            finalization=fin,
            private_ratio=private_ratio,
            duration_sec=10.0
        )

    def demo(self) -> None:
        """Run an interactive demo."""
        print("\n" + "="*70)
        print("PAYMENT SHARDING NETWORK - INTERACTIVE DEMO")
        print("="*70 + "\n")

        self.init_network(num_shards=4)

        # Generate sample transactions
        print("1. Creating sample transactions...\n")
        senders = ["alice", "bob", "charlie", "diana"]
        recipients = ["eve", "frank", "grace", "henry"]

        for i in range(12):
            sender = senders[i % len(senders)]
            recipient = recipients[i % len(recipients)]
            amount = 10 + (i * 5)
            is_private = (i % 3 == 0)
            self.create_transaction(sender, recipient, amount, i % 4, is_private)

        # Show network status
        print("\n2. Network Status:")
        self.show_network_status()

        # Process epochs with different finalization levels
        print("3. Processing Epochs with Different Finalization Levels:\n")
        results = []
        for finalization in ["optimistic", "probabilistic", "deterministic"]:
            self.init_network(num_shards=4)
            # Re-populate transactions
            for i in range(12):
                sender = senders[i % len(senders)]
                recipient = recipients[i % len(recipients)]
                amount = 10 + (i * 5)
                is_private = (i % 3 == 0)
                self.create_transaction(sender, recipient, amount, i % 4, is_private)

            result = self.process_epoch(finalization)
            results.append(result)

        # Summary
        print("\n" + "="*70)
        print("SUMMARY: Trade-off Analysis")
        print("="*70 + "\n")

        if results:
            opt = [r for r in results if r.get('finalization') == 'OPTIMISTIC'][0] if results else {}
            prob = [r for r in results if r.get('finalization') == 'PROBABILISTIC'][0] if len(results) > 1 else {}
            det = [r for r in results if r.get('finalization') == 'DETERMINISTIC'][0] if len(results) > 2 else {}

            print("Throughput Ranking:")
            print(f"  🥇 Optimistic:   {opt.get('throughput_tps', 0):.0f} tx/s")
            if prob:
                print(f"  🥈 Probabilistic: {prob.get('throughput_tps', 0):.0f} tx/s")
            if det:
                print(f"  🥉 Deterministic: {det.get('throughput_tps', 0):.0f} tx/s")

    def interactive_mode(self) -> None:
        """Run interactive command mode."""
        print("\n" + "="*70)
        print("PAYMENT SHARDING CLI - Interactive Mode")
        print("Type 'help' for available commands")
        print("="*70 + "\n")

        self.init_network()

        while True:
            try:
                cmd = input("payment-shard> ").strip().lower()

                if not cmd:
                    continue
                elif cmd == "help":
                    self._show_help()
                elif cmd == "status":
                    self.show_network_status()
                elif cmd == "demo":
                    self.demo()
                elif cmd.startswith("tx "):
                    # Format: tx sender recipient amount shard [private]
                    parts = cmd.split()
                    if len(parts) >= 5:
                        sender, recipient, amount, shard = parts[1:5]
                        is_private = len(parts) > 5 and parts[5] == "private"
                        try:
                            self.create_transaction(sender, recipient, float(amount),
                                                  int(shard), is_private)
                        except ValueError:
                            print("❌ Invalid transaction parameters")
                    else:
                        print("Usage: tx <sender> <recipient> <amount> <shard> [private]")
                elif cmd.startswith("epoch "):
                    finalization = cmd.split()[1] if len(cmd.split()) > 1 else "probabilistic"
                    self.process_epoch(finalization)
                elif cmd.startswith("simulate "):
                    parts = cmd.split()
                    if len(parts) >= 3:
                        try:
                            num_txs = int(parts[1])
                            finalization = parts[2]
                            private_ratio = float(parts[3]) if len(parts) > 3 else 0.3
                            self.simulate_workload(num_txs, finalization, private_ratio)
                        except ValueError:
                            print("❌ Invalid parameters")
                    else:
                        print("Usage: simulate <num_txs> <finalization> [private_ratio]")
                elif cmd == "exit" or cmd == "quit":
                    print("👋 Goodbye!")
                    break
                else:
                    print(f"Unknown command: {cmd}. Type 'help' for options.")

            except KeyboardInterrupt:
                print("\n👋 Interrupted. Type 'exit' to quit.")
            except Exception as e:
                print(f"❌ Error: {e}")

    def _show_help(self) -> None:
        """Show available commands."""
        print("""
Available Commands:

  help                                    Show this help message
  status                                  Show network status
  demo                                    Run interactive demo

  tx <sender> <recipient> <amount> <shard> [private]
                                          Create a transaction
                                          Example: tx alice bob 50 0 private

  epoch <finalization>                    Process one epoch
                                          Options: optimistic, probabilistic, deterministic
                                          Example: epoch probabilistic

  simulate <num_txs> <finalization> [ratio]
                                          Simulate workload
                                          Example: simulate 100 optimistic 0.3

  exit, quit                              Exit the program

Examples:
  > tx alice bob 50 0
  > tx charlie diana 100 1 private
  > epoch optimistic
  > status
  > simulate 500 probabilistic 0.35
""")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Payment Sharding Network with ZK Privacy"
    )
    parser.add_argument(
        "--mode", choices=["interactive", "demo", "simulate"],
        default="interactive",
        help="Run mode (default: interactive)"
    )
    parser.add_argument(
        "--shards", type=int, default=4,
        help="Number of shards (default: 4)"
    )
    parser.add_argument(
        "--transactions", type=int, default=500,
        help="Number of transactions for simulation (default: 500)"
    )
    parser.add_argument(
        "--finalization", choices=["optimistic", "probabilistic", "deterministic"],
        default="probabilistic",
        help="Finalization level for simulation (default: probabilistic)"
    )
    parser.add_argument(
        "--private-ratio", type=float, default=0.3,
        help="Ratio of private transactions (default: 0.3)"
    )

    args = parser.parse_args()

    cli = PaymentShardingCLI()

    if args.mode == "demo":
        cli.demo()
    elif args.mode == "simulate":
        cli.init_network(num_shards=args.shards)
        cli.simulate_workload(args.transactions, args.finalization, args.private_ratio)
    else:  # interactive
        cli.interactive_mode()


if __name__ == "__main__":
    main()
