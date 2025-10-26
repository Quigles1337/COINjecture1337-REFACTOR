#!/usr/bin/env python3
"""
Continuous CID Migration Service
Automatically converts new blocks from regular base58 to base58btc format
Runs continuously to handle blocks as they arrive from external miners
"""

import sqlite3
import base58
import json
import time
import logging
from typing import Dict, Any, Optional, Tuple
import os
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/coinjecture/logs/continuous_cid_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('continuous_cid_migration')

class ContinuousCIDMigrator:
    def __init__(self, db_path: str, check_interval: int = 30):
        self.db_path = db_path
        self.check_interval = check_interval
        self.running = True
        self.last_processed_height = -1
        self.converted_count = 0
        self.already_correct_count = 0
        self.conversion_error_count = 0
        
        # Create regular base58 alphabet (includes 0, O, I, l)
        self.regular_alphabet = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz0OIl'
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def convert_regular_base58_to_base58btc(self, cid: str) -> Optional[str]:
        """Convert regular base58 CID to base58btc CID"""
        try:
            if not cid or len(cid) != 46:
                return None
            
            # Decode using regular base58 alphabet (includes 0, O, I, l)
            raw_bytes = base58.b58decode(cid, alphabet=self.regular_alphabet)
            
            # Re-encode using base58btc (which excludes 0, O, I, l)
            base58btc_cid = base58.b58encode(raw_bytes, alphabet=base58.BITCOIN_ALPHABET).decode('utf-8')
            
            return base58btc_cid
        except Exception as e:
            logger.error(f"Error converting CID {cid}: {e}")
            return None
    
    def has_invalid_characters(self, cid: str) -> bool:
        """Check if CID has characters that are invalid in base58btc"""
        if not cid or len(cid) != 46:
            return False
        
        invalid_chars = ['0', 'O', 'I', 'l']
        return any(char in cid for char in invalid_chars)

    def process_block_json(self, block_data: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """Recursively process JSON data to find and convert CIDs."""
        updated = False
        
        if isinstance(block_data, dict):
            if 'cid' in block_data and isinstance(block_data['cid'], str):
                current_cid = block_data['cid']
                if self.has_invalid_characters(current_cid):
                    new_cid = self.convert_regular_base58_to_base58btc(current_cid)
                    if new_cid and new_cid != current_cid:
                        block_data['cid'] = new_cid
                        updated = True
                        self.converted_count += 1
                        logger.info(f"  - Converted CID: {current_cid} -> {new_cid}")
                    else:
                        self.conversion_error_count += 1
                        logger.error(f"  - Failed to convert CID: {current_cid}")
                else:
                    self.already_correct_count += 1
            
            for key, value in block_data.items():
                if isinstance(value, (dict, list)):
                    sub_data, sub_updated = self.process_block_json(value)
                    if sub_updated:
                        block_data[key] = sub_data
                        updated = True
        elif isinstance(block_data, list):
            for i, item in enumerate(block_data):
                if isinstance(item, (dict, list)):
                    sub_data, sub_updated = self.process_block_json(item)
                    if sub_updated:
                        block_data[i] = sub_data
                        updated = True
        return block_data, updated

    def get_latest_height(self) -> int:
        """Get the latest block height from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT MAX(height) FROM blocks')
            result = cursor.fetchone()
            conn.close()
            return result[0] if result[0] is not None else -1
        except Exception as e:
            logger.error(f"Error getting latest height: {e}")
            return -1

    def process_new_blocks(self):
        """Process new blocks that arrived since last check"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get blocks newer than last processed height
            cursor.execute(
                'SELECT height, block_bytes FROM blocks WHERE height > ? ORDER BY height ASC',
                (self.last_processed_height,)
            )
            blocks = cursor.fetchall()
            
            if not blocks:
                conn.close()
                return
            
            logger.info(f"Processing {len(blocks)} new blocks (heights {blocks[0][0]} to {blocks[-1][0]})")
            
            for height, block_bytes_data in blocks:
                try:
                    # Handle both string and bytes data
                    if isinstance(block_bytes_data, bytes):
                        block_json_str = block_bytes_data.decode('utf-8')
                    else:
                        block_json_str = block_bytes_data

                    block_data = json.loads(block_json_str)
                    
                    processed_block_data, updated = self.process_block_json(block_data)
                    
                    if updated:
                        updated_block_bytes = json.dumps(processed_block_data).encode('utf-8')
                        cursor.execute(
                            "UPDATE blocks SET block_bytes = ? WHERE height = ?",
                            (updated_block_bytes, height)
                        )
                        logger.info(f"✅ Block {height}: CIDs converted")
                    else:
                        logger.debug(f"ℹ️ Block {height}: CID already correct")

                    self.last_processed_height = height
                    
                except json.JSONDecodeError:
                    self.conversion_error_count += 1
                    logger.error(f"❌ Error decoding JSON for block at height {height}")
                except Exception as e:
                    self.conversion_error_count += 1
                    logger.error(f"❌ Unexpected error processing block {height}: {e}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"📊 Processed {len(blocks)} blocks - Converted: {self.converted_count}, Already correct: {self.already_correct_count}, Errors: {self.conversion_error_count}")
            
        except Exception as e:
            logger.error(f"Database error: {e}")

    def run(self):
        """Main continuous migration loop"""
        logger.info("🚀 Starting Continuous CID Migration Service")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Check interval: {self.check_interval} seconds")
        
        # Initialize last processed height
        self.last_processed_height = self.get_latest_height()
        logger.info(f"Starting from block height: {self.last_processed_height}")
        
        while self.running:
            try:
                current_height = self.get_latest_height()
                
                if current_height > self.last_processed_height:
                    logger.info(f"New blocks detected: {current_height - self.last_processed_height} blocks")
                    self.process_new_blocks()
                else:
                    logger.debug("No new blocks to process")
                
                # Wait for next check
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(self.check_interval)
        
        logger.info("🛑 Continuous CID Migration Service stopped")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 continuous_cid_migration.py <database_path> [check_interval_seconds]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    # Ensure log directory exists
    os.makedirs('/opt/coinjecture/logs', exist_ok=True)
    
    migrator = ContinuousCIDMigrator(db_path, check_interval)
    migrator.run()
