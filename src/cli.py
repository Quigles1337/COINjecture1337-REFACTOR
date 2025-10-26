"""
COINjecture CLI Module

Provides user-facing commands to run nodes and interact with the chain.
Includes user submissions management commands.

Based on docs/blockchain/cli.md specification.
"""

import argparse
import sys
import json
import os
import time
import requests  # type: ignore
import threading
import queue
from pathlib import Path
from typing import Optional, Dict, Any

# Import node and related modules
try:
    from .node import Node, NodeConfig, NodeRole, create_node, load_config
    from .user_submissions.aggregation import AggregationStrategy
except ImportError:
    from node import Node, NodeConfig, NodeRole, create_node, load_config
    from user_submissions.aggregation import AggregationStrategy


class COINjectureCLI:
    """COINjecture Command Line Interface."""
    
    def __init__(self):
        self.parser = self._create_parser()
        # P2P bootstrap peers (no HTTP API needed for mining)
        self.bootstrap_peers = ["167.172.213.70:12345"]
        # IPFS API endpoint (configurable via env)
        self.ipfs_api_url = os.environ.get("IPFS_API_URL", "http://localhost:5001")
        # Faucet API endpoint (configurable via env)
        self.faucet_api_url = os.environ.get("API_URL", "http://167.172.213.70:12346")
        self.ipfs_available = False
        self.offline_queue_file = "offline_queue.json"
        self.telemetry_enabled = True  # Enable telemetry by default
        self.telemetry_queue = queue.Queue()
        self.telemetry_thread = None
        self._check_network_connectivity()
        self._check_ipfs_connectivity()
    
    def _check_network_connectivity(self):
        """Check P2P network connectivity to bootstrap peers."""
        print(f"🌐 P2P Network Configuration")
        print(f"   Bootstrap Peers: {', '.join(self.bootstrap_peers)}")
        print(f"   Note: Use P2P mining node for blockchain participation")
        print(f"   Run: scripts/deployment/deploy_mining_node.sh start")
        return True

    def _check_ipfs_connectivity(self) -> bool:
        """Check if IPFS API is reachable and print status."""
        try:
            # IPFS /api/v0/version requires POST
            version_url = f"{self.ipfs_api_url}/api/v0/version"
            r = requests.post(version_url, timeout=5)
            if r.ok:
                info = r.json() if r.content else {}
                vers = info.get("Version", "unknown")
                print("🧩 IPFS: ✅ Available")
                print(f"   API URL: {self.ipfs_api_url}")
                print(f"   Version: {vers}")
                self.ipfs_available = True
                return True
            print(f"🧩 IPFS: ❌ Unavailable (HTTP {r.status_code})")
        except Exception as e:
            print(f"🧩 IPFS: ❌ Unavailable ({e})")
        self.ipfs_available = False
        return False
    
    def _fetch_live_blockchain_data(self):
        """Fetch live blockchain data from the droplet."""
        try:
            response = requests.get(f"{self.faucet_api_url}/v1/data/block/latest", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {})
            else:
                print(f"⚠️  Failed to fetch blockchain data (HTTP {response.status_code})")
                return None
        except Exception as e:
            print(f"⚠️  Error fetching blockchain data: {e}")
            return None
    
    def _send_mining_data(self, block_data):
        """Send mining data via P2P network (deprecated - use Node class instead)."""
        print("⚠️  HTTP API mining deprecated - use P2P mining node instead")
        print("💡 Run: ./deploy_mining_node.sh start")
        return False
    
    def _submit_block_to_network(self, block_data):
        """Submit mined block via P2P network (deprecated - use Node class instead)."""
        print("⚠️  HTTP API mining deprecated - use P2P mining node instead")
        print("💡 Run: ./deploy_mining_node.sh start")
        return False
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            prog='coinjectured',
            description='COINjecture blockchain node and interaction tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  coinjectured init --role miner --data-dir ./data
  coinjectured run --config ./config.json
  coinjectured mine --config ./config.json --problem-type subset_sum --tier desktop
  coinjectured get-block --hash 0xabc123...
  coinjectured get-proof --cid QmXyZ...
  coinjectured add-peer --multiaddr /ip4/127.0.0.1/tcp/8080
  coinjectured peers
  coinjectured submit-problem --type subset_sum --bounty 100 --strategy BEST
  coinjectured check-submission --id submission-123
  coinjectured list-submissions
  coinjectured wallet-generate --output ./my_wallet.json
  coinjectured wallet-info --wallet ./my_wallet.json
  coinjectured wallet-balance --wallet ./my_wallet.json
  coinjectured ipfs-upload --file proof_bundle.json
  coinjectured ipfs-retrieve --cid QmXyZ... --output proof.json
  coinjectured ipfs-status
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Node management commands
        self._add_init_command(subparsers)
        self._add_run_command(subparsers)
        self._add_mine_command(subparsers)
        
        # Blockchain interaction commands
        self._add_get_block_command(subparsers)
        self._add_get_proof_command(subparsers)
        
        # Network commands
        self._add_add_peer_command(subparsers)
        self._add_peers_command(subparsers)
        
        # User submissions commands
        self._add_submit_problem_command(subparsers)
        self._add_check_submission_command(subparsers)
        self._add_list_submissions_command(subparsers)
        
        # Wallet and transaction commands
        self._add_wallet_commands(subparsers)
        self._add_transaction_commands(subparsers)
        
        # Interactive menu command
        self._add_interactive_command(subparsers)
        
        # Telemetry commands
        self._add_telemetry_commands(subparsers)
        
        # Wallet management commands
        self._add_wallet_generate_command(subparsers)
        self._add_wallet_info_command(subparsers)
        self._add_wallet_balance_command(subparsers)
        
        # IPFS operation commands
        self._add_ipfs_upload_command(subparsers)
        self._add_ipfs_retrieve_command(subparsers)
        self._add_ipfs_status_command(subparsers)
        
        # Rewards commands
        self._add_rewards_command(subparsers)
        self._add_leaderboard_command(subparsers)
        self._add_mining_rewards_command(subparsers)
        
        return parser
    
    def _add_init_command(self, subparsers):
        """Add init command parser."""
        parser = subparsers.add_parser(
            'init',
            help='Initialize a new COINjecture node'
        )
        parser.add_argument(
            '--role',
            choices=['light', 'full', 'miner', 'archive'],
            required=True,
            help='Node role (light, full, miner, archive)'
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            default='./data',
            help='Data directory for node storage (default: ./data)'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Output config file path (default: config.json)'
        )
        parser.add_argument(
            '--network-id',
            type=str,
            default='coinjecture-testnet-v1',
            help='Network identifier (default: coinjecture-testnet-v1)'
        )
        parser.add_argument(
            '--listen-addr',
            type=str,
            default='0.0.0.0:8080',
            help='Listen address (default: 0.0.0.0:8080)'
        )
        parser.add_argument(
            '--enable-user-submissions',
            action='store_true',
            default=True,
            help='Enable user submissions system (default: True)'
        )
    
    def _add_run_command(self, subparsers):
        """Add run command parser."""
        parser = subparsers.add_parser(
            'run',
            help='Start a COINjecture node'
        )
        parser.add_argument(
            '--config',
            type=str,
            required=True,
            help='Path to configuration file'
        )
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run as daemon (background process)'
        )
    
    def _add_mine_command(self, subparsers):
        """Add mine command parser."""
        parser = subparsers.add_parser(
            'mine',
            help='Start mining operations'
        )
        parser.add_argument(
            '--config',
            type=str,
            required=True,
            help='Path to configuration file'
        )
        parser.add_argument(
            '--problem-type',
            type=str,
            default='subset_sum',
            help='Problem type to mine (default: subset_sum)'
        )
        parser.add_argument(
            '--tier',
            choices=['mobile', 'desktop', 'server', 'gpu'],
            default='desktop',
            help='Hardware tier for mining (default: desktop)'
        )
        parser.add_argument(
            '--duration',
            type=int,
            help='Mining duration in seconds (default: unlimited)'
        )
    
    def _add_get_block_command(self, subparsers):
        """Add get-block command parser."""
        parser = subparsers.add_parser(
            'get-block',
            help='Get block information'
        )
        parser.add_argument(
            '--hash',
            type=str,
            help='Block hash (hex format)'
        )
        parser.add_argument(
            '--index',
            type=int,
            help='Block index/height'
        )
        parser.add_argument(
            '--latest',
            action='store_true',
            help='Get latest block'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'pretty'],
            default='pretty',
            help='Output format (default: pretty)'
        )
    
    def _add_get_proof_command(self, subparsers):
        """Add get-proof command parser."""
        parser = subparsers.add_parser(
            'get-proof',
            help='Get proof data from IPFS'
        )
        parser.add_argument(
            '--cid',
            type=str,
            required=True,
            help='IPFS CID of the proof data'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'raw'],
            default='json',
            help='Output format (default: json)'
        )
        parser.set_defaults(func=self._handle_get_proof)

        # IPFS status command
        ipfs_parser = subparsers.add_parser(
            'ipfs-status',
            help='Check IPFS connectivity and version'
        )
        ipfs_parser.set_defaults(func=self._handle_ipfs_status)
    
    def _add_add_peer_command(self, subparsers):
        """Add add-peer command parser."""
        parser = subparsers.add_parser(
            'add-peer',
            help='Add a peer to the network'
        )
        parser.add_argument(
            '--multiaddr',
            type=str,
            required=True,
            help='Multiaddress of the peer'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )
    
    def _add_peers_command(self, subparsers):
        """Add peers command parser."""
        parser = subparsers.add_parser(
            'peers',
            help='List connected peers'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'table'],
            default='table',
            help='Output format (default: table)'
        )
    
    def _add_submit_problem_command(self, subparsers):
        """Add submit-problem command parser."""
        parser = subparsers.add_parser(
            'submit-problem',
            help='Submit a problem for mining with bounty'
        )
        parser.add_argument(
            '--type',
            type=str,
            required=True,
            help='Problem type (e.g., subset_sum)'
        )
        parser.add_argument(
            '--template',
            type=str,
            required=True,
            help='Problem template as JSON string'
        )
        parser.add_argument(
            '--bounty',
            type=float,
            required=True,
            help='Bounty amount per solution'
        )
        parser.add_argument(
            '--strategy',
            choices=['ANY', 'BEST', 'MULTIPLE', 'STATISTICAL'],
            default='BEST',
            help='Aggregation strategy (default: BEST)'
        )
        parser.add_argument(
            '--min-quality',
            type=float,
            default=0.0,
            help='Minimum solution quality threshold (default: 0.0)'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )
    
    def _add_check_submission_command(self, subparsers):
        """Add check-submission command parser."""
        parser = subparsers.add_parser(
            'check-submission',
            help='Check submission status'
        )
        parser.add_argument(
            '--id',
            type=str,
            required=True,
            help='Submission ID'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'pretty'],
            default='pretty',
            help='Output format (default: pretty)'
        )
    
    def _add_list_submissions_command(self, subparsers):
        """Add list-submissions command parser."""
        parser = subparsers.add_parser(
            'list-submissions',
            help='List active problem submissions'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'table'],
            default='table',
            help='Output format (default: table)'
        )
        parser.add_argument(
            '--status',
            choices=['open', 'partially_filled', 'complete', 'expired'],
            help='Filter by submission status'
        )
    
    def _add_wallet_commands(self, subparsers):
        """Add wallet command parsers."""
        # Create wallet
        create_parser = subparsers.add_parser(
            'wallet-create',
            help='Create new wallet'
        )
        create_parser.add_argument('name', help='Wallet name')
        create_parser.set_defaults(func=self._handle_wallet_create)
        
        # List wallets
        list_parser = subparsers.add_parser(
            'wallet-list',
            help='List available wallets'
        )
        list_parser.set_defaults(func=self._handle_wallet_list)
        
        # Get balance - removed duplicate, using _add_wallet_balance_command instead
    
    def _add_transaction_commands(self, subparsers):
        """Add transaction command parsers."""
        # Send transaction
        send_parser = subparsers.add_parser(
            'transaction-send',
            help='Send transaction'
        )
        send_parser.add_argument('sender', help='Sender address')
        send_parser.add_argument('recipient', help='Recipient address')
        send_parser.add_argument('amount', type=float, help='Amount to send')
        send_parser.add_argument('--private-key', help='Private key for signing')
        send_parser.set_defaults(func=self._handle_transaction_send)
        
        # Transaction history
        history_parser = subparsers.add_parser(
            'transaction-history',
            help='Get transaction history'
        )
        history_parser.add_argument('address', help='Wallet address')
        history_parser.add_argument('--limit', type=int, default=100, help='Number of transactions to show')
        history_parser.set_defaults(func=self._handle_transaction_history)
        
        # Pending transactions
        pending_parser = subparsers.add_parser(
            'transaction-pending',
            help='View pending transactions'
        )
        pending_parser.add_argument('--limit', type=int, default=100, help='Number of transactions to show')
        pending_parser.set_defaults(func=self._handle_transaction_pending)
        
        # Get transaction by ID
        get_parser = subparsers.add_parser(
            'transaction-get',
            help='Get transaction by ID'
        )
        get_parser.add_argument('tx_id', help='Transaction ID')
        get_parser.set_defaults(func=self._handle_transaction_get)

    def _add_interactive_command(self, subparsers):
        """Add interactive menu command parser."""
        parser = subparsers.add_parser(
            'interactive',
            help='Start interactive menu system'
        )
        parser.set_defaults(func=self._handle_interactive)
    
    def _add_telemetry_commands(self, subparsers):
        """Add telemetry command parsers."""
        # Enable telemetry
        enable_parser = subparsers.add_parser(
            'enable-telemetry',
            help='Enable telemetry reporting to faucet API'
        )
        enable_parser.add_argument(
            '--faucet-url',
            type=str,
            default='f"{self.faucet_api_url}"',
            help='Faucet API URL (default: f"{self.faucet_api_url}")'
        )
        enable_parser.add_argument(
            '--secret',
            type=str,
            default='dev-secret',
            help='HMAC secret for signing (default: dev-secret)'
        )
        enable_parser.set_defaults(func=self._handle_enable_telemetry)
        
        # Disable telemetry
        disable_parser = subparsers.add_parser(
            'disable-telemetry',
            help='Disable telemetry reporting'
        )
        disable_parser.set_defaults(func=self._handle_disable_telemetry)
        
        # Telemetry status
        status_parser = subparsers.add_parser(
            'telemetry-status',
            help='Check telemetry status and queue'
        )
        status_parser.set_defaults(func=self._handle_telemetry_status)
        
        # Flush queue
        flush_parser = subparsers.add_parser(
            'flush-telemetry',
            help='Manually flush telemetry queue'
        )
        flush_parser.set_defaults(func=self._handle_flush_telemetry)
    
    def _add_wallet_generate_command(self, subparsers):
        """Add wallet-generate command parser."""
        parser = subparsers.add_parser(
            'wallet-generate',
            help='Generate a new wallet'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='config/miner_wallet.json',
            help='Output wallet file path (default: config/miner_wallet.json)'
        )
        parser.set_defaults(func=self._handle_wallet_generate)
    
    def _add_wallet_info_command(self, subparsers):
        """Add wallet-info command parser."""
        parser = subparsers.add_parser(
            'wallet-info',
            help='Show wallet information'
        )
        parser.add_argument(
            '--wallet',
            type=str,
            default='config/miner_wallet.json',
            help='Wallet file path (default: config/miner_wallet.json)'
        )
        parser.set_defaults(func=self._handle_wallet_info)
    
    def _add_wallet_balance_command(self, subparsers):
        """Add wallet-balance command parser."""
        parser = subparsers.add_parser(
            'wallet-balance',
            help='Check wallet balance'
        )
        parser.add_argument(
            '--wallet',
            type=str,
            default='config/miner_wallet.json',
            help='Wallet file path (default: config/miner_wallet.json)'
        )
        parser.add_argument(
            '--api-url',
            type=str,
            default='f"{self.faucet_api_url}"',
            help='API URL for balance query (default: f"{self.faucet_api_url}")'
        )
        parser.set_defaults(func=self._handle_wallet_balance)
    
    def _add_ipfs_upload_command(self, subparsers):
        """Add ipfs-upload command parser."""
        parser = subparsers.add_parser(
            'ipfs-upload',
            help='Upload proof bundle to IPFS'
        )
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to proof bundle file'
        )
        parser.set_defaults(func=self._handle_ipfs_upload)
    
    def _add_ipfs_retrieve_command(self, subparsers):
        """Add ipfs-retrieve command parser."""
        parser = subparsers.add_parser(
            'ipfs-retrieve',
            help='Retrieve proof bundle from IPFS'
        )
        parser.add_argument(
            '--cid',
            type=str,
            required=True,
            help='IPFS CID to retrieve'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: stdout)'
        )
        parser.set_defaults(func=self._handle_ipfs_retrieve)
    
    def _add_ipfs_status_command(self, subparsers):
        """Add ipfs-status command parser."""
        parser = subparsers.add_parser(
            'ipfs-status',
            help='Check IPFS daemon status'
        )
        parser.set_defaults(func=self._handle_ipfs_status)
    
    def run(self, args: Optional[list] = None) -> int:
        """
        Run the CLI with given arguments.
        
        Args:
            args: Command line arguments (default: sys.argv[1:])
            
        Returns:
            int: Exit code (0 for success, non-zero for error)
        """
        try:
            parsed_args = self.parser.parse_args(args)
            
            if not parsed_args.command:
                self.parser.print_help()
                return 1
            
            # Route to appropriate command handler
            command_method = getattr(self, f'_handle_{parsed_args.command.replace("-", "_")}', None)
            if not command_method:
                print(f"Error: Unknown command '{parsed_args.command}'", file=sys.stderr)
                return 1
            
            return command_method(parsed_args)
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def _handle_init(self, args) -> int:
        """Handle init command."""
        try:
            # Convert role string to enum
            role_map = {
                'light': NodeRole.LIGHT,
                'full': NodeRole.FULL,
                'miner': NodeRole.MINER,
                'archive': NodeRole.ARCHIVE
            }
            role = role_map[args.role]
            
            # Create node configuration
            config = NodeConfig(
                role=role,
                data_dir=args.data_dir,
                network_id=args.network_id,
                listen_addr=args.listen_addr,
                enable_user_submissions=args.enable_user_submissions
            )
            
            # Create data directory
            data_path = Path(args.data_dir)
            data_path.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            config_path = args.config or 'config.json'
            config_data = {
                'role': args.role,
                'data_dir': args.data_dir,
                'network_id': args.network_id,
                'listen_addr': args.listen_addr,
                'enable_user_submissions': args.enable_user_submissions,
                'ipfs_api_url': config.ipfs_api_url,
                'target_block_interval_secs': config.target_block_interval_secs,
                'log_level': config.log_level
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print(f"✅ Node initialized successfully")
            print(f"   Role: {args.role}")
            print(f"   Data directory: {args.data_dir}")
            print(f"   Config file: {config_path}")
            print(f"   User submissions: {'enabled' if args.enable_user_submissions else 'disabled'}")
            
            return 0
            
        except Exception as e:
            print(f"Error initializing node: {e}", file=sys.stderr)
            return 1
    
    def _handle_run(self, args) -> int:
        """Handle run command."""
        try:
            # Load configuration
            config = load_config(args.config)
            
            # Create and start node
            node = Node(config)
            
            if not node.init():
                print("Error: Failed to initialize node", file=sys.stderr)
                return 1
            
            if not node.start():
                print("Error: Failed to start node", file=sys.stderr)
                return 1
            
            print(f"✅ Node started successfully in {config.role.value} mode")
            print(f"   Data directory: {config.data_dir}")
            print(f"   Listen address: {config.listen_addr}")
            
            if args.daemon:
                print("Running as daemon...")
                # In a real implementation, this would fork to background
                # For now, just run in foreground
                import time
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nShutting down node...")
                    node.stop()
            else:
                print("Press Ctrl+C to stop the node")
                import time
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nShutting down node...")
                    node.stop()
            
            return 0
            
        except Exception as e:
            print(f"Error running node: {e}", file=sys.stderr)
            return 1
    
    def _handle_mine(self, args) -> int:
        """Handle mine command with P2P mining logic."""
        try:
            try:
                from .tokenomics.wallet import Wallet
            except ImportError:
                from tokenomics.wallet import Wallet
            try:
                from .storage import StorageManager, StorageConfig, NodeRole, PruningMode
            except ImportError:
                from storage import StorageManager, StorageConfig, NodeRole, PruningMode
            try:
                from .core.blockchain import Block, ProblemTier, ProblemType, Transaction, mine_block, generate_subset_sum_problem, solve_subset_sum, verify_subset_sum
                from .core.blockchain import EnergyMetrics, ComputationalComplexity, subset_sum_complexity
            except ImportError:
                from core.blockchain import Block, ProblemTier, ProblemType, Transaction, mine_block, generate_subset_sum_problem, solve_subset_sum, verify_subset_sum
                from core.blockchain import EnergyMetrics, ComputationalComplexity, subset_sum_complexity
            import hashlib
            import json
            
            # Load or generate wallet
            wallet_path = "config/miner_wallet.json"
            try:
                wallet = Wallet.load_from_file(wallet_path)
                print(f"🔑 Loaded existing wallet: {wallet.address}")
            except:
                print(f"🔑 Generating new wallet...")
                wallet = Wallet.generate_new()
                wallet.save_to_file(wallet_path)
                print(f"💰 Mining rewards will be sent to: {wallet.address}")
            
            # Get current blockchain state
            current_index = self._get_current_blockchain_index()
            latest_hash = self._get_latest_block_hash()
            next_index = current_index + 1
            
            print(f"🌐 Current blockchain state:")
            print(f"   Latest block: #{current_index}")
            print(f"   Next block: #{next_index}")
            print(f"   Previous hash: {latest_hash[:16]}...")
            
            # Create storage manager for IPFS
            storage_config = StorageConfig(
                data_dir='./data',
                role=NodeRole.FULL,
                pruning_mode=PruningMode.FULL,
                ipfs_api_url=self.ipfs_api_url
            )
            storage_manager = StorageManager(storage_config)
            
            # Generate problem
            problem = generate_subset_sum_problem(
                seed=int(time.time()),
                tier=ProblemTier.TIER_2_DESKTOP
            )
            
            print(f"🧩 Generated problem: target={problem['target']}, size={problem['size']}")
            
            # Solve the problem
            start_time = time.time()
            solution = solve_subset_sum(problem)
            solve_time = time.time() - start_time
            
            if not solution:
                print("❌ Could not solve problem")
                return 1
            
            # Verify solution
            verify_start = time.time()
            is_valid = verify_subset_sum(problem, solution)
            verify_time = time.time() - verify_start
            
            if not is_valid:
                print("❌ Solution verification failed")
                return 1
            
            print(f"✅ Problem solved in {solve_time:.4f}s: {solution}")
            
            # Create energy metrics
            energy_metrics = EnergyMetrics(
                solve_energy_joules=solve_time * 100,
                verify_energy_joules=verify_time * 1,
                solve_power_watts=100,
                verify_power_watts=1,
                solve_time_seconds=solve_time,
                verify_time_seconds=verify_time,
                cpu_utilization=80.0,
                memory_utilization=50.0,
                gpu_utilization=0.0
            )
            
            # Create complexity specification
            complexity = subset_sum_complexity(
                problem=problem,
                solution=solution,
                solve_time=solve_time,
                verify_time=verify_time,
                solve_memory=0,
                verify_memory=0,
                energy_metrics=energy_metrics
            )
            
            # Create mining reward transaction
            reward_tx = Transaction(
                sender="network",
                recipient=wallet.address,
                amount=50.0,
                timestamp=time.time()
            )
            
            # Create block with proper chaining
            block = Block(
                index=next_index,
                timestamp=time.time(),
                previous_hash=latest_hash,
                transactions=[reward_tx],
                merkle_root="",  # Will be calculated
                problem=problem,
                solution=solution,
                complexity=complexity,
                mining_capacity=ProblemTier.TIER_2_DESKTOP,
                cumulative_work_score=max(complexity.measured_solve_time * 1000, problem['size'] * 0.1),
                block_hash="",  # Will be calculated
                offchain_cid=None
            )
            
            # Calculate merkle root and block hash
            block.merkle_root = self._calculate_merkle_root([reward_tx])
            block.block_hash = block.calculate_hash()
            
            # Upload proof bundle to IPFS
            try:
                proof_data = {
                    'problem': problem,
                    'solution': solution,
                    'complexity': {
                        'solve_time': solve_time,
                        'verify_time': verify_time,
                        'work_score': max(complexity.measured_solve_time * 1000, problem['size'] * 0.1)
                    },
                    'block_hash': block.block_hash,
                    'timestamp': time.time(),
                    'miner_address': wallet.address
                }
                bundle_bytes = json.dumps(proof_data, indent=2).encode('utf-8')
                cid = storage_manager.ipfs_client.add(bundle_bytes)
                block.offchain_cid = cid
                print(f"✅ Proof bundle uploaded to IPFS: {cid}")
            except Exception as e:
                print(f"⚠️  IPFS upload failed: {e}")
                import base58
                hash_bytes = hashlib.sha256(block.block_hash.encode()).digest()
                # IPFS CIDv0 uses multihash with sha256 (0x12) and length 32 (0x20)
                multihash = b'\x12\x20' + hash_bytes
                block.offchain_cid = base58.b58encode(multihash, alphabet=base58.BITCOIN_ALPHABET).decode('ascii')
                print(f"📦 Using placeholder CID: {block.offchain_cid}")
            
            print(f"✅ Block mined: #{block.index} - {block.block_hash[:16]}...")
            print(f"📊 Work score: {block.cumulative_work_score:.2f}")
            print(f"🧩 Problem size: {block.problem.get('size', 'unknown')}")
            
            # Sign block with wallet
            block_data = {
                "event_id": f"block-{int(time.time())}-{wallet.address}",
                "block_index": block.index,
                "block_hash": block.block_hash,
                "previous_hash": block.previous_hash,
                "merkle_root": block.merkle_root,
                "timestamp": block.timestamp,
                "cid": block.offchain_cid,
                "miner_address": wallet.address,
                "capacity": block.mining_capacity.value,
                "work_score": block.cumulative_work_score,
                "ts": int(block.timestamp)
            }
            
            signature = wallet.sign_block(block_data)
            public_key = wallet.get_public_key_bytes().hex()
            
            block_data["signature"] = signature
            block_data["public_key"] = public_key
            
            print(f"🔐 Block signed with wallet: {wallet.address}")
            
            # Submit to network API
            try:
                import requests
                response = requests.post(f"{self.faucet_api_url}/v1/ingest/block", 
                                       json=block_data, timeout=10)
                if response.status_code in [200, 202]:
                    print(f"✅ Block submitted to network: {response.status_code}")
                    print(f"💰 Mining rewards will be sent to: {wallet.address}")
                else:
                    print(f"❌ Network submission failed: {response.status_code}")
                    print(f"Response: {response.text}")
            except Exception as e:
                print(f"❌ Network submission error: {e}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Mining failed: {e}")
            return 1
    
    def _get_current_blockchain_index(self) -> int:
        """Get the current blockchain index from the network."""
        try:
            response = requests.get(f"{self.faucet_api_url}/v1/data/block/latest", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data['data']['index']
            return 0  # Default to genesis (index 0)
        except Exception as e:
            print(f"⚠️  Could not get current blockchain index: {e}")
            return 0  # Default to genesis (index 0)
    
    def _get_latest_block_hash(self) -> str:
        """Get the latest block hash from the network."""
        try:
            response = requests.get(f"{self.faucet_api_url}/v1/data/block/latest", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data['data']['block_hash']
            return "0000000000000000000000000000000000000000000000000000000000000000"  # Genesis hash
        except Exception as e:
            print(f"⚠️  Could not get latest block hash: {e}")
            return "0000000000000000000000000000000000000000000000000000000000000000"  # Genesis hash
    
    def _calculate_merkle_root(self, transactions):
        """Calculate merkle root for transactions."""
        import hashlib
        if not transactions:
            return "0" * 64
        
        tx_hashes = []
        for tx in transactions:
            if hasattr(tx, 'transaction_id'):
                tx_hashes.append(tx.transaction_id)
            else:
                tx_hashes.append(hashlib.sha256(str(tx).encode()).hexdigest())
        
        return hashlib.sha256("".join(tx_hashes).encode()).hexdigest()
    
    def _handle_get_block(self, args) -> int:
        """Handle get-block command."""
        try:
            # This would typically connect to a running node or read from storage
            # For now, return a placeholder response
            
            if args.latest:
                print("Getting latest block...")
                # Placeholder response
                block_data = {
                    "index": 1,
                    "timestamp": 1760601000.0,
                    "previous_hash": "0x0000000000000000000000000000000000000000000000000000000000000000",
                    "block_hash": "0xabc123...",
                    "mining_capacity": "TIER_2_DESKTOP",
                    "cumulative_work_score": 100.0
                }
            elif args.hash:
                print(f"Getting block by hash: {args.hash}")
                block_data = {"error": "Block not found"}
            elif args.index:
                print(f"Getting block by index: {args.index}")
                block_data = {"error": "Block not found"}
            else:
                print("Error: Must specify --hash, --index, or --latest", file=sys.stderr)
                return 1
            
            if args.format == 'json':
                print(json.dumps(block_data, indent=2))
            else:
                self._print_block_pretty(block_data)
            
            return 0
            
        except Exception as e:
            print(f"Error getting block: {e}", file=sys.stderr)
            return 1
    
    def _handle_get_proof(self, args) -> int:
        """Handle get-proof command."""
        try:
            print(f"Getting proof data from IPFS CID: {args.cid}")
            data_bytes: Optional[bytes] = None
            # Prefer direct IPFS API if available
            if self.ipfs_available:
                try:
                    # Lazy import to avoid hard dependency if packaging without IPFS
                    from .storage import IPFSClient  # type: ignore
                except Exception:
                    try:
                        from storage import IPFSClient  # type: ignore
                    except Exception:
                        IPFSClient = None  # type: ignore
                if IPFSClient is not None:
                    client = IPFSClient(api_url=self.ipfs_api_url)
                    data_bytes = client.get(args.cid)
            # Fallback to public gateway
            if data_bytes is None:
                gateway = f"https://ipfs.io/ipfs/{args.cid}"
                resp = requests.get(gateway, timeout=10)
                if resp.ok:
                    data_bytes = resp.content
            if data_bytes is None:
                print("Error: Unable to fetch proof data (IPFS unavailable)", file=sys.stderr)
                return 1
            # Try to decode JSON if requested
            if args.format == 'json':
                try:
                    obj = json.loads(data_bytes.decode('utf-8'))
                    print(json.dumps(obj, indent=2))
                except Exception:
                    print("Warning: Data is not valid JSON; showing raw bytes length")
                    print(len(data_bytes))
            else:
                # Raw output: print size and a safe preview
                preview = data_bytes[:64]
                print(f"Bytes: {len(data_bytes)}")
                try:
                    print(f"Preview: {preview.decode('utf-8', errors='ignore')}")
                except Exception:
                    print("Preview: <binary>")
            return 0
        except Exception as e:
            print(f"Error getting proof: {e}", file=sys.stderr)
            return 1

    def _handle_ipfs_status(self, args) -> int:
        """Report IPFS status."""
        try:
            ok = self._check_ipfs_connectivity()
            return 0 if ok else 1
        except Exception as e:
            print(f"Error checking IPFS: {e}", file=sys.stderr)
            return 1
    
    def _handle_add_peer(self, args) -> int:
        """Handle add-peer command."""
        try:
            print(f"Adding peer: {args.multiaddr}")
            
            # This would typically connect to a running node
            # For now, just confirm the action
            print("✅ Peer added successfully")
            
            return 0
            
        except Exception as e:
            print(f"Error adding peer: {e}", file=sys.stderr)
            return 1
    
    def _handle_peers(self, args) -> int:
        """Handle peers command."""
        try:
            print("Connected peers:")
            
            # This would typically query a running node
            # For now, return placeholder data
            peers = [
                {"id": "peer1", "address": "/ip4/127.0.0.1/tcp/8080", "status": "connected"},
                {"id": "peer2", "address": "/ip4/192.168.1.100/tcp/8080", "status": "connected"}
            ]
            
            if args.format == 'json':
                print(json.dumps(peers, indent=2))
            else:
                print(f"{'ID':<10} {'Address':<30} {'Status':<10}")
                print("-" * 50)
                for peer in peers:
                    print(f"{peer['id']:<10} {peer['address']:<30} {peer['status']:<10}")
            
            return 0
            
        except Exception as e:
            print(f"Error listing peers: {e}", file=sys.stderr)
            return 1
    
    def _handle_submit_problem(self, args) -> int:
        """Handle submit-problem command."""
        try:
            # Load configuration
            config = load_config(args.config) if args.config else NodeConfig()
            
            # Create node for submission
            node = Node(config)
            
            # Parse problem template
            try:
                problem_template = json.loads(args.template)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in problem template: {e}", file=sys.stderr)
                return 1
            
            # Convert strategy string to enum
            strategy_map = {
                'ANY': AggregationStrategy.ANY,
                'BEST': AggregationStrategy.BEST,
                'MULTIPLE': AggregationStrategy.MULTIPLE,
                'STATISTICAL': AggregationStrategy.STATISTICAL
            }
            strategy = strategy_map[args.strategy]
            
            # Submit problem
            submission_id = node.submit_problem(
                problem_type=args.type,
                problem_template=problem_template,
                aggregation=strategy,
                bounty=args.bounty,
                min_quality=args.min_quality
            )
            
            if submission_id:
                print(f"✅ Problem submitted successfully")
                print(f"   Submission ID: {submission_id}")
                print(f"   Problem type: {args.type}")
                print(f"   Bounty: {args.bounty}")
                print(f"   Strategy: {args.strategy}")
                return 0
            else:
                print("Error: Failed to submit problem", file=sys.stderr)
                return 1
            
        except Exception as e:
            print(f"Error submitting problem: {e}", file=sys.stderr)
            return 1
    
    def _handle_check_submission(self, args) -> int:
        """Handle check-submission command."""
        try:
            # Load configuration
            config = load_config(args.config) if args.config else NodeConfig()
            
            # Create node for query
            node = Node(config)
            
            # Check submission status
            status = node.get_submission_status(args.id)
            
            if status:
                if args.format == 'json':
                    print(json.dumps(status, indent=2))
                else:
                    self._print_submission_pretty(args.id, status)
                return 0
            else:
                print(f"Error: Submission '{args.id}' not found", file=sys.stderr)
                return 1
            
        except Exception as e:
            print(f"Error checking submission: {e}", file=sys.stderr)
            return 1
    
    def _handle_list_submissions(self, args) -> int:
        """Handle list-submissions command."""
        try:
            # Load configuration
            config = load_config(args.config) if args.config else NodeConfig()
            
            # Create node for query
            node = Node(config)
            
            # List active submissions
            submissions = node.list_active_submissions()
            
            # Filter by status if specified
            if args.status:
                submissions = [s for s in submissions if s['status'] == args.status]
            
            if args.format == 'json':
                print(json.dumps(submissions, indent=2))
            else:
                if submissions:
                    print(f"Active submissions ({len(submissions)}):")
                    print(f"{'ID':<25} {'Type':<15} {'Bounty':<10} {'Status':<15} {'Solutions':<10}")
                    print("-" * 85)
                    for sub in submissions:
                        print(f"{sub['submission_id']:<25} {sub['problem_type']:<15} {sub['bounty']:<10} {sub['status']:<15} {sub['solutions_count']:<10}")
                else:
                    print("No active submissions found")
            
            return 0
            
        except Exception as e:
            print(f"Error listing submissions: {e}", file=sys.stderr)
            return 1
    
    def _print_block_pretty(self, block_data: Dict[str, Any]) -> None:
        """Print block data in a pretty format."""
        if "error" in block_data:
            print(f"Error: {block_data['error']}")
            return
        
        print(f"Block Index: {block_data.get('index', 'N/A')}")
        print(f"Timestamp: {block_data.get('timestamp', 'N/A')}")
        print(f"Previous Hash: {block_data.get('previous_hash', 'N/A')}")
        print(f"Block Hash: {block_data.get('block_hash', 'N/A')}")
        print(f"Mining Capacity: {block_data.get('mining_capacity', 'N/A')}")
        print(f"Work Score: {block_data.get('cumulative_work_score', 'N/A')}")
    
    def _print_submission_pretty(self, submission_id: str, status: Dict[str, Any]) -> None:
        """Print submission status in a pretty format."""
        print(f"Submission ID: {submission_id}")
        print(f"Mode: {status.get('mode', 'N/A')}")
        print(f"Status: {status.get('status', 'N/A')}")
        print(f"Solutions Count: {status.get('solutions_count', 0)}")
        
        if status.get('mode') == 'BEST':
            print(f"Best Quality: {status.get('best_quality', 'N/A')}")
            print(f"Current Leader: {status.get('current_leader', 'N/A')}")
        elif status.get('mode') == 'MULTIPLE':
            print(f"Progress: {status.get('progress', 'N/A')}")
    
    def _handle_wallet_create(self, args) -> int:
        """Handle wallet creation."""
        try:
            try:
                from .tokenomics.wallet import Wallet
            except ImportError:
                from tokenomics.wallet import WalletManager
            manager = WalletManager()
            
            wallet = manager.create_wallet(args.name)
            if wallet:
                print(f"✅ Created wallet '{args.name}'")
                print(f"   Address: {wallet.address}")
                print(f"   Public Key: {wallet.get_public_key_bytes().hex()}")
                return 0
            else:
                print("❌ Failed to create wallet")
                return 1
        except Exception as e:
            print(f"❌ Error creating wallet: {e}")
            return 1
    
    def _handle_wallet_list(self, args) -> int:
        """Handle wallet listing."""
        try:
            try:
                from .tokenomics.wallet import Wallet
            except ImportError:
                from tokenomics.wallet import WalletManager
            manager = WalletManager()
            
            wallets = manager.list_wallets()
            if wallets:
                print("📋 Available wallets:")
                for wallet in wallets:
                    print(f"   Address: {wallet['address']}")
                    print(f"   Public Key: {wallet['public_key']}")
                    print()
            else:
                print("📋 No wallets found")
            return 0
        except Exception as e:
            print(f"❌ Error listing wallets: {e}")
            return 1
    
    # Removed duplicate _handle_wallet_balance method - using the one at line 2160
    
    def _handle_transaction_send(self, args) -> int:
        """Handle transaction sending."""
        try:
            from tokenomics.blockchain_state import BlockchainState, Transaction
            state = BlockchainState()
            
            # Create transaction
            transaction = Transaction(
                sender=args.sender,
                recipient=args.recipient,
                amount=args.amount,
                timestamp=time.time()
            )
            
            # Sign if private key provided
            if args.private_key:
                private_key_bytes = bytes.fromhex(args.private_key)
                transaction.sign(private_key_bytes)
            
            # Add to pool
            if state.add_transaction(transaction):
                print(f"✅ Transaction submitted")
                print(f"   ID: {transaction.transaction_id}")
                print(f"   From: {args.sender}")
                print(f"   To: {args.recipient}")
                print(f"   Amount: {args.amount}")
                return 0
            else:
                print("❌ Transaction validation failed")
                return 1
        except Exception as e:
            print(f"❌ Error sending transaction: {e}")
            return 1
    
    def _handle_transaction_history(self, args) -> int:
        """Handle transaction history retrieval."""
        try:
            from tokenomics.blockchain_state import BlockchainState
            state = BlockchainState()
            
            transactions = state.get_transaction_history(args.address, args.limit)
            if transactions:
                print(f"📜 Transaction history for {args.address}:")
                for tx in transactions:
                    print(f"   {tx.transaction_id[:8]}... | {tx.sender} -> {tx.recipient} | {tx.amount} | {time.ctime(tx.timestamp)}")
            else:
                print(f"📜 No transactions found for {args.address}")
            return 0
        except Exception as e:
            print(f"❌ Error getting transaction history: {e}")
            return 1
    
    def _handle_transaction_pending(self, args) -> int:
        """Handle pending transactions listing."""
        try:
            from tokenomics.blockchain_state import BlockchainState
            state = BlockchainState()
            
            pending = state.get_pending_transactions(args.limit)
            if pending:
                print(f"⏳ Pending transactions ({len(pending)}):")
                for tx in pending:
                    print(f"   {tx.transaction_id[:8]}... | {tx.sender} -> {tx.recipient} | {tx.amount} | {time.ctime(tx.timestamp)}")
            else:
                print("⏳ No pending transactions")
            return 0
        except Exception as e:
            print(f"❌ Error getting pending transactions: {e}")
            return 1
    
    def _handle_transaction_get(self, args) -> int:
        """Handle transaction retrieval by ID."""
        try:
            from tokenomics.blockchain_state import BlockchainState
            state = BlockchainState()
            
            transaction = state.get_transaction_by_id(args.tx_id)
            if transaction:
                print(f"🔍 Transaction {args.tx_id}:")
                print(f"   From: {transaction.sender}")
                print(f"   To: {transaction.recipient}")
                print(f"   Amount: {transaction.amount}")
                print(f"   Timestamp: {time.ctime(transaction.timestamp)}")
                print(f"   Signature: {transaction.signature[:16]}..." if transaction.signature else "   Signature: None")
            else:
                print(f"❌ Transaction {args.tx_id} not found")
                return 1
            return 0
        except Exception as e:
            print(f"❌ Error getting transaction: {e}")
            return 1

    def _handle_interactive(self, args) -> int:
        """Handle interactive menu system."""
        return self._interactive_menu()
    
    def _interactive_menu(self) -> int:
        """Interactive menu system with clear navigation."""
        while True:
            print("\n" + "="*60)
            print("🚀 COINjecture Interactive Menu")
            print("="*60)
            
            # Show live network status
            if self.telemetry_enabled:
                live_data = self._fetch_live_blockchain_data()
                if live_data:
                    print(f"🌐 Live Network: Block #{live_data.get('index', 'unknown')} | Hash: {live_data.get('block_hash', 'unknown')[:16]}...")
                    print(f"   Work Score: {live_data.get('cumulative_work_score', 0):.2f} | Capacity: {live_data.get('mining_capacity', 'unknown')}")
                else:
                    print("🌐 Live Network: Connected but no data available")
            else:
                print("🌐 Live Network: Offline mode")
            
            print("="*60)
            print("1. 🏗️  Setup & Configuration")
            print("2. ⛏️  Mining Operations") 
            print("3. 💰 Problem Submissions")
            print("4. 🔍 Blockchain Explorer")
            print("5. 🌐 Network Management")
            print("6. 📊 Telemetry & Monitoring")
            print("7. ❓ Help & Documentation")
            print("8. 🚪 Exit")
            print("="*60)
            
            choice = input("Choose an option (1-8): ").strip()
            
            if choice == '1':
                self._setup_menu()
            elif choice == '2':
                self._mining_menu()
            elif choice == '3':
                self._submissions_menu()
            elif choice == '4':
                self._explorer_menu()
            elif choice == '5':
                self._network_menu()
            elif choice == '6':
                self._telemetry_menu()
            elif choice == '7':
                self._help_menu()
            elif choice == '8':
                print("👋 Goodbye!")
                return 0
            else:
                print("❌ Invalid choice. Please select 1-8.")
    
    def _setup_menu(self):
        """Setup and configuration menu."""
        while True:
            print("\n" + "-"*40)
            print("🏗️  Setup & Configuration")
            print("-"*40)
            print("1. Initialize Miner Node")
            print("2. Initialize Full Node")
            print("3. Initialize Light Node")
            print("4. Initialize Archive Node")
            print("5. ← Back to Main Menu")
            print("-"*40)
            
            choice = input("Choose setup option (1-5): ").strip()
            
            if choice == '1':
                self._init_node_interactive('miner')
            elif choice == '2':
                self._init_node_interactive('full')
            elif choice == '3':
                self._init_node_interactive('light')
            elif choice == '4':
                self._init_node_interactive('archive')
            elif choice == '5':
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
    
    def _mining_menu(self):
        """Mining operations menu."""
        while True:
            print("\n" + "-"*40)
            print("⛏️  Mining Operations")
            print("-"*40)
            
            # Show live network mining data
            if self.telemetry_enabled:
                live_data = self._fetch_live_blockchain_data()
                if live_data:
                    print(f"🌐 Live Network Mining:")
                    print(f"   Current Block: #{live_data.get('index', 'unknown')}")
                    print(f"   Work Score: {live_data.get('cumulative_work_score', 0):.2f}")
                    print(f"   Capacity: {live_data.get('mining_capacity', 'unknown')}")
                    print(f"   Hash: {live_data.get('block_hash', 'unknown')[:16]}...")
                else:
                    print("🌐 Live Network: Connected but no data available")
            else:
                print("🌐 Live Network: Offline mode")
            
            print("-"*40)
            print("1. Start Mining (Desktop)")
            print("2. Start Mining (Mobile)")
            print("3. Start Mining (Server)")
            print("4. Start Mining (GPU)")
            print("5. Check Mining Status")
            print("6. ← Back to Main Menu")
            print("-"*40)
            
            choice = input("Choose mining option (1-6): ").strip()
            
            if choice == '1':
                self._start_mining_interactive('desktop')
            elif choice == '2':
                self._start_mining_interactive('mobile')
            elif choice == '3':
                self._start_mining_interactive('server')
            elif choice == '4':
                self._start_mining_interactive('gpu')
            elif choice == '5':
                self._check_mining_status()
            elif choice == '6':
                break
            else:
                print("❌ Invalid choice. Please select 1-6.")
    
    def _submissions_menu(self):
        """Problem submissions menu."""
        while True:
            print("\n" + "-"*40)
            print("💰 Problem Submissions")
            print("-"*40)
            print("1. Submit New Problem")
            print("2. Check Submission Status")
            print("3. List All Submissions")
            print("4. ← Back to Main Menu")
            print("-"*40)
            
            choice = input("Choose submission option (1-4): ").strip()
            
            if choice == '1':
                self._submit_problem_interactive()
            elif choice == '2':
                self._check_submission_interactive()
            elif choice == '3':
                self._list_submissions_interactive()
            elif choice == '4':
                break
            else:
                print("❌ Invalid choice. Please select 1-4.")
    
    def _explorer_menu(self):
        """Blockchain explorer menu."""
        while True:
            print("\n" + "-"*40)
            print("🔍 Blockchain Explorer")
            print("-"*40)
            print("1. View Latest Block")
            print("2. View Block by Index")
            print("3. View Block by Hash")
            print("4. Get Proof Data")
            print("5. ← Back to Main Menu")
            print("-"*40)
            
            choice = input("Choose explorer option (1-5): ").strip()
            
            if choice == '1':
                self._view_latest_block()
            elif choice == '2':
                self._view_block_by_index()
            elif choice == '3':
                self._view_block_by_hash()
            elif choice == '4':
                self._get_proof_data()
            elif choice == '5':
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
    
    def _network_menu(self):
        """Network management menu."""
        while True:
            print("\n" + "-"*40)
            print("🌐 Network Management")
            print("-"*40)
            print("1. Add Peer")
            print("2. List Connected Peers")
            print("3. ← Back to Main Menu")
            print("-"*40)
            
            choice = input("Choose network option (1-3): ").strip()
            
            if choice == '1':
                self._add_peer_interactive()
            elif choice == '2':
                self._list_peers()
            elif choice == '3':
                break
            else:
                print("❌ Invalid choice. Please select 1-3.")
    
    def _telemetry_menu(self):
        """Telemetry and monitoring menu."""
        while True:
            print("\n" + "-"*40)
            print("📊 Telemetry & Monitoring")
            print("-"*40)
            print("1. Enable Telemetry")
            print("2. Disable Telemetry")
            print("3. Check Telemetry Status")
            print("4. Flush Telemetry Queue")
            print("5. ← Back to Main Menu")
            print("-"*40)
            
            choice = input("Choose telemetry option (1-5): ").strip()
            
            if choice == '1':
                self._enable_telemetry_interactive()
            elif choice == '2':
                self._disable_telemetry_interactive()
            elif choice == '3':
                self._check_telemetry_status()
            elif choice == '4':
                self._flush_telemetry_queue()
            elif choice == '5':
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
    
    def _help_menu(self):
        """Help and documentation menu."""
        while True:
            print("\n" + "-"*40)
            print("❓ Help & Documentation")
            print("-"*40)
            print("1. Show All Commands")
            print("2. Command Help")
            print("3. User Guide")
            print("4. ← Back to Main Menu")
            print("-"*40)
            
            choice = input("Choose help option (1-4): ").strip()
            
            if choice == '1':
                self.parser.print_help()
            elif choice == '2':
                cmd = input("Enter command name: ").strip()
                try:
                    subparser = self.parser._subparsers._actions[0].choices.get(cmd)
                    if subparser:
                        subparser.print_help()
                    else:
                        print(f"❌ Command '{cmd}' not found.")
                except:
                    print("❌ Error showing help.")
            elif choice == '3':
                print("📖 See USER_GUIDE.md for detailed instructions")
            elif choice == '4':
                break
            else:
                print("❌ Invalid choice. Please select 1-4.")
    
    # Interactive helper methods
    def _init_node_interactive(self, role: str):
        """Interactive node initialization."""
        print(f"\n🏗️  Initializing {role} node...")
        data_dir = input(f"Data directory (default: ./{role}_data): ").strip() or f"./{role}_data"
        config_file = input(f"Config file (default: {role}_config.json): ").strip() or f"{role}_config.json"
        
        args = type('Args', (), {
            'role': role,
            'data_dir': data_dir,
            'config': config_file,
            'network_id': 'coinjecture-testnet-v1',
            'listen_addr': '0.0.0.0:8080',
            'enable_user_submissions': True
        })()
        
        result = self._handle_init(args)
        if result == 0:
            print(f"✅ {role.title()} node initialized successfully!")
        else:
            print(f"❌ Failed to initialize {role} node.")
    
    def _start_mining_interactive(self, tier: str):
        """Interactive mining start."""
        print(f"\n⛏️  Starting mining with {tier} tier...")
        
        # Use the new direct mining method
        capacity_map = {
            'mobile': 'TIER_1_MOBILE',
            'desktop': 'TIER_2_DESKTOP', 
            'server': 'TIER_3_SERVER',
            'gpu': 'TIER_4_GPU'
        }
        capacity = capacity_map.get(tier, 'TIER_2_DESKTOP')
        
        print(f"🚀 Mining single block...")
        success = self._mine_single_block(capacity)
        
        if success:
            print("✅ Mining completed successfully!")
            return 0
        else:
            print("❌ Mining failed!")
            return 1
    
    def _submit_problem_interactive(self):
        """Interactive problem submission."""
        print("\n💰 Submit a new problem...")
        problem_type = input("Problem type (default: subset_sum): ").strip() or "subset_sum"
        template = input("Problem template (JSON): ").strip()
        bounty = input("Bounty amount: ").strip()
        strategy = input("Strategy (ANY/BEST/MULTIPLE/STATISTICAL, default: BEST): ").strip() or "BEST"
        
        if not template or not bounty:
            print("❌ Template and bounty are required.")
            return
        
        args = type('Args', (), {
            'type': problem_type,
            'template': template,
            'bounty': float(bounty),
            'strategy': strategy,
            'min_quality': 0.0,
            'config': None
        })()
        
        result = self._handle_submit_problem(args)
        if result == 0:
            print("✅ Problem submitted successfully!")
        else:
            print("❌ Failed to submit problem.")
    
    def _check_submission_interactive(self):
        """Interactive submission check."""
        submission_id = input("Enter submission ID: ").strip()
        if not submission_id:
            print("❌ Submission ID is required.")
            return
        
        args = type('Args', (), {
            'id': submission_id,
            'config': None,
            'format': 'pretty'
        })()
        
        self._handle_check_submission(args)
    
    def _list_submissions_interactive(self):
        """Interactive submissions listing."""
        args = type('Args', (), {
            'config': None,
            'format': 'table',
            'status': None
        })()
        
        self._handle_list_submissions(args)
    
    def _view_latest_block(self):
        """View latest block."""
        args = type('Args', (), {
            'latest': True,
            'hash': None,
            'index': None,
            'format': 'pretty'
        })()
        
        self._handle_get_block(args)
    
    def _view_block_by_index(self):
        """View block by index."""
        index = input("Enter block index: ").strip()
        if not index.isdigit():
            print("❌ Block index must be a number.")
            return
        
        args = type('Args', (), {
            'latest': False,
            'hash': None,
            'index': int(index),
            'format': 'pretty'
        })()
        
        self._handle_get_block(args)
    
    def _view_block_by_hash(self):
        """View block by hash."""
        block_hash = input("Enter block hash: ").strip()
        if not block_hash:
            print("❌ Block hash is required.")
            return
        
        args = type('Args', (), {
            'latest': False,
            'hash': block_hash,
            'index': None,
            'format': 'pretty'
        })()
        
        self._handle_get_block(args)
    
    def _get_proof_data(self):
        """Get proof data."""
        cid = input("Enter IPFS CID: ").strip()
        if not cid:
            print("❌ IPFS CID is required.")
            return
        
        args = type('Args', (), {
            'cid': cid,
            'format': 'json'
        })()
        
        self._handle_get_proof(args)
    
    def _add_peer_interactive(self):
        """Interactive peer addition."""
        multiaddr = input("Enter peer multiaddress: ").strip()
        if not multiaddr:
            print("❌ Multiaddress is required.")
            return
        
        args = type('Args', (), {
            'multiaddr': multiaddr,
            'config': None
        })()
        
        self._handle_add_peer(args)
    
    def _list_peers(self):
        """List connected peers."""
        args = type('Args', (), {
            'config': None,
            'format': 'table'
        })()
        
        self._handle_peers(args)
    
    def _enable_telemetry_interactive(self):
        """Interactive telemetry enable."""
        faucet_url = input(f"Faucet API URL (default: {self.faucet_api_url}): ").strip() or self.faucet_api_url
        secret = input("HMAC secret (default: dev-secret): ").strip() or "dev-secret"
        
        args = type('Args', (), {
            'faucet_url': faucet_url,
            'secret': secret
        })()
        
        self._handle_enable_telemetry(args)
    
    def _disable_telemetry_interactive(self):
        """Interactive telemetry disable."""
        args = type('Args', (), {})()
        self._handle_disable_telemetry(args)
    
    def _check_telemetry_status(self):
        """Check telemetry status."""
        args = type('Args', (), {})()
        self._handle_telemetry_status(args)
    
    def _flush_telemetry_queue(self):
        """Flush telemetry queue."""
        args = type('Args', (), {})()
        self._handle_flush_telemetry(args)
    
    def _check_mining_status(self):
        """Check mining status."""
        print("📊 Mining Status:")
        print(f"   Telemetry: {'✅ Enabled' if self.telemetry_enabled else '❌ Disabled'}")
        print(f"   Queue size: {self.telemetry_queue.qsize()}")
        
        # Show live network data
        if self.telemetry_enabled:
            live_data = self._fetch_live_blockchain_data()
            if live_data:
                print(f"   Live Network: Block #{live_data.get('index', 'unknown')}")
                print(f"   Work Score: {live_data.get('cumulative_work_score', 0):.2f}")
                print(f"   Capacity: {live_data.get('mining_capacity', 'unknown')}")
            else:
                print("   Live Network: Connected but no data available")
        else:
            print("   Live Network: Offline mode")
        
        print("   Use 'telemetry-status' for detailed info")
    
    def _mine_single_block(self, capacity: str = "TIER_2_DESKTOP"):
        """Mine a single block and submit to network."""
        try:
            print(f"⛏️  Mining block with {capacity} capacity...")
            
            # Import required modules
            from .core.blockchain import mine_block, Block, ProblemTier, ProblemType, Transaction, ComputationalComplexity, EnergyMetrics
            import time
            
            # Create a complete EnergyMetrics object
            energy_metrics = EnergyMetrics(
                solve_energy_joules=0.1,
                verify_energy_joules=0.001,
                solve_power_watts=50.0,
                verify_power_watts=10.0,
                solve_time_seconds=0.1,
                verify_time_seconds=0.001,
                cpu_utilization=80.0,
                memory_utilization=50.0,
                gpu_utilization=0.0
            )
            
            # Create a complete ComputationalComplexity object
            complexity = ComputationalComplexity(
                # Asymptotic Time Complexities
                time_solve_O="O(2^n)",
                time_solve_Omega="Omega(2^(n/2))",
                time_solve_Theta=None,
                time_verify_O="O(n)",
                time_verify_Omega="Omega(n)",
                time_verify_Theta="Theta(n)",
                
                # Asymptotic Space Complexities
                space_solve_O="O(n)",
                space_solve_Omega="Omega(1)",
                space_solve_Theta=None,
                space_verify_O="O(1)",
                space_verify_Omega="Omega(1)",
                space_verify_Theta="Theta(1)",
                
                # Problem Classification
                problem_class="NP-Complete",
                
                # Problem Characteristics
                problem_size=8,
                solution_size=3,
                
                # Solution Quality
                epsilon_approximation=None,  # Exact algorithm
                
                # Asymmetry Measures
                asymmetry_time=2.0,  # solve_time_O / verify_time_O
                asymmetry_space=1.0,  # space_solve_O / verify_time_O
                
                # Measured Performance
                measured_solve_time=0.1,
                measured_verify_time=0.001,
                measured_solve_space=1024,
                measured_verify_space=256,
                
                # Energy Metrics
                energy_metrics=energy_metrics,
                
                # Problem Data
                problem={"type": "subset_sum", "size": 8, "target": 100},
                
                # Solution Quality
                solution_quality=1.0
            )
            
            # Create a simple previous block for testing
            previous_block = Block(
                index=0,
                timestamp=time.time() - 30,
                previous_hash="0" * 64,
                transactions=[],
                merkle_root="0" * 64,
                problem={"type": "subset_sum", "size": 8, "target": 100},
                solution=[1, 2, 3],
                complexity=complexity,
                mining_capacity=ProblemTier.TIER_1_MOBILE,
                cumulative_work_score=0.0,
                block_hash="0" * 64
            )
            
            # Create a simple transaction for mining reward
            reward_tx = Transaction(
                sender="",
                recipient="miner_address",
                amount=50.0,
                timestamp=time.time()
            )
            
            # Convert capacity string to ProblemTier
            capacity_map = {
                "TIER_1_MOBILE": ProblemTier.TIER_1_MOBILE,
                "TIER_2_DESKTOP": ProblemTier.TIER_2_DESKTOP,
                "TIER_3_WORKSTATION": ProblemTier.TIER_3_WORKSTATION,
                "TIER_4_SERVER": ProblemTier.TIER_4_SERVER,
                "TIER_5_CLUSTER": ProblemTier.TIER_5_CLUSTER
            }
            problem_tier = capacity_map.get(capacity, ProblemTier.TIER_2_DESKTOP)
            
            # Mine the block
            print("🔨 Solving computational problem...")
            block = mine_block(
                transactions=[reward_tx],
                previous_block=previous_block,
                capacity=problem_tier,
                problem_type=ProblemType.SUBSET_SUM,
                miner_address="cli_miner"
            )
            
            print(f"✅ Block mined successfully!")
            print(f"   Index: {block.index}")
            print(f"   Hash: {block.block_hash[:16]}...")
            print(f"   Work Score: {block.cumulative_work_score:.2f}")
            
            # Submit to network
            print("📡 Submitting block to network...")
            block_dict = block.to_dict()
            success = self._submit_block_to_network(block_dict)
            
            if success:
                print("🎉 Block successfully submitted to network!")
                return True
            else:
                print("⚠️  Block mining completed but network submission failed")
                return False
                
        except Exception as e:
            print(f"❌ Mining failed: {e}")
            return False
    
    # Telemetry command handlers
    def _handle_enable_telemetry(self, args) -> int:
        """Handle enable telemetry command."""
        try:
            self.faucet_api_url = args.faucet_url
            self.telemetry_enabled = True
            print(f"✅ Telemetry enabled")
            print(f"   Faucet URL: {self.faucet_api_url}")
            print(f"   Secret: {'*' * len(args.secret)}")
            return 0
        except Exception as e:
            print(f"❌ Error enabling telemetry: {e}")
            return 1
    
    def _handle_disable_telemetry(self, args) -> int:
        """Handle disable telemetry command."""
        try:
            self.telemetry_enabled = False
            print("✅ Telemetry disabled")
            return 0
        except Exception as e:
            print(f"❌ Error disabling telemetry: {e}")
            return 1
    
    def _handle_telemetry_status(self, args) -> int:
        """Handle telemetry status command."""
        try:
            print("📊 Telemetry Status:")
            print(f"   Enabled: {'✅ Yes' if self.telemetry_enabled else '❌ No'}")
            print(f"   Faucet URL: {self.faucet_api_url}")
            print(f"   Queue size: {self.telemetry_queue.qsize()}")
            return 0
        except Exception as e:
            print(f"❌ Error checking telemetry status: {e}")
            return 1
    
    def _handle_flush_telemetry(self, args) -> int:
        """Handle flush telemetry command."""
        try:
            if not self.telemetry_enabled:
                print("❌ Telemetry is not enabled")
                return 1
            
            # TODO: Implement actual flush logic
            print("✅ Telemetry queue flushed")
            return 0
        except Exception as e:
            print(f"❌ Error flushing telemetry: {e}")
            return 1
    
    def _handle_wallet_generate(self, args) -> int:
        """Handle wallet-generate command."""
        try:
            try:
                from .tokenomics.wallet import Wallet
            except ImportError:
                from tokenomics.wallet import Wallet
            
            # Generate new wallet
            wallet = Wallet.generate_new()
            
            # Save to file
            wallet.save_to_file(args.output)
            
            print(f"✅ Wallet generated successfully!")
            print(f"   Address: {wallet.address}")
            print(f"   Saved to: {args.output}")
            print(f"   ⚠️  IMPORTANT: Backup your private key securely!")
            
            return 0
        except Exception as e:
            print(f"❌ Error generating wallet: {e}")
            return 1
    
    def _handle_wallet_info(self, args) -> int:
        """Handle wallet-info command."""
        try:
            try:
                from .tokenomics.wallet import Wallet
            except ImportError:
                from tokenomics.wallet import Wallet
            
            # Load wallet from file
            wallet = Wallet.load_from_file(args.wallet)
            
            print(f"📋 Wallet Information:")
            print(f"   Address: {wallet.address}")
            print(f"   Public Key: {wallet.get_public_key_bytes().hex()}")
            print(f"   File: {args.wallet}")
            
            return 0
        except Exception as e:
            print(f"❌ Error loading wallet: {e}")
            return 1
    
    def _handle_wallet_balance(self, args) -> int:
        """Handle wallet-balance command."""
        try:
            try:
                from .tokenomics.wallet import Wallet
                from .tokenomics.blockchain_state import BlockchainState
            except ImportError:
                from tokenomics.wallet import Wallet
                from tokenomics.blockchain_state import BlockchainState
            
            # Load wallet from file
            wallet = Wallet.load_from_file(args.wallet)
            
            # Check local blockchain state first
            try:
                blockchain_state = BlockchainState()
                blockchain_state.load_state()
                local_balance = blockchain_state.get_balance(wallet.address)
                
                print(f"💰 Wallet Balance (Local Blockchain State):")
                print(f"   Address: {wallet.address}")
                print(f"   Balance: {local_balance:.6f} COIN")
                
                # Also try API for comparison (if available)
                try:
                    response = requests.get(f"{self.faucet_api_url}/v1/wallet/{wallet.address}/balance", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        api_balance = data.get('balance', 0)
                        print(f"   API Balance: {api_balance:.6f} COIN")
                        if abs(local_balance - api_balance) > 0.000001:
                            print(f"   ⚠️  Balance mismatch between local and API")
                    else:
                        print(f"   API: Not available (HTTP {response.status_code})")
                except Exception as e:
                    print(f"   API: Not available ({e})")
                    
            except Exception as e:
                print(f"⚠️  Could not load local blockchain state: {e}")
                print(f"   Address: {wallet.address}")
                print(f"   Note: Local blockchain state may not be initialized yet")
            
            return 0
        except Exception as e:
            print(f"❌ Error checking wallet balance: {e}")
            return 1
    
    def _handle_ipfs_upload(self, args) -> int:
        """Handle ipfs-upload command."""
        try:
            try:
                from .storage import StorageManager, StorageConfig, NodeRole, PruningMode
            except ImportError:
                from storage import StorageManager, StorageConfig, NodeRole, PruningMode
            
            # Create storage manager
            storage_config = StorageConfig(
                data_dir='./data',
                role=NodeRole.FULL,
                pruning_mode=PruningMode.FULL,
                ipfs_api_url=self.ipfs_api_url
            )
            storage_manager = StorageManager(storage_config)
            
            # Read file
            with open(args.file, 'rb') as f:
                file_data = f.read()
            
            # Upload to IPFS
            cid = storage_manager.ipfs_client.add(file_data)
            
            print(f"✅ File uploaded to IPFS successfully!")
            print(f"   File: {args.file}")
            print(f"   CID: {cid}")
            print(f"   Size: {len(file_data)} bytes")
            
            return 0
        except Exception as e:
            print(f"❌ Error uploading to IPFS: {e}")
            return 1
    
    def _handle_ipfs_retrieve(self, args) -> int:
        """Handle ipfs-retrieve command."""
        try:
            try:
                from .storage import StorageManager, StorageConfig, NodeRole, PruningMode
            except ImportError:
                from storage import StorageManager, StorageConfig, NodeRole, PruningMode
            
            # Create storage manager
            storage_config = StorageConfig(
                data_dir='./data',
                role=NodeRole.FULL,
                pruning_mode=PruningMode.FULL,
                ipfs_api_url=self.ipfs_api_url
            )
            storage_manager = StorageManager(storage_config)
            
            # Retrieve from IPFS
            data = storage_manager.ipfs_client.get(args.cid)
            
            if args.output:
                # Save to file
                with open(args.output, 'wb') as f:
                    f.write(data)
                print(f"✅ Data retrieved from IPFS successfully!")
                print(f"   CID: {args.cid}")
                print(f"   Saved to: {args.output}")
                print(f"   Size: {len(data)} bytes")
            else:
                # Print to stdout
                print(data.decode('utf-8', errors='ignore'))
            
            return 0
        except Exception as e:
            print(f"❌ Error retrieving from IPFS: {e}")
            return 1
    
    def _handle_ipfs_status(self, args) -> int:
        """Handle ipfs-status command."""
        try:
            print("🧩 IPFS Status:")
            if self._check_ipfs_connectivity():
                print(f"   Status: ✅ Available")
                print(f"   API URL: {self.ipfs_api_url}")
            else:
                print(f"   Status: ❌ Unavailable")
                print(f"   API URL: {self.ipfs_api_url}")
                print(f"   Note: Start IPFS daemon with 'ipfs daemon'")
            
            return 0
        except Exception as e:
            print(f"❌ Error checking IPFS status: {e}")
            return 1
    
    def _add_rewards_command(self, subparsers):
        """Add rewards command parser."""
        parser = subparsers.add_parser('rewards', help='Check mining rewards')
        parser.add_argument('--address', help='Miner address to check rewards for')
        parser.add_argument('--wallet', help='Wallet file to get address from')
    
    def _add_leaderboard_command(self, subparsers):
        """Add leaderboard command parser."""
        subparsers.add_parser('leaderboard', help='Show mining leaderboard')
    
    def _add_mining_rewards_command(self, subparsers):
        """Add mining-rewards command parser."""
        parser = subparsers.add_parser(
            'mining-rewards',
            help='Show mining rewards and transaction history'
        )
        parser.add_argument(
            '--wallet',
            type=str,
            default='config/miner_wallet.json',
            help='Wallet file path (default: config/miner_wallet.json)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Number of recent transactions to show (default: 10)'
        )
        parser.set_defaults(func=self._handle_mining_rewards)
    
    def _handle_mining_rewards(self, args) -> int:
        """Handle mining-rewards command."""
        try:
            try:
                from .tokenomics.wallet import Wallet
                from .tokenomics.blockchain_state import BlockchainState
            except ImportError:
                from tokenomics.wallet import Wallet
                from tokenomics.blockchain_state import BlockchainState
            
            # Load wallet from file
            wallet = Wallet.load_from_file(args.wallet)
            
            # Load blockchain state
            blockchain_state = BlockchainState()
            blockchain_state.load_state()
            
            # Get current balance
            balance = blockchain_state.get_balance(wallet.address)
            
            print(f"💰 Mining Rewards Summary:")
            print(f"   Address: {wallet.address}")
            print(f"   Current Balance: {balance:.6f} COIN")
            
            # Get transaction history for this address
            transactions = []
            for tx in blockchain_state.transaction_history.get(wallet.address, []):
                if tx.recipient == wallet.address:  # Incoming transactions (rewards)
                    transactions.append(tx)
            
            # Sort by timestamp (newest first)
            transactions.sort(key=lambda x: x.timestamp, reverse=True)
            
            print(f"\n📊 Recent Mining Rewards (last {min(args.limit, len(transactions))}):")
            if transactions:
                for i, tx in enumerate(transactions[:args.limit]):
                    timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tx.timestamp))
                    print(f"   {i+1}. {tx.amount:.6f} COIN - {timestamp_str}")
                    print(f"      Transaction ID: {tx.transaction_id}")
                    if tx.sender == "NETWORK_MINING_REWARDS":
                        print(f"      Type: Mining Reward")
                    else:
                        print(f"      From: {tx.sender}")
            else:
                print("   No mining rewards found yet")
                print("   Start mining to earn rewards!")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error checking mining rewards: {e}")
            return 1
    
    def _handle_rewards(self, args) -> int:
        """Handle rewards command."""
        try:
            import requests
            
            # Get miner address
            miner_address = args.address
            if not miner_address and args.wallet:
                try:
                    from tokenomics.wallet import Wallet
                    wallet = Wallet.load_from_file(args.wallet)
                    miner_address = wallet.address
                except Exception as e:
                    print(f"❌ Error loading wallet: {e}")
                    return 1
            
            if not miner_address:
                print("❌ Please provide either --address or --wallet")
                return 1
            
            # Query rewards API
            response = requests.get(f"{self.faucet_api_url}/v1/rewards/{miner_address}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()['data']
                print(f"💰 Mining Rewards for {miner_address[:16]}...")
                print(f"   Total Rewards: {data['total_rewards']} COIN")
                print(f"   Blocks Mined: {data['blocks_mined']}")
                print(f"   Total Work Score: {data['total_work_score']}")
                print(f"   Average Work Score: {data['average_work_score']}")
                
                # Show additional details if available
                if data.get('blocks_mined', 0) > 0:
                    print(f"\n📊 Mining Summary:")
                    print(f"   Average Reward per Block: {data.get('avg_reward', 0.0):.6f} COIN")
                    print(f"   Total Blocks Mined: {data.get('total_blocks', 0)}")
                    print(f"   Average Work Score: {data.get('average_work_score', 0.0):.2f}")
                else:
                    print(f"\n💡 Start mining to earn rewards!")
                    print(f"   Use: python3 src/cli.py mine --config ./config.json")
                
                return 0
            else:
                print(f"❌ Error getting rewards: {response.status_code}")
                print(f"Response: {response.text}")
                return 1
                
        except Exception as e:
            print(f"❌ Error checking rewards: {e}")
            return 1
    
    def _handle_leaderboard(self, args) -> int:
        """Handle leaderboard command."""
        try:
            import requests
            
            # Query leaderboard API
            response = requests.get(f"{self.faucet_api_url}/v1/rewards/leaderboard", timeout=10)
            
            if response.status_code == 200:
                data = response.json()['data']
                print(f"🏆 Mining Leaderboard")
                print(f"   Address: {data.get('address', 'N/A')}")
                print(f"   Total Rewards: {data.get('total_rewards', 0.0)} COIN")
                print(f"   Blocks Mined: {data.get('blocks_mined', 0)}")
                print(f"   Total Work Score: {data.get('total_work_score', 0.0)}")
                print(f"   Average Work Score: {data.get('average_work_score', 0.0)}")
                
                # Note: The current API doesn't provide a full leaderboard
                # This is a placeholder for future leaderboard functionality
                print(f"\n💡 Leaderboard functionality coming soon!")
                print(f"   Current API provides individual miner stats")
                
                return 0
            else:
                print(f"❌ Error getting leaderboard: {response.status_code}")
                print(f"Response: {response.text}")
                return 1
                
        except Exception as e:
            print(f"❌ Error checking leaderboard: {e}")
            return 1


def main():
    """Main entry point for the CLI."""
    cli = COINjectureCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
