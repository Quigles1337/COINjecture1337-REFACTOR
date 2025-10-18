"""
COINjecture Faucet API Server

Flask-based REST API server for streaming blockchain data.
Implements the specification from FAUCET_API.README.md.
"""

import time
from flask import Flask, jsonify, request, Response  # type: ignore
from flask_cors import CORS  # type: ignore
from flask_limiter import Limiter  # type: ignore
from flask_limiter.util import get_remote_address  # type: ignore
from typing import Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from api.cache_manager import CacheManager
    from api.schema import TelemetryEvent, BlockEvent
    from api.ingest_store import IngestStore
    from api.auth import HMACAuth
    from api.user_auth import auth_manager
    from api.user_registration import user_bp
except ImportError:
    # Fallback for direct execution
    from cache_manager import CacheManager
    from schema import TelemetryEvent, BlockEvent
    from ingest_store import IngestStore
    from auth import HMACAuth
    from user_auth import auth_manager
    from user_registration import user_bp


class FaucetAPI:
    """
    COINjecture Faucet API server.
    
    Provides one-way access to blockchain data via REST endpoints.
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize faucet API.
        
        Args:
            cache_dir: Directory containing cache files
        """
        self.app = Flask(__name__)
        self.cache_manager = CacheManager(cache_dir)
        self.ingest_store = IngestStore()
        # TODO: load from env or config
        self.auth = HMACAuth(secret=os.environ.get("FAUCET_HMAC_SECRET", "dev-secret"))
        
        # Enable CORS for browser access
        CORS(self.app)
        
        # Rate limiting: 100 requests/minute per IP
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["100 per minute"]
        )
        
        # Register user management routes
        self.app.register_blueprint(user_bp)
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register API routes."""
        
        @self.app.route('/', methods=['GET'])
        def root():
            """Root endpoint with API information."""
            return jsonify({
                "name": "COINjecture Faucet API",
                "version": "3.7.0",
                "description": "One-way faucet API for streaming blockchain data",
                "token_name": "COINjecture",
                "token_symbol": "$BEANS",
                "endpoints": {
                    "health": "/health",
                    "latest_block": "/v1/data/block/latest",
                    "block_by_index": "/v1/data/block/{index}",
                    "block_range": "/v1/data/blocks?start={start}&end={end}",
                    "ipfs_data": "/v1/data/ipfs/{cid}",
                    "telemetry_ingest": "/v1/ingest/telemetry",
                    "block_ingest": "/v1/ingest/block",
                    "latest_telemetry": "/v1/display/telemetry/latest",
                    "latest_blocks": "/v1/display/blocks/latest"
                },
                "server": "http://167.172.213.70:5000",
                "status": "operational"
            })
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            cache_info = self.cache_manager.get_cache_info()
            return jsonify({
                "status": "healthy",
                "timestamp": time.time(),
                "cache": cache_info
            })
        
        @self.app.route('/v1/data/block/latest', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_latest_block():
            """Get latest block data."""
            try:
                block_data = self.cache_manager.get_latest_block()
                return jsonify({
                    "status": "success",
                    "data": block_data,
                    "meta": {
                        "cached_at": block_data.get("last_updated", time.time()),
                        "api_version": "v1"
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Cache unavailable",
                    "message": str(e)
                }), 503

        # Ingest: Telemetry
        @self.app.route('/v1/ingest/telemetry', methods=['POST'])
        @self.limiter.limit("10 per minute")
        def ingest_telemetry():
            try:
                headers = request.headers
                sig = headers.get("X-Signature", "")
                ts_hdr = headers.get("X-Timestamp", "0")
                payload = request.get_json(force=True, silent=False) or {}
                ev = TelemetryEvent.from_json(payload)
                if not self.auth.verify(payload, sig, ts_hdr):
                    return jsonify({"status": "error", "error": "UNAUTHORIZED"}), 401
                ok = self.ingest_store.insert_telemetry(payload)
                if not ok:
                    return jsonify({"status": "error", "error": "DUPLICATE"}), 409
                return jsonify({"status": "accepted"}), 202
            except ValueError as ve:
                return jsonify({"status": "error", "error": "INVALID", "message": str(ve)}), 422
            except Exception as e:
                return jsonify({"status": "error", "error": "INTERNAL", "message": str(e)}), 500

        # Ingest: Block events
        @self.app.route('/v1/ingest/block', methods=['POST'])
        @self.limiter.limit("10 per minute")
        def ingest_block():
            try:
                payload = request.get_json(force=True, silent=False) or {}
                
                # DEBUG: Log raw payload
                import json
                print(f"=== RAW PAYLOAD DEBUG ===")
                print(f"Payload: {json.dumps(payload, indent=2)}")
                print(f"Payload keys: {list(payload.keys())}")
                print(f"Payload types: {[(k, type(v).__name__) for k, v in payload.items()]}")
                
                # Validate block event format
                try:
                    ev = BlockEvent.from_json(payload)
                    print(f"✅ BlockEvent validation passed")
                except ValueError as ve:
                    print(f"❌ BlockEvent validation failed: {ve}")
                    return jsonify({
                        "status": "error",
                        "error": "INVALID",
                        "message": str(ve)
                    }), 422
                except Exception as e:
                    print(f"❌ BlockEvent validation error: {type(e).__name__}: {e}")
                    return jsonify({
                        "status": "error",
                        "error": "VALIDATION_ERROR",
                        "message": str(e)
                    }), 422
                
                # Verify wallet signature instead of HMAC
                signature = payload.get('signature', '')
                public_key = payload.get('public_key', '')
                
                if not signature or not public_key:
                    return jsonify({"status": "error", "error": "Missing signature or public_key"}), 400
                
                # Verify with existing Wallet class
                # IMPORTANT: Verify the original data that was signed (without signature and public_key)
                block_data_for_verification = {k: v for k, v in payload.items() 
                                               if k not in ['signature', 'public_key']}
                
                # TEMPORARY DEBUG: Log what we're verifying
                import json
                print(f"=== BACKEND DEBUG ===")
                print(f"Received payload keys: {list(payload.keys())}")
                print(f"Block data for verification: {json.dumps(block_data_for_verification, sort_keys=True)}")
                print(f"Public key: {public_key}")
                print(f"Signature: {signature}")
                
                from tokenomics.wallet import Wallet
                verification_result = Wallet.verify_block_signature(public_key, block_data_for_verification, signature)
                print(f"Signature verification result: {verification_result}")
                
                if not verification_result:
                    return jsonify({"status": "error", "error": "Invalid signature"}), 401
                
                # Store block event
                ok = self.ingest_store.insert_block_event(payload)
                if not ok:
                    return jsonify({"status": "error", "error": "DUPLICATE"}), 409
                
                return jsonify({
                    "status": "accepted",
                    "miner_address": payload.get('miner_address')
                }), 202
            except ValueError as ve:
                return jsonify({"status": "error", "error": "INVALID", "message": str(ve)}), 422
            except Exception as e:
                return jsonify({"status": "error", "error": "INTERNAL", "message": str(e)}), 500

        # Display: latest telemetry
        @self.app.route('/v1/display/telemetry/latest', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def display_latest_telemetry():
            try:
                limit = request.args.get('limit', default=20, type=int)
                data = self.ingest_store.latest_telemetry(limit=limit)
                return jsonify({"status": "success", "data": data})
            except Exception as e:
                return jsonify({"status": "error", "error": "INTERNAL", "message": str(e)}), 500

        # Display: latest blocks
        @self.app.route('/v1/display/blocks/latest', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def display_latest_blocks():
            try:
                limit = request.args.get('limit', default=20, type=int)
                data = self.ingest_store.latest_blocks(limit=limit)
                return jsonify({"status": "success", "data": data})
            except Exception as e:
                return jsonify({"status": "error", "error": "INTERNAL", "message": str(e)}), 500
        
        @self.app.route('/v1/data/block/<int:index>', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_block_by_index(index: int):
            """Get block data by index."""
            try:
                # Validate index
                if index < 0:
                    return jsonify({
                        "status": "error",
                        "error": "Invalid block index",
                        "message": "Block index must be non-negative"
                    }), 400
                
                block_data = self.cache_manager.get_block_by_index(index)
                if block_data is None:
                    return jsonify({
                        "status": "error",
                        "error": "Block not found",
                        "message": f"Block with index {index} not found"
                    }), 404
                
                return jsonify({
                    "status": "success",
                    "data": block_data,
                    "meta": {
                        "cached_at": block_data.get("last_updated", time.time()),
                        "api_version": "v1"
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/data/blocks', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_blocks_range():
            """Get range of blocks."""
            try:
                # Get query parameters
                start = request.args.get('start', type=int)
                end = request.args.get('end', type=int)
                
                if start is None or end is None:
                    return jsonify({
                        "status": "error",
                        "error": "Missing parameters",
                        "message": "Both 'start' and 'end' parameters are required"
                    }), 400
                
                # Validate range
                if start < 0 or end < 0:
                    return jsonify({
                        "status": "error",
                        "error": "Invalid range",
                        "message": "Start and end must be non-negative"
                    }), 400
                
                if start > end:
                    return jsonify({
                        "status": "error",
                        "error": "Invalid range",
                        "message": "Start must be less than or equal to end"
                    }), 400
                
                # Limit range size
                if end - start > 100:
                    return jsonify({
                        "status": "error",
                        "error": "Range too large",
                        "message": "Range cannot exceed 100 blocks"
                    }), 400
                
                blocks = self.cache_manager.get_blocks_range(start, end)
                
                return jsonify({
                    "status": "success",
                    "data": blocks,
                    "meta": {
                        "count": len(blocks),
                        "range": f"{start}-{end}",
                        "api_version": "v1"
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/data/ipfs/<cid>', methods=['GET'])
        @self.limiter.limit("50 per minute")
        def get_ipfs_data(cid: str):
            """Get IPFS data by CID (placeholder for future implementation)."""
            return jsonify({
                "status": "error",
                "error": "Not implemented",
                "message": "IPFS integration coming soon"
            }), 501
        
        # ============================================
        # WALLET ENDPOINTS
        # ============================================
        
        @self.app.route('/v1/wallet/create', methods=['POST'])
        @self.limiter.limit("10 per minute")
        def create_wallet():
            """Create new wallet."""
            try:
                data = request.get_json() or {}
                name = data.get('name', f'wallet_{int(time.time())}')
                
                # Import wallet manager
                from tokenomics.wallet import WalletManager
                manager = WalletManager()
                
                wallet = manager.create_wallet(name)
                if wallet:
                    return jsonify({
                        "status": "success",
                        "wallet": {
                            "address": wallet.address,
                            "name": name,
                            "public_key": wallet.get_public_key_bytes().hex()
                        }
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "error": "Failed to create wallet"
                    }), 500
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/wallet/<address>/balance', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_wallet_balance(address: str):
            """Get wallet balance."""
            try:
                # Import blockchain state
                from tokenomics.blockchain_state import BlockchainState
                state = BlockchainState()
                
                balance = state.get_balance(address)
                return jsonify({
                    "status": "success",
                    "address": address,
                    "balance": balance
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/wallet/<address>/transactions', methods=['GET'])
        @self.limiter.limit("50 per minute")
        def get_wallet_transactions(address: str):
            """Get wallet transaction history."""
            try:
                limit = request.args.get('limit', 100, type=int)
                
                # Import blockchain state
                from tokenomics.blockchain_state import BlockchainState
                state = BlockchainState()
                
                transactions = state.get_transaction_history(address, limit)
                return jsonify({
                    "status": "success",
                    "address": address,
                    "transactions": [tx.to_dict() for tx in transactions],
                    "count": len(transactions)
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        # ============================================
        # TRANSACTION ENDPOINTS
        # ============================================
        
        @self.app.route('/v1/transaction/send', methods=['POST'])
        @self.limiter.limit("20 per minute")
        def send_transaction():
            """Submit transaction to pool."""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        "status": "error",
                        "error": "No transaction data provided"
                    }), 400
                
                # Import blockchain state
                from tokenomics.blockchain_state import BlockchainState, Transaction
                state = BlockchainState()
                
                # Create transaction
                transaction = Transaction(
                    sender=data['sender'],
                    recipient=data['recipient'],
                    amount=float(data['amount']),
                    timestamp=time.time()
                )
                
                # Sign transaction if private key provided
                if 'private_key' in data:
                    private_key_bytes = bytes.fromhex(data['private_key'])
                    transaction.sign(private_key_bytes)
                
                # Add to pool
                if state.add_transaction(transaction):
                    return jsonify({
                        "status": "success",
                        "transaction": transaction.to_dict()
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "error": "Transaction validation failed"
                    }), 400
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/transaction/pending', methods=['GET'])
        @self.limiter.limit("50 per minute")
        def get_pending_transactions():
            """Get pending transactions."""
            try:
                limit = request.args.get('limit', 100, type=int)
                
                # Import blockchain state
                from tokenomics.blockchain_state import BlockchainState
                state = BlockchainState()
                
                pending = state.get_pending_transactions(limit)
                return jsonify({
                    "status": "success",
                    "transactions": [tx.to_dict() for tx in pending],
                    "count": len(pending)
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/transaction/<tx_id>', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_transaction(tx_id: str):
            """Get transaction by ID."""
            try:
                # Import blockchain state
                from tokenomics.blockchain_state import BlockchainState
                state = BlockchainState()
                
                transaction = state.get_transaction_by_id(tx_id)
                if transaction:
                    return jsonify({
                        "status": "success",
                        "transaction": transaction.to_dict()
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "error": "Transaction not found"
                    }), 404
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/ingest/block', methods=['POST'])
        @self.limiter.limit("10 per minute")
        def ingest_block_submission():
            """Accept mined blocks from CLI clients."""
            try:
                data = request.get_json()
                if not data or 'block' not in data:
                    return jsonify({
                        "status": "error",
                        "error": "Missing block data"
                    }), 400
                
                block_data = data['block']
                peer_id = data.get('peer_id', 'unknown')
                signature = data.get('signature', None)
                
                # Import required modules
                from core.blockchain import Block, Transaction
                from consensus import ConsensusEngine, ConsensusConfig
                from storage import StorageManager, StorageConfig, NodeRole, PruningMode
                
                # Create storage manager
                storage_config = StorageConfig(
                    data_dir="data",
                    role=NodeRole.FULL,
                    pruning_mode=PruningMode.FULL,
                    ipfs_api_url="http://localhost:5001"
                )
                storage_manager = StorageManager(storage_config)
                
                # Create consensus engine
                consensus_config = ConsensusConfig()
                consensus = ConsensusEngine(consensus_config, storage_manager, None)
                
                # Validate block structure
                required_fields = ['index', 'timestamp', 'previous_hash', 'transactions', 'merkle_root', 'block_hash']
                for field in required_fields:
                    if field not in block_data:
                        return jsonify({
                            "status": "error",
                            "error": f"Missing required field: {field}"
                        }), 400
                
                # Convert transactions back to Transaction objects
                transactions = []
                for tx_data in block_data.get('transactions', []):
                    if isinstance(tx_data, dict):
                        tx = Transaction.from_dict(tx_data)
                        transactions.append(tx)
                    else:
                        transactions.append(tx_data)
                
                # Create Block object
                block = Block(
                    index=block_data['index'],
                    timestamp=block_data['timestamp'],
                    previous_hash=block_data['previous_hash'],
                    transactions=transactions,
                    merkle_root=block_data['merkle_root'],
                    block_hash=block_data['block_hash'],
                    problem=block_data.get('problem'),
                    solution=block_data.get('solution'),
                    complexity=block_data.get('complexity'),
                    mining_capacity=block_data.get('mining_capacity'),
                    cumulative_work_score=block_data.get('cumulative_work_score', 0),
                    offchain_cid=block_data.get('offchain_cid')
                )
                
                # Validate block
                if not consensus.validate_header(block):
                    return jsonify({
                        "status": "error",
                        "error": "Block validation failed"
                    }), 400
                
                # Store block
                try:
                    storage_manager.store_block(block)
                    
                    # Update cache
                    self.cache_manager.update_cache()
                    
                    return jsonify({
                        "status": "success",
                        "message": f"Block {block.index} accepted",
                        "block_hash": block.block_hash,
                        "index": block.index
                    })
                    
                except Exception as e:
                    return jsonify({
                        "status": "error",
                        "error": "Failed to store block",
                        "message": str(e)
                    }), 500
                    
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/rewards/<address>', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_mining_rewards(address: str):
            """Get mining rewards earned by a specific address."""
            try:
                # Get block events for this miner
                block_events = self.ingest_store.latest_blocks(limit=1000)
                miner_events = [event for event in block_events if event.get('miner_address') == address]
                
                if not miner_events:
                    return jsonify({
                        "status": "success",
                        "data": {
                            "miner_address": address,
                            "total_rewards": 0.0,
                            "blocks_mined": 0,
                            "rewards_breakdown": [],
                            "total_work_score": 0.0
                        }
                    }), 200
                
                # Calculate rewards (50 COIN per block + work score bonus)
                rewards_breakdown = []
                total_rewards = 0.0
                total_work_score = 0.0
                
                for event in miner_events:
                    work_score = event.get('work_score', 0.0)
                    base_reward = 50.0  # Base mining reward
                    work_bonus = work_score * 0.1  # 0.1 COIN per work score point
                    block_reward = base_reward + work_bonus
                    
                    rewards_breakdown.append({
                        "block_index": event.get('block_index'),
                        "block_hash": event.get('block_hash'),
                        "work_score": work_score,
                        "base_reward": base_reward,
                        "work_bonus": work_bonus,
                        "total_reward": block_reward,
                        "timestamp": event.get('ts'),
                        "cid": event.get('cid')
                    })
                    
                    total_rewards += block_reward
                    total_work_score += work_score
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "miner_address": address,
                        "total_rewards": round(total_rewards, 2),
                        "blocks_mined": len(miner_events),
                        "rewards_breakdown": rewards_breakdown,
                        "total_work_score": round(total_work_score, 2),
                        "average_work_score": round(total_work_score / len(miner_events), 2) if miner_events else 0.0
                    }
                }), 200
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Failed to get mining rewards",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/rewards/leaderboard', methods=['GET'])
        @self.limiter.limit("50 per minute")
        def get_mining_leaderboard():
            """Get mining leaderboard showing top miners by rewards."""
            try:
                # Get all block events
                block_events = self.ingest_store.latest_blocks(limit=10000)
                
                # Group by miner address
                miner_stats = {}
                for event in block_events:
                    miner_address = event.get('miner_address')
                    if not miner_address:
                        continue
                    
                    if miner_address not in miner_stats:
                        miner_stats[miner_address] = {
                            'address': miner_address,
                            'blocks_mined': 0,
                            'total_work_score': 0.0,
                            'total_rewards': 0.0
                        }
                    
                    work_score = event.get('work_score', 0.0)
                    base_reward = 50.0
                    work_bonus = work_score * 0.1
                    block_reward = base_reward + work_bonus
                    
                    miner_stats[miner_address]['blocks_mined'] += 1
                    miner_stats[miner_address]['total_work_score'] += work_score
                    miner_stats[miner_address]['total_rewards'] += block_reward
                
                # Sort by total rewards
                leaderboard = sorted(
                    miner_stats.values(),
                    key=lambda x: x['total_rewards'],
                    reverse=True
                )
                
                # Round values for display
                for miner in leaderboard:
                    miner['total_rewards'] = round(miner['total_rewards'], 2)
                    miner['total_work_score'] = round(miner['total_work_score'], 2)
                    miner['average_work_score'] = round(
                        miner['total_work_score'] / miner['blocks_mined'], 2
                    ) if miner['blocks_mined'] > 0 else 0.0
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "leaderboard": leaderboard[:50],  # Top 50 miners
                        "total_miners": len(leaderboard),
                        "total_blocks": sum(m['blocks_mined'] for m in leaderboard),
                        "total_rewards_distributed": round(sum(m['total_rewards'] for m in leaderboard), 2)
                    }
                }), 200
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Failed to get mining leaderboard",
                    "message": str(e)
                }), 500
        
        # Error handlers
        @self.app.errorhandler(429)
        def ratelimit_handler(e):
            """Handle rate limit exceeded."""
            return jsonify({
                "status": "error",
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": e.retry_after
            }), 429
        
        @self.app.errorhandler(404)
        def not_found_handler(e):
            """Handle 404 errors."""
            return jsonify({
                "status": "error",
                "error": "Not found",
                "message": "The requested resource was not found"
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error_handler(e):
            """Handle 500 errors."""
            return jsonify({
                "status": "error",
                "error": "Internal server error",
                "message": "An unexpected error occurred"
            }), 500
    
    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """
        Run the API server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        print(f"🚰 COINjecture Faucet API starting on {host}:{port}")
        print(f"📊 Cache directory: {self.cache_manager.cache_dir}")
        print(f"🔗 Health check: http://{host}:{port}/health")
        print(f"📈 Latest block: http://{host}:{port}/v1/data/block/latest")
        
        self.app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    # Create and run API server
    api = FaucetAPI()
    api.run(debug=True)
