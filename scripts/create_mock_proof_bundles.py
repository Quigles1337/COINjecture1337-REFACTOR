#!/usr/bin/env python3
"""
Create Mock Proof Bundles Script

Creates mock proof bundles for testing frontend functionality.
This generates realistic proof bundle data for existing CIDs.
"""

import sqlite3
import json
import hashlib
import base58
import os
import sys
from datetime import datetime

class MockProofBundleCreator:
    def __init__(self, db_path="/opt/coinjecture/data/blockchain.db"):
        self.db_path = db_path
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def create_mock_proof_bundle(self, block_data):
        """Create a mock proof bundle for a block"""
        try:
            # Extract block information
            block_hash = block_data.get('block_hash', '')
            index = block_data.get('index', 0)
            timestamp = block_data.get('timestamp', 0)
            work_score = block_data.get('work_score', 1.0)
            
            # Create realistic problem data
            problem_data = {
                "type": "subset_sum",
                "target": 15 + (index % 20),  # Vary target based on block index
                "numbers": [i for i in range(1, 11 + (index % 10))],  # Vary problem size
                "difficulty": 1.0 + (index % 10) * 0.1,
                "constraints": 3 + (index % 5)
            }
            
            # Create realistic solution data
            solution_data = {
                "solve_time": 0.5 + (index % 5) * 0.2,  # 0.5-1.5 seconds
                "verify_time": 0.01 + (index % 3) * 0.005,  # 0.01-0.025 seconds
                "memory_used": 1024 + (index % 10) * 256,  # 1KB-3.5KB
                "energy_used": 0.1 + (index % 5) * 0.05,  # 0.1-0.35
                "quality": 0.8 + (index % 20) * 0.01,  # 0.8-1.0
                "algorithm": "dynamic_programming"
            }
            
            # Create complexity metrics
            complexity_metrics = {
                "time_asymmetry": solution_data["solve_time"] / solution_data["verify_time"],
                "space_asymmetry": solution_data["memory_used"] / 1000,
                "problem_weight": problem_data["difficulty"],
                "size_factor": len(problem_data["numbers"]) / 10,
                "quality_score": solution_data["quality"],
                "energy_efficiency": 1.0 / solution_data["energy_used"]
            }
            
            # Create the complete proof bundle
            proof_bundle = {
                "block_hash": block_hash,
                "block_index": index,
                "timestamp": timestamp,
                "problem_data": problem_data,
                "solution_data": solution_data,
                "complexity_metrics": complexity_metrics,
                "work_score": work_score,
                "gas_used": int(1000 + complexity_metrics["time_asymmetry"] * 100),
                "gas_limit": 1000000,
                "gas_price": 0.000001,
                "reward": work_score * 0.1,
                "miner_address": f"BEANS{block_hash[:8]}",
                "created_at": datetime.now().isoformat()
            }
            
            return proof_bundle
            
        except Exception as e:
            self.log(f"⚠️  Error creating mock bundle for block {block_hash[:16]}...: {e}")
            return None
    
    def create_mock_bundles_for_database(self, limit=100):
        """Create mock proof bundles for database blocks"""
        if not os.path.exists(self.db_path):
            self.log(f"❌ Database not found: {self.db_path}")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent blocks
            cursor.execute("""
                SELECT block_hash, block_bytes 
                FROM blocks 
                ORDER BY height DESC 
                LIMIT ?
            """, (limit,))
            blocks = cursor.fetchall()
            
            if not blocks:
                self.log("❌ No blocks found in database")
                return False
            
            self.log(f"📊 Creating mock bundles for {len(blocks)} blocks")
            
            created_count = 0
            bundles_dir = "/tmp/mock_proof_bundles"
            os.makedirs(bundles_dir, exist_ok=True)
            
            for block_hash, block_bytes in blocks:
                try:
                    # Parse block data
                    block_data = json.loads(block_bytes.decode('utf-8'))
                    cid = block_data.get('cid', '')
                    
                    if not cid:
                        continue
                    
                    # Create mock proof bundle
                    proof_bundle = self.create_mock_proof_bundle(block_data)
                    if not proof_bundle:
                        continue
                    
                    # Save bundle to file
                    bundle_file = os.path.join(bundles_dir, f"{cid}.json")
                    with open(bundle_file, 'w') as f:
                        json.dump(proof_bundle, f, indent=2)
                    
                    created_count += 1
                    
                    if created_count % 20 == 0:
                        self.log(f"📈 Created {created_count} mock bundles...")
                    
                except Exception as e:
                    self.log(f"⚠️  Error processing block {block_hash[:16]}...: {e}")
                    continue
            
            conn.close()
            
            self.log(f"✅ Mock bundles created!")
            self.log(f"   📊 Total blocks: {len(blocks)}")
            self.log(f"   ✅ Created: {created_count}")
            self.log(f"   📁 Location: {bundles_dir}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Database error: {e}")
            return False

def main():
    """Main execution function"""
    print("🎭 Mock Proof Bundle Creator")
    print("=" * 40)
    
    creator = MockProofBundleCreator()
    
    # Create mock bundles
    print("\n🎭 Creating mock proof bundles...")
    success = creator.create_mock_bundles_for_database(limit=50)
    
    if success:
        print("\n✅ Mock proof bundles created successfully!")
        print("📁 Bundles saved to: /tmp/mock_proof_bundles/")
        print("🌐 You can now test frontend proof bundle downloads!")
    else:
        print("\n❌ Failed to create mock proof bundles.")
        sys.exit(1)

if __name__ == "__main__":
    main()
