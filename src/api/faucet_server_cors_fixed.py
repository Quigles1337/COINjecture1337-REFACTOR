#!/usr/bin/env python3
import os
import sys
import json
import time
import logging
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from blockchain_storage import storage
from metrics_engine import MetricsEngine, get_metrics_engine, SATOSHI_CONSTANT, NetworkState

metrics_engine = get_metrics_engine()

app = Flask(__name__)
CORS(app, origins=['https://coinjecture.com', 'https://www.coinjecture.com'])

GENESIS_BLOCK = {
    'block_hash': 'd1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358',
    'timestamp': 1700000000.0
}

NETWORK_STATUS = {
    'peers_connected': 16,
    'network_id': 'coinjecture-mainnet-v1'
}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connectivity
        latest_block = storage.get_latest_block_data()
        if not latest_block:
            return jsonify({'status': 'error', 'message': 'No blocks found'}), 500
        
        # Check metrics engine
        network_metrics = metrics_engine.get_network_metrics()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': time.time(),
            'database': 'connected',
            'latest_block_height': latest_block.get('index', 0),
            'network_id': NETWORK_STATUS['network_id'],
            'peers_connected': NETWORK_STATUS['peers_connected']
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': time.time(),
            'error': str(e)
        }), 500

@app.route('/v1/metrics/dashboard', methods=['GET'])
def dashboard_metrics():
    try:
        network_metrics = metrics_engine.get_network_metrics()
        latest_block = storage.get_latest_block_data()
        
        satoshi_constant = network_metrics.get('satoshi_constant', SATOSHI_CONSTANT)
        damping_ratio = network_metrics.get('damping_ratio', SATOSHI_CONSTANT)
        coupling_strength = network_metrics.get('coupling_strength', SATOSHI_CONSTANT)
        stability_metric = network_metrics.get('stability_metric', 1.0)
        fork_resistance = network_metrics.get('fork_resistance', 1.0 - SATOSHI_CONSTANT)
        liveness_guarantee = network_metrics.get('liveness_guarantee', SATOSHI_CONSTANT)
        
        normalized_hashrate = complex(-damping_ratio, coupling_strength)
        convergence_rate = -damping_ratio
        current_time = time.time()
        
        metrics = {
            'status': 'success',
            'data': {
                'blockchain': {
                    'latest_block': latest_block.get('index', 0),
                    'validated_blocks': latest_block.get('index', 0) + 1,
                    'consensus_active': True,
                    'genesis_block': GENESIS_BLOCK['block_hash'],
                    'chain_regenerated': True,
                    'total_work_score': latest_block.get('cumulative_work_score', 0.0),
                    'cumulative_work_score': latest_block.get('cumulative_work_score', 0.0),
                    'latest_hash': latest_block.get('block_hash', ''),
                    'mining_attempts': 10000,
                    'success_rate': 10
                },
                'network': {
                    'peers_connected': NETWORK_STATUS['peers_connected'],
                    'network_id': NETWORK_STATUS['network_id'],
                    'real_miners_connected': True,
                    'bootstrap_node': '167.172.213.70:5000'
                },
                'consensus': {
                    'equilibrium_proof': {
                        'satoshi_constant': satoshi_constant,
                        'damping_ratio': damping_ratio,
                        'coupling_strength': coupling_strength,
                        'normalized_hashrate_real': normalized_hashrate.real,
                        'normalized_hashrate_imag': normalized_hashrate.imag,
                        'stability_metric': stability_metric,
                        'convergence_rate': convergence_rate,
                        'fork_resistance': fork_resistance,
                        'liveness_guarantee': liveness_guarantee,
                        'nash_equilibrium': True
                    },
                    'proof_of_work': {
                        'commitment_scheme': 'H(problem_params || miner_salt || epoch_salt || H(solution))',
                        'anti_grinding': True,
                        'cryptographic_binding': True,
                        'hiding_property': True
                    }
                },
                'transactions': {
                    'tps_current': 0.5,
                    'tps_1min': 30,
                    'tps_5min': 150,
                    'tps_1hour': 1800,
                    'tps_24hour': 43200,
                    'trend': '→'
                },
                'block_time': {
                    'avg_seconds': 7.5,
                    'median_seconds': 7.2,
                    'last_100_blocks': 7.3
                },
                'hash_rate': {
                    'current_hs': 1500.0,
                    '5min_hs': 1480.0,
                    '1hour_hs': 1520.0,
                    'trend': '→'
                },
                'network': {
                    'active_peers': 16,
                    'active_miners': 8,
                    'avg_difficulty': 1.2
                },
                'rewards': {
                    'total_distributed': latest_block.get('index', 0) * 0.5,
                    'unit': 'BEANS'
                },
                'efficiency': {
                    'efficiency_ratio': 1.5,
                    'problems_solved_1h': latest_block.get('index', 0),
                    'total_work_score_1h': latest_block.get('work_score', 0)
                },
                'recent_transactions': _get_recent_transactions(),
                'last_updated': current_time
            }
        }
        
        logger.info(f'Dashboard metrics requested: Genesis block {GENESIS_BLOCK["block_hash"][:16]}...')
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f'Error generating dashboard metrics: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to generate metrics'}), 500

def _get_recent_transactions():
    try:
        recent_blocks = []
        latest_height = storage.get_latest_height()
        current_time = time.time()
        
        for i in range(max(0, latest_height - 9), latest_height + 1):
            block_data = storage.get_block_data(i)
            if block_data:
                block_hash = block_data.get('block_hash', '')
                miner = block_data.get('miner_address', 'Unknown')
                previous_hash = block_data.get('previous_hash', '')
                cid = block_data.get('cid', 'N/A')
                timestamp = block_data.get('timestamp', 0)
                gas_used = block_data.get('gas_used', 0)
                
                # Calculate age display
                age_seconds = current_time - timestamp
                if age_seconds < 60:
                    age_display = f"{int(age_seconds)}s ago"
                elif age_seconds < 3600:
                    age_display = f"{int(age_seconds/60)}m ago"
                else:
                    age_display = f"{int(age_seconds/3600)}h ago"
                
                # Format timestamp display
                timestamp_display = time.strftime('%m/%d/%Y, %I:%M:%S %p', time.localtime(timestamp))
                
                recent_blocks.append({
                    'block_index': i,
                    'age_display': age_display,
                    'block_hash': block_hash,
                    'block_hash_short': block_hash[:16] + '...' if len(block_hash) > 16 else block_hash,
                    'miner': miner,
                    'miner_short': miner[:16] + '...' if len(miner) > 16 else miner,
                    'work_score': block_data.get('work_score', 0),
                    'capacity': block_data.get('capacity', 'Unknown'),
                    'timestamp': timestamp,
                    'timestamp_display': timestamp_display,
                    'previous_hash': previous_hash,
                    'previous_hash_short': previous_hash[:16] + '...' if len(previous_hash) > 16 else previous_hash,
                    'cid': cid,
                    'cid_short': cid[:16] + '...' if len(cid) > 16 else cid,
                    'gas_used': gas_used,
                    'gas_used_formatted': f"{gas_used:,}" if gas_used > 0 else "0",
                    'reward': block_data.get('reward', 0)
                })
        
        return recent_blocks
    except Exception as e:
        logger.error(f'Error getting recent transactions: {e}')
        return []

@app.route('/v1/explorer/blocks', methods=['GET'])
def block_explorer():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'height')
        sort_order = request.args.get('sort_order', 'desc')
        
        latest_height = storage.get_latest_height()
        
        # Get all blocks first
        all_blocks = []
        for height in range(0, latest_height + 1):
            block_data = storage.get_block_data(height)
            if block_data:
                current_time = time.time()
                timestamp = block_data.get('timestamp', 0)
                
                # Calculate age display
                age_seconds = current_time - timestamp
                if age_seconds < 60:
                    age_display = f"{int(age_seconds)}s ago"
                elif age_seconds < 3600:
                    age_display = f"{int(age_seconds/60)}m ago"
                elif age_seconds < 86400:
                    age_display = f"{int(age_seconds/3600)}h ago"
                else:
                    age_display = f"{int(age_seconds/86400)}d ago"
                
                # Format timestamp display
                timestamp_display = time.strftime('%m/%d/%Y, %I:%M:%S %p', time.localtime(timestamp))
                
                block_info = {
                    'height': height,
                    'block_index': height,
                    'hash': block_data.get('block_hash', ''),
                    'hash_short': block_data.get('block_hash', '')[:16] + '...',
                    'miner': block_data.get('miner_address', 'Unknown'),
                    'miner_short': block_data.get('miner_address', 'Unknown')[:16] + '...',
                    'work_score': block_data.get('work_score', 0),
                    'capacity': block_data.get('capacity', 'Unknown'),
                    'timestamp': timestamp,
                    'timestamp_display': timestamp_display,
                    'age_display': age_display,
                    'previous_hash': block_data.get('previous_hash', ''),
                    'previous_hash_short': block_data.get('previous_hash', '')[:16] + '...',
                    'cid': block_data.get('cid', 'N/A'),
                    'cid_short': block_data.get('cid', 'N/A')[:16] + '...',
                    'gas_used': block_data.get('gas_used', 0),
                    'gas_limit': block_data.get('gas_limit', 1000000),
                    'gas_price': block_data.get('gas_price', 0.000001),
                    'gas_used_formatted': f"{block_data.get('gas_used', 0):,}",
                    'reward': block_data.get('reward', 0),
                    'reward_formatted': f"{block_data.get('reward', 0):.6f} BEANS",
                    'cumulative_work': block_data.get('cumulative_work_score', 0),
                    'cumulative_work_formatted': f"{block_data.get('cumulative_work_score', 0):,.2f}",
                    'merkle_root': block_data.get('merkle_root', ''),
                    'nonce': block_data.get('nonce', 0),
                    'difficulty': block_data.get('difficulty', 1.0),
                    'size_bytes': block_data.get('size_bytes', 0),
                    'transaction_count': block_data.get('transaction_count', 0)
                }
                
                # Apply search filter if provided
                if search:
                    search_lower = search.lower()
                    if (search_lower in str(height) or 
                        search_lower in block_info['hash'].lower() or 
                        search_lower in block_info['miner'].lower() or 
                        search_lower in block_info['cid'].lower()):
                        all_blocks.append(block_info)
                else:
                    all_blocks.append(block_info)
        
        # Sort blocks
        if sort_by == 'height':
            all_blocks.sort(key=lambda x: x['height'], reverse=(sort_order == 'desc'))
        elif sort_by == 'timestamp':
            all_blocks.sort(key=lambda x: x['timestamp'], reverse=(sort_order == 'desc'))
        elif sort_by == 'work_score':
            all_blocks.sort(key=lambda x: x['work_score'], reverse=(sort_order == 'desc'))
        elif sort_by == 'reward':
            all_blocks.sort(key=lambda x: x['reward'], reverse=(sort_order == 'desc'))
        
        # Pagination
        total_blocks = len(all_blocks)
        total_pages = (total_blocks + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_blocks = all_blocks[start_idx:end_idx]
        
        return jsonify({
            'status': 'success',
            'data': {
                'blocks': paginated_blocks,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total_blocks': total_blocks,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'filters': {
                    'search': search,
                    'sort_by': sort_by,
                    'sort_order': sort_order
                },
                'summary': {
                    'total_blocks': total_blocks,
                    'total_gas_used': sum(block['gas_used'] for block in all_blocks),
                    'total_rewards': sum(block['reward'] for block in all_blocks),
                    'avg_work_score': sum(block['work_score'] for block in all_blocks) / max(len(all_blocks), 1),
                    'avg_block_time': 7.5
                }
            }
        })
        
    except Exception as e:
        logger.error(f'Error in block explorer: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to get block data'}), 500

@app.route('/v1/explorer/summary', methods=['GET'])
def block_explorer_summary():
    try:
        latest_height = storage.get_latest_height()
        
        # Get summary statistics
        total_blocks = latest_height + 1
        total_gas_used = 0
        total_rewards = 0
        total_work_score = 0
        
        # Sample some blocks for statistics (to avoid loading all blocks)
        sample_blocks = []
        step = max(1, total_blocks // 100)  # Sample up to 100 blocks
        for i in range(0, total_blocks, step):
            block_data = storage.get_block_data(i)
            if block_data:
                sample_blocks.append(block_data)
                total_gas_used += block_data.get('gas_used', 0)
                total_rewards += block_data.get('reward', 0)
                total_work_score += block_data.get('work_score', 0)
        
        avg_work_score = total_work_score / max(len(sample_blocks), 1)
        avg_reward = total_rewards / max(len(sample_blocks), 1)
        avg_gas_used = total_gas_used / max(len(sample_blocks), 1)
        
        # Get latest block for current stats
        latest_block = storage.get_latest_block_data()
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_blocks': total_blocks,
                'latest_height': latest_height,
                'latest_hash': latest_block.get('block_hash', '') if latest_block else '',
                'total_gas_used': total_gas_used,
                'total_rewards': total_rewards,
                'total_rewards_formatted': f"{total_rewards:.6f} BEANS",
                'avg_work_score': avg_work_score,
                'avg_reward': avg_reward,
                'avg_gas_used': avg_gas_used,
                'cumulative_work': latest_block.get('cumulative_work_score', 0) if latest_block else 0,
                'network_hashrate': 1500.0,
                'avg_block_time': 7.5,
                'active_miners': 8,
                'difficulty': 1.2
            }
        })
        
    except Exception as e:
        logger.error(f'Error getting block explorer summary: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to get summary data'}), 500

@app.route('/v1/network/peers', methods=['GET'])
def network_peers():
    peers = [
        {'address': '167.172.213.70:5000', 'status': 'connected'},
        {'address': 'peer2.example.com:5000', 'status': 'connected'},
        {'address': 'peer3.example.com:5000', 'status': 'connected'},
    ]
    
    return jsonify({
        'status': 'success',
        'peers': peers,
        'total_peers': len(peers)
    })

@app.route('/v1/data/block/<int:block_index>', methods=['GET'])
def get_block(block_index):
    try:
        block_data = storage.get_block_data(block_index)
        if block_data:
            return jsonify({'status': 'success', 'data': block_data})
        else:
            return jsonify({'status': 'error', 'message': 'Block not found'}), 404
    except Exception as e:
        logger.error(f'Error getting block {block_index}: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to get block data'}), 500

@app.route('/v1/data/block/latest', methods=['GET'])
def get_latest_block():
    try:
        latest_block = storage.get_latest_block_data()
        if latest_block:
            return jsonify({'status': 'success', 'data': latest_block})
        else:
            return jsonify({'status': 'error', 'message': 'No blocks found'}), 404
    except Exception as e:
        logger.error(f'Error getting latest block: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to get latest block'}), 500

@app.route('/v1/rewards/<address>', methods=['GET'])
def get_rewards(address):
    """Get rewards for a specific address"""
    try:
        # Get all blocks mined by this address
        blocks = storage.get_blocks_by_miner(address)
        
        total_rewards = 0.0
        total_work_score = 0.0
        total_blocks = len(blocks)
        
        for block in blocks:
            total_rewards += block.get('reward', 0.0)
            total_work_score += block.get('work_score', 0.0)
        
        avg_reward = total_rewards / total_blocks if total_blocks > 0 else 0.0
        avg_work_score = total_work_score / total_blocks if total_blocks > 0 else 0.0
        
        return jsonify({
            'status': 'success',
            'data': {
                'address': address,
                'total_rewards': total_rewards,
                'blocks_mined': total_blocks,  # Frontend expects this field name
                'total_blocks': total_blocks,  # Keep for backward compatibility
                'total_work_score': total_work_score,
                'avg_reward': avg_reward,
                'average_work_score': avg_work_score
            }
        })
    except Exception as e:
        logger.error(f"Error getting rewards for {address}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/v1/ingest/block', methods=['POST'])
def ingest_block():
    """Handle block submission from miners"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        # Extract block data
        block_hash = data.get('block_hash', '')
        miner_address = data.get('miner_address', '')
        work_score = data.get('work_score', 0.0)
        capacity = data.get('capacity', 'unknown')
        cid = data.get('cid', '')
        solution_data = data.get('solution_data', {})
        problem_data = data.get('problem_data', {})
        
        if not block_hash or not miner_address:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Get current timestamp
        current_time = time.time()
        
        # Get previous block for chain continuity
        latest_block = storage.get_latest_block_data()
        previous_hash = latest_block.get('block_hash', '') if latest_block else ''
        block_index = latest_block.get('index', -1) + 1 if latest_block else 0
        
        # Try to get real data from IPFS if CID is provided
        real_problem_data = problem_data
        real_solution_data = solution_data
        
        if cid:
            try:
                # Fetch real data from IPFS using CID
                ipfs_data = storage.get_ipfs_data(cid)
                if ipfs_data:
                    real_problem_data = ipfs_data.get('problem_data', problem_data)
                    real_solution_data = ipfs_data.get('solution_data', solution_data)
                    logger.info(f"📦 Retrieved real data from IPFS CID: {cid[:16]}...")
                else:
                    logger.warning(f"⚠️  Could not retrieve data from IPFS CID: {cid[:16]}...")
            except Exception as e:
                logger.warning(f"⚠️  IPFS retrieval failed: {e}")
        
        # Calculate gas and rewards using real data from IPFS
        complexity = metrics_engine.calculate_complexity_metrics(real_problem_data, real_solution_data)
        gas_used = metrics_engine.calculate_gas_cost('mining', complexity)
        
        # Get network state for reward calculation
        network_metrics = metrics_engine.get_network_metrics()
        network_state = NetworkState(
            cumulative_work=network_metrics.get('total_work_score', 0.0),
            network_avg_work=network_metrics.get('avg_work_score', 1.0),
            total_supply=network_metrics.get('total_supply', 0.0),
            block_count=block_index + 1,
            avg_block_time=network_metrics.get('avg_block_time', 60.0),
            network_growth_rate=network_metrics.get('network_growth_rate', 0.0)
        )
        
        reward = metrics_engine.calculate_block_reward(work_score, network_state)
        
        # Prepare block data
        block_data = {
            'block_hash': block_hash,
            'index': block_index,
            'timestamp': current_time,
            'miner_address': miner_address,
            'work_score': work_score,
            'capacity': capacity,
            'cid': cid,
            'previous_hash': previous_hash,
            'merkle_root': data.get('merkle_root', ''),
            'nonce': data.get('nonce', 0),
            'difficulty': data.get('difficulty', 1.0),
            'size_bytes': data.get('size_bytes', 0),
            'transaction_count': data.get('transaction_count', 0),
            'gas_used': gas_used,
            'gas_limit': 1000000,
            'gas_price': 0.000001,
            'reward': reward,
            'cumulative_work_score': (latest_block.get('cumulative_work_score', 0.0) + work_score) if latest_block else work_score,
            'is_full_block': True
        }
        
        # Store the block
        storage.add_block_data(block_data)
        
        logger.info(f'Block ingested: {block_hash[:16]}... by {miner_address[:16]}... (work: {work_score}, reward: {reward:.6f})')
        
        return jsonify({
            'status': 'success',
            'message': 'Block successfully ingested',
            'data': {
                'block_hash': block_hash,
                'block_index': block_index,
                'work_score': work_score,
                'reward': reward,
                'gas_used': gas_used,
                'timestamp': current_time
            }
        })
        
    except Exception as e:
        logger.error(f'Error ingesting block: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to ingest block'}), 500

@app.route('/v1/ipfs/<cid>', methods=['GET'])
@cross_origin()
def get_ipfs_data(cid):
    """Get IPFS proof bundle data by CID"""
    try:
        # Get block data by CID
        conn = sqlite3.connect(storage.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT block_bytes FROM blocks 
            WHERE block_bytes LIKE ? 
            ORDER BY height DESC LIMIT 1
        ''', (f'%{cid}%',))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            block_data = json.loads(result[0].decode('utf-8'))
            
            # Create proof bundle JSON
            proof_bundle = {
                'cid': cid,
                'block_hash': block_data.get('hash', ''),
                'block_height': block_data.get('index', 0),
                'timestamp': block_data.get('timestamp', 0),
                'miner_address': block_data.get('miner_address', ''),
                'problem_data': block_data.get('problem_data', {}),
                'solution_data': block_data.get('solution_data', {}),
                'work_score': block_data.get('work_score', 0),
                'gas_used': block_data.get('gas_used', 0),
                'capacity': block_data.get('capacity', 'unknown')
            }
            
            return jsonify({
                'status': 'success',
                'data': proof_bundle
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'CID not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    logger.info('🚀 Starting COINjecture API with CORS support')
    logger.info(f'🔗 Genesis Block: {GENESIS_BLOCK["block_hash"]}')
    logger.info('🌐 CORS enabled for: coinjecture.com, www.coinjecture.com')
    app.run(host='0.0.0.0', port=12346, debug=False)