
# Updated CID Generation for COINjecture Backend
# This should replace the existing CID generation code

import base58
import hashlib
from typing import Dict, Any

def generate_block_cid(block_data: Dict[Any, Any]) -> str:
    """
    Generate a proper base58btc CID for a block
    """
    try:
        # Create a deterministic string from block data
        block_string = f"{block_data['index']}_{block_data['block_hash']}_{block_data['timestamp']}"
        
        # Create SHA-256 hash
        hash_bytes = hashlib.sha256(block_string.encode('utf-8')).digest()
        
        # Create CIDv0 format (multihash with SHA-256)
        # CIDv0 format: 0x12 (SHA-256) + 0x20 (32 bytes) + hash
        cid_bytes = b'\x12\x20' + hash_bytes
        
        # Encode using base58btc (excludes 0, O, I, l)
        cid = base58.b58encode(cid_bytes, alphabet=base58.BITCOIN_ALPHABET).decode('utf-8')
        
        return cid
    except Exception as e:
        print(f"Error generating CID: {e}")
        return None

def validate_cid_format(cid: str) -> bool:
    """
    Validate that CID uses proper base58btc encoding
    """
    if not cid or len(cid) != 46:
        return False
    
    # Check for base58btc characters (excludes 0, O, I, l)
    import re
    base58btc_pattern = r'^[1-9A-HJ-NP-Za-km-z]+$'
    return bool(re.match(base58btc_pattern, cid))

# Example usage:
# block_data = {
#     'index': 11473,
#     'block_hash': 'ea67892b21f971d636625994774a7a56262a955b0df0bdecca69e0af4fd2a0a7',
#     'timestamp': 1761442499.7123244
# }
# cid = generate_block_cid(block_data)
# print(f"Generated CID: {cid}")
# print(f"Valid format: {validate_cid_format(cid)}")
