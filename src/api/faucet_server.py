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
        self.ingest_store = IngestStore("/opt/coinjecture-consensus/data/faucet_ingest.db")
        # TODO: load from env or config
        self.auth = HMACAuth(secret=os.environ.get("FAUCET_HMAC_SECRET", "dev-secret"))
        
        # Enable CORS for browser access
        CORS(self.app, 
            origins=["https://coinjecture.com", "https://www.coinjecture.com", "https://api.coinjecture.com", "https://d3srwqcuj8kw0l.cloudfront.net"],
            methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization", "X-User-ID", "X-Timestamp", "X-Signature"],
            supports_credentials=True)
        
        # Rate limiting: 100 requests/minute per IP
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["100 per minute"]
        )
        
        # Register user management routes
        self.app.register_blueprint(user_bp)
        
        # Register problem submission blueprint
        from api.problem_endpoints import problem_bp
        self.app.register_blueprint(problem_bp)
        
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
                    "all_blocks": "/v1/data/blocks/all",
                    "ipfs_data": "/v1/data/ipfs/{cid}",
                    "ipfs_list": "/v1/data/ipfs/list",
                    "ipfs_search": "/v1/data/ipfs/search?q={query}",
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
        @self.limiter.limit("60 per minute")
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
                
                # TEMPORARY: Accept demo signatures for testing
                if not verification_result and (signature.startswith('demo_signature_') or public_key == 'demo-public-key'):
                    print("⚠️  WARNING: Accepting demo signature for testing")
                    verification_result = True
                
                if not verification_result:
                    return jsonify({"status": "error", "error": "Invalid signature"}), 401
                
                # Store block event
                ok = self.ingest_store.insert_block_event(payload)
                if not ok:
                    return jsonify({"status": "error", "error": "DUPLICATE"}), 409
                
                # Auto-register wallet on first mining submission
                miner_address = payload.get('miner_address')
                if miner_address:
                    self._ensure_wallet_registered(miner_address, public_key)
                
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
        
        @self.app.route('/v1/data/blocks/all', methods=['GET'])
        @self.limiter.limit("50 per minute")
        def get_all_blocks():
            """Get all blocks in the blockchain."""
            try:
                # Get all blocks from cache
                all_blocks = self.cache_manager.get_all_blocks()
                
                return jsonify({
                    "status": "success",
                    "data": all_blocks,
                    "meta": {
                        "total_blocks": len(all_blocks),
                        "api_version": "v1",
                        "cached_at": time.time()
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
            """Get IPFS data by CID."""
            try:
                # Try to get IPFS data from cache
                ipfs_data = self.cache_manager.get_ipfs_data(cid)
                if ipfs_data:
                    return jsonify({
                        "status": "success",
                        "data": ipfs_data,
                        "meta": {
                            "cid": cid,
                            "api_version": "v1"
                        }
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "error": "IPFS data not found",
                        "message": f"CID {cid} not found in cache"
                    }), 404
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500

        @self.app.route('/v1/data/ipfs/list', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def list_ipfs_data():
            """List all available IPFS CIDs."""
            try:
                # Get list of all IPFS CIDs from cache
                ipfs_list = self.cache_manager.list_ipfs_cids()
                
                return jsonify({
                    "status": "success",
                    "data": ipfs_list,
                    "meta": {
                        "total_cids": len(ipfs_list),
                        "api_version": "v1"
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500

        @self.app.route('/v1/data/ipfs/search', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def search_ipfs_data():
            """Search IPFS data by content or metadata."""
            try:
                query = request.args.get('q', '')
                if not query:
                    return jsonify({
                        "status": "error",
                        "error": "Missing query parameter",
                        "message": "Query parameter 'q' is required"
                    }), 400
                
                # Search IPFS data
                results = self.cache_manager.search_ipfs_data(query)
                
                return jsonify({
                    "status": "success",
                    "data": results,
                    "meta": {
                        "query": query,
                        "results_count": len(results),
                        "api_version": "v1"
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/peers', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_peers():
            """Get network peers and mining activity information."""
            try:
                # Get real network statistics from database
                import sqlite3
                
                # Connect to the database
                db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Get unique miners (active nodes)
                    cursor.execute("""
                        SELECT DISTINCT miner_address, COUNT(*) as block_count, MAX(created_at) as last_activity
                        FROM block_events 
                        WHERE miner_address IS NOT NULL 
                        GROUP BY miner_address 
                        ORDER BY block_count DESC
                        LIMIT 20
                    """)
                    miners = cursor.fetchall()
                    
                    # Get network statistics
                    cursor.execute("SELECT COUNT(DISTINCT miner_address) FROM block_events WHERE miner_address IS NOT NULL")
                    unique_miners = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM block_events")
                    total_blocks = cursor.fetchone()[0]
                    
                    # Get the real block count from consensus service API
                    try:
                        import requests
                        consensus_response = requests.get('http://localhost:5000/v1/consensus/status', timeout=5)
                        if consensus_response.status_code == 200:
                            consensus_data = consensus_response.json()
                            real_block_count = consensus_data.get('data', {}).get('total_blocks', 0)
                            if real_block_count > total_blocks:
                                total_blocks = real_block_count
                    except:
                        # Fallback to blockchain_state.json if consensus API not available
                        blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
                        if os.path.exists(blockchain_state_path):
                            import json
                            with open(blockchain_state_path, 'r') as f:
                                blockchain_data = json.load(f)
                                real_block_count = blockchain_data.get('latest_block_index', 0) + 1
                                if real_block_count > total_blocks:
                                    total_blocks = real_block_count
                    
                    conn.close()
                    
                    # Format peer data based on actual miners
                    peers = []
                    for i, (miner_address, block_count, last_activity) in enumerate(miners):
                        peers.append({
                            "peer_id": f"miner_{i+1:03d}",
                            "address": miner_address,
                            "status": "active",
                            "last_seen": int(last_activity) if last_activity else int(time.time()),
                            "protocol_version": "v3.10.2",
                            "blocks_mined": block_count,
                            "reputation": min(block_count / 100.0, 1.0)  # Reputation based on blocks mined
                        })
                    
                    return jsonify({
                        "status": "success",
                        "data": {
                            "peers": peers,
                            "total_peers": unique_miners,
                            "active_miners": len(peers),
                            "total_blocks": total_blocks,
                            "network_status": "active",
                            "network_type": "mining_network"
                        }
                    })
                else:
                    # Fallback if database not available
                    return jsonify({
                        "status": "success",
                        "data": {
                            "peers": [],
                            "total_peers": 0,
                            "active_miners": 0,
                            "total_blocks": 0,
                            "network_status": "database_unavailable",
                            "message": "Database not accessible"
                        }
                    })
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/metrics/dashboard', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_dashboard_metrics():
            """Get comprehensive blockchain explorer metrics for dashboard display."""
            try:
                import sqlite3
                import time
                from datetime import datetime, timedelta
                
                # Connect to database
                db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
                if not os.path.exists(db_path):
                    return jsonify({
                        "status": "error",
                        "message": "Database not available"
                    }), 500
                
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                current_time = time.time()
                
                # Get consecutive blockchain blocks
                cursor.execute("""
                    SELECT block_index, block_hash, created_at, miner_address, work_score, capacity
                    FROM consecutive_blockchain 
                    ORDER BY block_index DESC
                """)
                consecutive_blocks = cursor.fetchall()
                
                # Get latest block
                latest_block = consecutive_blocks[0] if consecutive_blocks else None
                
                # Count consecutive blocks (true blockchain)
                consecutive_count = len(consecutive_blocks)
                
                # Get total mining events (for reference, but not primary metric)
                cursor.execute("SELECT COUNT(*) FROM block_events")
                total_mining_events = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT miner_address) FROM block_events WHERE miner_address IS NOT NULL")
                unique_miners = cursor.fetchone()[0]
                
                # Calculate TPS for different time windows (using consecutive blockchain)
                def calculate_tps(minutes):
                    start_time = current_time - (minutes * 60)
                    cursor.execute("""
                        SELECT COUNT(*) FROM consecutive_blockchain 
                        WHERE created_at >= ?
                    """, (start_time,))
                    block_count = cursor.fetchone()[0]
                    return block_count / (minutes * 60) if minutes > 0 else 0
                
                tps_1min = calculate_tps(1)
                tps_5min = calculate_tps(5)
                tps_1hour = calculate_tps(60)
                tps_24hour = calculate_tps(1440)
                
                # Calculate block time (average time between winning blocks)
                cursor.execute("""
                    SELECT created_at FROM (
                        SELECT DISTINCT block_index, MIN(created_at) as created_at 
                        FROM block_events 
                        GROUP BY block_index
                        ORDER BY created_at DESC 
                        LIMIT 100
                    )
                """)
                recent_times = [row[0] for row in cursor.fetchall()]
                
                block_times = []
                for i in range(len(recent_times) - 1):
                    block_times.append(recent_times[i] - recent_times[i + 1])
                
                avg_block_time = sum(block_times) / len(block_times) if block_times else 0
                median_block_time = sorted(block_times)[len(block_times)//2] if block_times else 0
                
                # Calculate hash rate (work score per second) for different periods
                def calculate_hash_rate(minutes):
                    start_time = current_time - (minutes * 60)
                    cursor.execute("""
                        SELECT SUM(work_score) FROM block_events 
                        WHERE created_at >= ?
                    """, (start_time,))
                    total_work_score = cursor.fetchone()[0] or 0
                    return total_work_score / (minutes * 60) if minutes > 0 else 0
                
                hash_rate_1min = calculate_hash_rate(1)
                hash_rate_5min = calculate_hash_rate(5)
                hash_rate_1hour = calculate_hash_rate(60)
                
                # Get network difficulty (average work score)
                cursor.execute("""
                    SELECT AVG(work_score) FROM block_events 
                    WHERE created_at >= ?
                """, (current_time - 3600,))  # Last hour
                avg_difficulty = cursor.fetchone()[0] or 0
                
                # Get consensus status
                try:
                    import requests
                    consensus_response = requests.get('http://localhost:5000/v1/consensus/status', timeout=5)
                    if consensus_response.status_code == 200:
                        consensus_data = consensus_response.json()
                        consensus_active = consensus_data.get('data', {}).get('consensus_active', False)
                        network_height = consensus_data.get('data', {}).get('network_height', 0)
                        last_block_hash = consensus_data.get('data', {}).get('last_block_hash', '')
                    else:
                        consensus_active = False
                        network_height = 0
                        last_block_hash = ''
                except:
                    consensus_active = False
                    network_height = 0
                    last_block_hash = ''
                
                # Get peer count
                try:
                    peers_response = requests.get('http://localhost:5000/v1/peers', timeout=5)
                    if peers_response.status_code == 200:
                        peers_data = peers_response.json()
                        peer_count = peers_data.get('data', {}).get('total_peers', 0)
                        active_miners = peers_data.get('data', {}).get('active_miners', 0)
                    else:
                        peer_count = 0
                        active_miners = 0
                except:
                    peer_count = 0
                    active_miners = 0
                
                # Calculate energy efficiency
                cursor.execute("""
                    SELECT COUNT(*) as problems_solved, 
                           SUM(work_score) as total_work_score,
                           AVG(work_score) as avg_work_score
                    FROM block_events 
                    WHERE created_at >= ?
                """, (current_time - 3600,))  # Last hour
                efficiency_data = cursor.fetchone()
                problems_solved_1h = efficiency_data[0] or 0
                total_work_score_1h = efficiency_data[1] or 0
                avg_work_score_1h = efficiency_data[2] or 0
                
                # Calculate total rewards distributed
                cursor.execute("""
                    SELECT SUM(total_rewards) FROM work_based_rewards
                """)
                total_rewards = cursor.fetchone()[0] or 0
                
                # Get recent transactions (blocks) for explorer from consecutive blockchain
                cursor.execute("""
                    SELECT block_index, block_hash, miner_address, work_score, created_at, capacity, previous_hash, merkle_root, cid
                    FROM consecutive_blockchain 
                    ORDER BY block_index DESC 
                    LIMIT 10
                """)
                recent_transactions = []
                for row in cursor.fetchall():
                    # Format timestamp for display
                    timestamp_display = datetime.fromtimestamp(row[4]).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Calculate gas used based on work score and capacity
                    base_gas = 21000  # Base gas for transaction
                    capacity_multiplier = {"mobile": 1.0, "desktop": 2.0, "server": 3.0}.get(row[5].lower(), 1.0)
                    work_gas = int(row[3] * 1000)  # Work score to gas conversion
                    gas_used = int(base_gas + (work_gas * capacity_multiplier))
                    
                    recent_transactions.append({
                        "block_index": row[0],
                        "block_hash": row[1],
                        "block_hash_short": row[1][:16] + "...",
                        "miner": row[2],
                        "miner_short": row[2][:20] + "..." if len(row[2]) > 20 else row[2],
                        "work_score": round(row[3], 2),
                        "timestamp": row[4],
                        "timestamp_display": timestamp_display,
                        "capacity": row[5],
                        "previous_hash": row[6],
                        "previous_hash_short": row[6][:16] + "..." if row[6] else "N/A",
                        "merkle_root": row[7],
                        "merkle_root_short": row[7][:16] + "..." if row[7] else "N/A",
                        "cid": row[8] if row[8] else "N/A",
                        "cid_short": (row[8][:20] + "...") if row[8] else "N/A",
                        "gas_used": gas_used,
                        "gas_used_formatted": f"{gas_used:,}",
                        "age_seconds": int(current_time - row[4]),
                        "age_display": self._format_age(current_time - row[4])
                    })
                
                conn.close()
                
                # Calculate trends
                tps_trend = "→"
                if tps_1min > tps_5min * 1.1:
                    tps_trend = "↑"
                elif tps_1min < tps_5min * 0.9:
                    tps_trend = "↓"
                
                hash_trend = "→"
                if hash_rate_1min > hash_rate_5min * 1.1:
                    hash_trend = "↑"
                elif hash_rate_1min < hash_rate_5min * 0.9:
                    hash_trend = "↓"
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "blockchain": {
                            "validated_blocks": consecutive_count,
                            "latest_block": latest_block[0] if latest_block else 0,
                            "latest_hash": latest_block[1][:16] + "..." if latest_block else "N/A",
                            "consensus_active": consensus_active,
                            "mining_attempts": total_mining_events,
                            "success_rate": round((consecutive_count / total_mining_events * 100), 2) if total_mining_events > 0 else 0
                        },
                        "transactions": {
                            "tps_current": round(tps_1min, 2),
                            "tps_1min": round(tps_1min, 2),
                            "tps_5min": round(tps_5min, 2),
                            "tps_1hour": round(tps_1hour, 2),
                            "tps_24hour": round(tps_24hour, 2),
                            "trend": tps_trend
                        },
                        "block_time": {
                            "avg_seconds": round(avg_block_time, 2),
                            "median_seconds": round(median_block_time, 2),
                            "last_100_blocks": round(avg_block_time, 2)
                        },
                        "hash_rate": {
                            "current_hs": round(hash_rate_1min, 2),
                            "5min_hs": round(hash_rate_5min, 2),
                            "1hour_hs": round(hash_rate_1hour, 2),
                            "unit": "work_score/s",
                            "trend": hash_trend
                        },
                        "network": {
                            "active_peers": peer_count,
                            "active_miners": active_miners,
                            "unique_miners": unique_miners,
                            "avg_difficulty": round(avg_difficulty, 2)
                        },
                        "efficiency": {
                            "problems_solved_1h": problems_solved_1h,
                            "total_work_score_1h": round(total_work_score_1h, 2),
                            "avg_work_score_1h": round(avg_work_score_1h, 2),
                            "efficiency_ratio": round(problems_solved_1h / max(total_work_score_1h, 1), 4)
                        },
                        "rewards": {
                            "total_distributed": round(total_rewards, 2),
                            "unit": "BEANS"
                        },
                        "recent_transactions": recent_transactions,
                        "last_updated": current_time
                    }
                })
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/consensus/status', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_consensus_status():
            """Get consensus engine status and blockchain statistics."""
            try:
                # Get latest block data
                latest_block = self.cache_manager.get_latest_block()
                
                # Get total block count from database (use max block_index as total submissions)
                try:
                    import sqlite3
                    db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute('SELECT MAX(block_index) FROM block_events')
                    total_blocks = cursor.fetchone()[0] or 0
                    conn.close()
                except Exception:
                    # Fallback to blockchain state file
                    import json
                    blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
                    try:
                        with open(blockchain_state_path, 'r') as f:
                            blockchain_data = json.load(f)
                        total_blocks = len(blockchain_data.get('blocks', []))
                    except Exception:
                        # Final fallback to cache manager
                        all_blocks = self.cache_manager.get_all_blocks()
                        total_blocks = len(all_blocks)
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "consensus_active": True,
                        "latest_block_index": latest_block.get("index", 0),
                        "total_blocks": total_blocks,
                        "network_height": latest_block.get("index", 0),
                        "consensus_engine": "operational",
                        "last_block_hash": latest_block.get("block_hash", ""),
                        "timestamp": time.time()
                    },
                    "meta": {
                        "api_version": "v1",
                        "cached_at": time.time()
                    }
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
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
        
        @self.app.route('/v1/ingest/block/cli', methods=['POST'])
        @self.limiter.limit("60 per minute")
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
            """Get mining rewards earned by a specific address based on work completed."""
            try:
                # First try to get from work_based_rewards table (new system)
                try:
                    import sqlite3
                    db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT total_rewards, blocks_mined, total_work_score, average_reward 
                        FROM work_based_rewards 
                        WHERE miner_address = ?
                    ''', (address,))
                    
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result:
                        total_rewards, blocks_mined, total_work_score, average_reward = result
                        return jsonify({
                            "status": "success",
                            "data": {
                                "miner_address": address,
                                "total_rewards": total_rewards,
                                "blocks_mined": blocks_mined,
                                "rewards_breakdown": [{"block": i+1, "reward": average_reward} for i in range(blocks_mined)],
                                "total_work_score": total_work_score,
                                "average_work_score": total_work_score / blocks_mined if blocks_mined > 0 else 0,
                                "tokenomics_version": "dynamic_work_score",
                                "reward_formula": "log(1 + work_ratio) * deflation_factor * diversity_bonus",
                                "explanation": {
                                    "work_ratio": "This block's work score relative to recent network average",
                                    "deflation_factor": "Decreases as cumulative work grows (natural deflation)",
                                    "diversity_bonus": "Bonus for underrepresented mining capacities"
                                }
                            }
                        }), 200
                except Exception as e:
                    print(f"Work-based rewards lookup failed: {e}")
                
                # Fallback to old system if work_based_rewards not found
                block_events = self.cache_manager.get_all_blocks()
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
                
                # Calculate rewards based on work completed
                rewards_breakdown = []
                total_rewards = 0.0
                total_work_score = 0.0
                
                for event in miner_events:
                    work_score = event.get('work_score', 0.0)
                    cumulative_work = event.get('cumulative_work_score', 0.0)
                    base_reward = 50.0  # Base mining reward
                    work_bonus = work_score * 0.1  # 0.1 COIN per work score point
                    cumulative_bonus = cumulative_work * 0.001  # Bonus for cumulative work
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
                # Get all block events from blockchain state
                block_events = self.cache_manager.get_all_blocks()
                
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
        
        # ============================================
        # WALLET PERSISTENCE ENDPOINTS
        # ============================================
        
        @self.app.route('/v1/wallet/register', methods=['POST'])
        @self.limiter.limit("10 per minute")
        def register_wallet():
            """Register wallet for persistence and IPFS data access."""
            try:
                payload = request.get_json() or {}
                
                # Required fields
                wallet_address = payload.get('wallet_address')
                public_key = payload.get('public_key')
                signature = payload.get('signature')
                device = payload.get('device', 'web')
                
                if not wallet_address or not public_key or not signature:
                    return jsonify({
                        "status": "error",
                        "error": "Missing required fields",
                        "message": "wallet_address, public_key, and signature are required"
                    }), 400
                
                # Optional fields
                mnemonic_hash = payload.get('mnemonic_hash')
                
                # Verify signature to prove ownership
                message = f"register:{wallet_address}:{int(time.time())}"
                if not self._verify_wallet_signature(message, signature, public_key):
                    return jsonify({
                        "status": "error",
                        "error": "Invalid signature",
                        "message": "Signature verification failed"
                    }), 401
                
                # Store in wallet_registry
                import sqlite3
                db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                current_time = int(time.time())
                
                # Check if wallet already exists
                cursor.execute('SELECT wallet_address FROM wallet_registry WHERE wallet_address = ?', (wallet_address,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update last active timestamp
                    cursor.execute('''
                        UPDATE wallet_registry 
                        SET last_active_timestamp = ?, wallet_metadata = ?
                        WHERE wallet_address = ?
                    ''', (current_time, '{"last_registration": ' + str(current_time) + '}', wallet_address))
                else:
                    # Insert new wallet
                    cursor.execute('''
                        INSERT INTO wallet_registry 
                        (wallet_address, public_key, mnemonic_hash, first_seen_timestamp, 
                         last_active_timestamp, created_from_device, wallet_metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (wallet_address, public_key, mnemonic_hash, current_time, 
                          current_time, device, '{"first_registration": ' + str(current_time) + '}'))
                
                conn.commit()
                conn.close()
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "wallet_address": wallet_address,
                        "registered": True,
                        "device": device,
                        "timestamp": current_time
                    }
                })
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/wallet/verify', methods=['POST'])
        @self.limiter.limit("10 per minute")
        def verify_wallet():
            """Verify wallet ownership using recovery phrase."""
            try:
                payload = request.get_json() or {}
                
                wallet_address = payload.get('wallet_address')
                mnemonic_hash = payload.get('mnemonic_hash')
                
                if not wallet_address or not mnemonic_hash:
                    return jsonify({
                        "status": "error",
                        "error": "Missing required fields",
                        "message": "wallet_address and mnemonic_hash are required"
                    }), 400
                
                # Check if wallet exists in registry
                import sqlite3
                db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT mnemonic_hash, total_blocks_mined, total_rewards, first_seen_timestamp
                    FROM wallet_registry
                    WHERE wallet_address = ?
                ''', (wallet_address,))
                
                result = cursor.fetchone()
                conn.close()
                
                if not result:
                    return jsonify({
                        "status": "error",
                        "error": "Wallet not found",
                        "message": "Wallet address not registered"
                    }), 404
                
                stored_mnemonic_hash, blocks_mined, total_rewards, first_seen = result
                
                if stored_mnemonic_hash != mnemonic_hash:
                    return jsonify({
                        "status": "error",
                        "error": "Invalid recovery phrase",
                        "message": "Mnemonic hash does not match"
                    }), 401
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "wallet_verified": True,
                        "wallet_address": wallet_address,
                        "blocks_mined": blocks_mined,
                        "total_rewards": total_rewards,
                        "first_seen": first_seen,
                        "verified_at": int(time.time())
                    }
                })
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        # ============================================
        # IPFS DATA ENDPOINTS
        # ============================================
        
        @self.app.route('/v1/ipfs/user/<address>', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_user_ipfs_data(address: str):
            """Get all IPFS data generated by a wallet address."""
            try:
                # Query parameters
                limit = request.args.get('limit', 100, type=int)
                offset = request.args.get('offset', 0, type=int)
                
                # Query block_events for this user's CIDs
                import sqlite3
                db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        block_index,
                        block_hash,
                        cid,
                        work_score,
                        capacity,
                        ts,
                        sig,
                        created_at
                    FROM block_events
                    WHERE miner_address = ?
                    ORDER BY block_index DESC
                    LIMIT ? OFFSET ?
                ''', (address, limit, offset))
                
                events = cursor.fetchall()
                conn.close()
                
                # Format response
                ipfs_data = []
                for event in events:
                    ipfs_data.append({
                        "block_index": event[0],
                        "block_hash": event[1],
                        "cid": event[2],
                        "work_score": event[3],
                        "capacity": event[4],
                        "timestamp": event[5],
                        "signature": event[6],
                        "created_at": event[7],
                        "ipfs_url": f"https://ipfs.io/ipfs/{event[2]}",
                        "gateway_url": f"https://gateway.coinjecture.com/ipfs/{event[2]}"
                    })
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "wallet_address": address,
                        "total_ipfs_records": len(ipfs_data),
                        "ipfs_data": ipfs_data
                    },
                    "meta": {
                        "limit": limit,
                        "offset": offset,
                        "has_more": len(ipfs_data) == limit
                    }
                })
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/ipfs/stats/<address>', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_user_ipfs_stats(address: str):
            """Get IPFS statistics for a wallet."""
            try:
                import sqlite3
                db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_cids,
                        SUM(work_score) as total_work,
                        AVG(work_score) as avg_work,
                        MIN(ts) as first_mining,
                        MAX(ts) as last_mining,
                        COUNT(DISTINCT capacity) as device_types
                    FROM block_events
                    WHERE miner_address = ?
                ''', (address,))
                
                stats = cursor.fetchone()
                conn.close()
                
                if not stats or stats[0] == 0:
                    return jsonify({
                        "status": "success",
                        "data": {
                            "wallet_address": address,
                            "total_ipfs_records": 0,
                            "total_computational_work": 0,
                            "average_work_score": 0,
                            "first_mining_date": None,
                            "last_mining_date": None,
                            "device_types_used": 0,
                            "data_produced": "0 MB"
                        }
                    })
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "wallet_address": address,
                        "total_ipfs_records": stats[0],
                        "total_computational_work": round(stats[1], 2),
                        "average_work_score": round(stats[2], 2),
                        "first_mining_date": stats[3],
                        "last_mining_date": stats[4],
                        "device_types_used": stats[5],
                        "data_produced": f"{stats[0] * 0.5:.1f} MB"  # Estimate
                    }
                })
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/ipfs/download/<address>', methods=['GET'])
        @self.limiter.limit("10 per minute")
        def download_user_ipfs_data(address: str):
            """Download all IPFS data for a wallet as JSON/CSV."""
            try:
                format_type = request.args.get('format', 'json')  # 'json' or 'csv'
                
                # Get all user's IPFS data
                import sqlite3
                db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        block_index,
                        block_hash,
                        cid,
                        work_score,
                        capacity,
                        ts,
                        sig,
                        created_at
                    FROM block_events
                    WHERE miner_address = ?
                    ORDER BY block_index DESC
                ''', (address,))
                
                events = cursor.fetchall()
                conn.close()
                
                # Format data
                ipfs_data = []
                for event in events:
                    ipfs_data.append({
                        "block_index": event[0],
                        "block_hash": event[1],
                        "cid": event[2],
                        "work_score": event[3],
                        "capacity": event[4],
                        "timestamp": event[5],
                        "signature": event[6],
                        "created_at": event[7],
                        "ipfs_url": f"https://ipfs.io/ipfs/{event[2]}",
                        "gateway_url": f"https://gateway.coinjecture.com/ipfs/{event[2]}"
                    })
                
                if format_type == 'csv':
                    # Generate CSV
                    import csv
                    import io
                    
                    output = io.StringIO()
                    writer = csv.writer(output)
                    
                    # Write header
                    writer.writerow(['Block Index', 'Block Hash', 'CID', 'Work Score', 'Capacity', 
                                   'Timestamp', 'Signature', 'Created At', 'IPFS URL', 'Gateway URL'])
                    
                    # Write data
                    for record in ipfs_data:
                        writer.writerow([
                            record['block_index'],
                            record['block_hash'],
                            record['cid'],
                            record['work_score'],
                            record['capacity'],
                            record['timestamp'],
                            record['signature'],
                            record['created_at'],
                            record['ipfs_url'],
                            record['gateway_url']
                        ])
                    
                    csv_data = output.getvalue()
                    output.close()
                    
                    return Response(csv_data, mimetype='text/csv',
                                   headers={'Content-Disposition': f'attachment; filename={address}_ipfs_data.csv'})
                else:
                    # Generate JSON
                    import json
                    json_data = json.dumps({
                        "wallet_address": address,
                        "export_timestamp": int(time.time()),
                        "total_records": len(ipfs_data),
                        "ipfs_data": ipfs_data
                    }, indent=2)
                    
                    return Response(json_data, mimetype='application/json',
                                   headers={'Content-Disposition': f'attachment; filename={address}_ipfs_data.json'})
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Internal server error",
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
    
    def _format_age(self, seconds):
        """Format age in seconds to human readable format."""
        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds/60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds/3600)}h ago"
        else:
            return f"{int(seconds/86400)}d ago"
    
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
    
    def _verify_wallet_signature(self, message: str, signature: str, public_key: str) -> bool:
        """Verify wallet signature for authentication."""
        try:
            # For demo wallets, accept demo signatures
            if signature.startswith('demo_signature_') or public_key == 'demo-public-key':
                return True
            
            # For Ed25519 wallets, verify the signature
            from cryptography.hazmat.primitives.asymmetric import ed25519
            from cryptography.exceptions import InvalidSignature
            
            public_key_bytes = bytes.fromhex(public_key)
            signature_bytes = bytes.fromhex(signature)
            message_bytes = message.encode('utf-8')
            
            public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key_obj.verify(signature_bytes, message_bytes)
            return True
            
        except (InvalidSignature, ValueError, Exception):
            return False
    
    def _ensure_wallet_registered(self, wallet_address: str, public_key: str):
        """Ensure wallet is registered in the wallet_registry table."""
        try:
            import sqlite3
            db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            current_time = int(time.time())
            
            # Check if wallet already exists
            cursor.execute('SELECT wallet_address FROM wallet_registry WHERE wallet_address = ?', (wallet_address,))
            existing = cursor.fetchone()
            
            if not existing:
                # Insert new wallet
                cursor.execute('''
                    INSERT INTO wallet_registry 
                    (wallet_address, public_key, mnemonic_hash, first_seen_timestamp, 
                     last_active_timestamp, created_from_device, wallet_metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (wallet_address, public_key, None, current_time, 
                      current_time, 'mining', '{"auto_registered": true, "first_mining": ' + str(current_time) + '}'))
                
                conn.commit()
                print(f"✅ Auto-registered wallet: {wallet_address}")
            else:
                # Update last active timestamp
                cursor.execute('''
                    UPDATE wallet_registry 
                    SET last_active_timestamp = ?
                    WHERE wallet_address = ?
                ''', (current_time, wallet_address))
                conn.commit()
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️  Failed to auto-register wallet {wallet_address}: {e}")


if __name__ == "__main__":
    # Create and run API server
    api = FaucetAPI()
    api.run(debug=True)
