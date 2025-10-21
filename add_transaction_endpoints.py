#!/usr/bin/env python3
"""
Add missing transaction endpoints to faucet_server.py
"""

import os
import sys

def add_transaction_endpoints():
    """Add transaction endpoints to faucet_server.py"""
    
    faucet_server_path = "src/api/faucet_server.py"
    
    if not os.path.exists(faucet_server_path):
        print(f"❌ File not found: {faucet_server_path}")
        return False
    
    # Read the current file
    with open(faucet_server_path, 'r') as f:
        content = f.read()
    
    # Check if transaction endpoints already exist
    if "/v1/transaction/send" in content:
        print("✅ Transaction endpoints already exist")
        return True
    
    # Find the position to insert (before error handlers)
    insert_position = content.find("@self.app.errorhandler(404)")
    
    if insert_position == -1:
        print("❌ Could not find insertion point")
        return False
    
    # Transaction endpoints to add
    transaction_endpoints = '''
        # TRANSACTION ENDPOINTS
        @self.app.route('/v1/transaction/send', methods=['POST'])
        @self.limiter.limit("10 per minute")
        def send_transaction():
            """Submit transaction to pool."""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        "status": "error",
                        "error": "No transaction data provided"
                    }), 400
                
                from tokenomics.blockchain_state import BlockchainState, Transaction
                import json
                
                # Load blockchain state
                blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
                if os.path.exists(blockchain_state_path):
                    with open(blockchain_state_path, 'r') as f:
                        state_data = json.load(f)
                        state = BlockchainState()
                        # Initialize state from file data
                        state.balances = state_data.get('balances', {})
                        state.pending_transactions = [Transaction.from_dict(tx) for tx in state_data.get('pending_transactions', [])]
                        state.transaction_history = {addr: [Transaction.from_dict(tx) for tx in txs] for addr, txs in state_data.get('transaction_history', {}).items()}
                else:
                    state = BlockchainState()
                
                # Create transaction
                transaction = Transaction(
                    sender=data['sender'],
                    recipient=data['recipient'],
                    amount=float(data['amount']),
                    timestamp=data.get('timestamp', time.time())
                )
                
                # Add to pending transactions
                if state.add_transaction(transaction):
                    # Save updated state
                    state_data = {
                        'balances': state.balances,
                        'pending_transactions': [tx.to_dict() for tx in state.pending_transactions],
                        'transaction_history': {addr: [tx.to_dict() for tx in txs] for addr, txs in state.transaction_history.items()}
                    }
                    with open(blockchain_state_path, 'w') as f:
                        json.dump(state_data, f, indent=2)
                    
                    return jsonify({
                        "status": "success",
                        "transaction": transaction.to_dict()
                    }), 200
                else:
                    return jsonify({
                        "status": "error",
                        "error": "Transaction validation failed"
                    }), 400
                    
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Failed to process transaction",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/transaction/pending', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_pending_transactions():
            """Get pending transactions."""
            try:
                limit = int(request.args.get('limit', 100))
                
                blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
                if os.path.exists(blockchain_state_path):
                    with open(blockchain_state_path, 'r') as f:
                        state_data = json.load(f)
                        pending = [Transaction.from_dict(tx) for tx in state_data.get('pending_transactions', [])]
                        pending = pending[:limit]
                    return jsonify({
                        "status": "success",
                        "transactions": [tx.to_dict() for tx in pending],
                        "count": len(pending)
                    }), 200
                else:
                    return jsonify({
                        "status": "success",
                        "transactions": [],
                        "count": 0
                    }), 200
                    
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Failed to get pending transactions",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/transaction/<tx_id>', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_transaction(tx_id: str):
            """Get transaction by ID."""
            try:
                blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
                if os.path.exists(blockchain_state_path):
                    with open(blockchain_state_path, 'r') as f:
                        state_data = json.load(f)
                        # Search in pending transactions
                        for tx_data in state_data.get('pending_transactions', []):
                            if tx_data.get('transaction_id') == tx_id:
                                return jsonify({
                                    "status": "success",
                                    "transaction": tx_data
                                }), 200
                        # Search in transaction history
                        for addr, txs in state_data.get('transaction_history', {}).items():
                            for tx_data in txs:
                                if tx_data.get('transaction_id') == tx_id:
                                    return jsonify({
                                        "status": "success",
                                        "transaction": tx_data
                                    }), 200
                
                return jsonify({
                    "status": "error",
                    "error": "Transaction not found"
                }), 404
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Failed to get transaction",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/wallet/<address>/transactions', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_wallet_transactions(address: str):
            """Get wallet transaction history."""
            try:
                limit = int(request.args.get('limit', 50))
                
                blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
                if os.path.exists(blockchain_state_path):
                    with open(blockchain_state_path, 'r') as f:
                        state_data = json.load(f)
                        transactions = state_data.get('transaction_history', {}).get(address, [])
                        transactions = transactions[:limit]
                    return jsonify({
                        "status": "success",
                        "transactions": transactions,
                        "count": len(transactions)
                    }), 200
                else:
                    return jsonify({
                        "status": "success",
                        "transactions": [],
                        "count": 0
                    }), 200
                    
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Failed to get wallet transactions",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/wallet/<address>/balance', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_wallet_balance(address: str):
            """Get wallet balance."""
            try:
                blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
                if os.path.exists(blockchain_state_path):
                    with open(blockchain_state_path, 'r') as f:
                        state_data = json.load(f)
                        balance = state_data.get('balances', {}).get(address, 0.0)
                    return jsonify({
                        "status": "success",
                        "balance": balance,
                        "address": address
                    }), 200
                else:
                    return jsonify({
                        "status": "success",
                        "balance": 0.0,
                        "address": address
                    }), 200
                    
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Failed to get wallet balance",
                    "message": str(e)
                }), 500
'''
    
    # Insert the transaction endpoints
    new_content = content[:insert_position] + transaction_endpoints + content[insert_position:]
    
    # Write the updated file
    with open(faucet_server_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Transaction endpoints added to faucet_server.py")
    return True

if __name__ == "__main__":
    success = add_transaction_endpoints()
    sys.exit(0 if success else 1)
