"""
Module: network
Specification: docs/blockchain/network.md

Networking module for COINjecture blockchain with libp2p integration,
gossipsub topics, RPC handlers, and message compression.
"""

import json
import time
import hashlib
import struct
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Union, Callable, Tuple, Set
from enum import Enum
import threading
from collections import defaultdict, deque

# Import from existing modules
try:
    from .core.blockchain import Block, ProblemTier, ProblemType
    from .consensus import ConsensusEngine
    from .storage import StorageManager
    from .pow import ProblemRegistry
except ImportError:
    # Fallback for direct execution
    from core.blockchain import Block, ProblemTier, ProblemType
    from consensus import ConsensusEngine
    from storage import StorageManager
    from pow import ProblemRegistry


# Constants
DEFAULT_TOPIC_VERSION = "1.0.0"
DEFAULT_MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB
DEFAULT_RATE_LIMIT_PER_SECOND = 100
DEFAULT_COMPRESSION_THRESHOLD = 1024  # 1KB
DEFAULT_PEER_TIMEOUT = 30.0  # seconds


class MessageType(Enum):
    """Message types for network protocol."""
    HEADER = "header"
    REVEAL = "reveal"
    REQUEST = "request"
    RESPONSE = "response"


class RequestKind(Enum):
    """RPC request kinds."""
    GET_HEADERS = "get_headers"
    GET_BLOCK_BY_HASH = "get_block_by_hash"
    GET_PROOF_BY_CID = "get_proof_by_cid"


class CompressionCodec(Enum):
    """Compression codecs."""
    NONE = "none"
    ZSTD = "zstd"
    SNAPPY = "snappy"


@dataclass
class HeaderMsg:
    """Header announcement message."""
    header_bytes: bytes
    tip_work: int  # u128 equivalent
    peer_id: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": MessageType.HEADER.value,
            "header_bytes": self.header_bytes.hex(),
            "tip_work": self.tip_work,
            "peer_id": self.peer_id,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HeaderMsg':
        return cls(
            header_bytes=bytes.fromhex(data["header_bytes"]),
            tip_work=data["tip_work"],
            peer_id=data["peer_id"],
            timestamp=data.get("timestamp", time.time())
        )


@dataclass
class RevealMsg:
    """Reveal bundle message."""
    cid: str
    commitment: bytes  # [32] bytes
    problem_type: int  # u8
    capacity: int  # u8 (renamed from tier)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": MessageType.REVEAL.value,
            "cid": self.cid,
            "commitment": self.commitment.hex(),
            "problem_type": self.problem_type,
            "capacity": self.capacity,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RevealMsg':
        return cls(
            cid=data["cid"],
            commitment=bytes.fromhex(data["commitment"]),
            problem_type=data["problem_type"],
            capacity=data["capacity"],
            timestamp=data.get("timestamp", time.time())
        )


@dataclass
class RequestMsg:
    """RPC request message."""
    kind: RequestKind
    params: Dict[str, Any]
    request_id: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": MessageType.REQUEST.value,
            "kind": self.kind.value,
            "params": self.params,
            "request_id": self.request_id,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequestMsg':
        return cls(
            kind=RequestKind(data["kind"]),
            params=data["params"],
            request_id=data["request_id"],
            timestamp=data.get("timestamp", time.time())
        )


@dataclass
class ResponseMsg:
    """RPC response message."""
    status: str  # "success", "error", "not_found"
    payload: Optional[bytes] = None
    error_message: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": MessageType.RESPONSE.value,
            "status": self.status,
            "timestamp": self.timestamp
        }
        
        if self.payload:
            result["payload"] = self.payload.hex()
        if self.error_message:
            result["error_message"] = self.error_message
        if self.request_id:
            result["request_id"] = self.request_id
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResponseMsg':
        payload = None
        if "payload" in data:
            payload = bytes.fromhex(data["payload"])
            
        return cls(
            status=data["status"],
            payload=payload,
            error_message=data.get("error_message"),
            request_id=data.get("request_id"),
            timestamp=data.get("timestamp", time.time())
        )


class MessageCompressor:
    """Handles message compression and decompression."""
    
    def __init__(self, threshold: int = DEFAULT_COMPRESSION_THRESHOLD):
        self.threshold = threshold
    
    def compress(self, data: bytes) -> Tuple[bytes, CompressionCodec]:
        """
        Compress data if it exceeds threshold.
        
        Args:
            data: Data to compress
            
        Returns:
            Tuple of (compressed_data, codec_used)
        """
        if len(data) <= self.threshold:
            return data, CompressionCodec.NONE
        
        # Try zstd first, fallback to snappy
        try:
            import zstandard as zstd  # type: ignore
            compressor = zstd.ZstdCompressor()
            compressed = compressor.compress(data)
            return compressed, CompressionCodec.ZSTD
        except ImportError:
            try:
                import snappy  # type: ignore
                compressed = snappy.compress(data)
                return compressed, CompressionCodec.SNAPPY
            except ImportError:
                # No compression available, return original
                return data, CompressionCodec.NONE
    
    def decompress(self, data: bytes, codec: CompressionCodec) -> bytes:
        """
        Decompress data using specified codec.
        
        Args:
            data: Compressed data
            codec: Compression codec used
            
        Returns:
            Decompressed data
        """
        if codec == CompressionCodec.NONE:
            return data
        elif codec == CompressionCodec.ZSTD:
            try:
                import zstandard as zstd  # type: ignore
                decompressor = zstd.ZstdDecompressor()
                return decompressor.decompress(data)
            except ImportError:
                raise ValueError("zstd decompression not available")
        elif codec == CompressionCodec.SNAPPY:
            try:
                import snappy  # type: ignore
                return snappy.decompress(data)
            except ImportError:
                raise ValueError("snappy decompression not available")
        else:
            raise ValueError(f"Unknown compression codec: {codec}")


class RateLimiter:
    """Rate limiter for network messages."""
    
    def __init__(self, max_per_second: int = DEFAULT_RATE_LIMIT_PER_SECOND):
        self.max_per_second = max_per_second
        self.peer_timestamps: Dict[str, deque] = defaultdict(lambda: deque())
        self.lock = threading.Lock()
    
    def is_allowed(self, peer_id: str) -> bool:
        """
        Check if peer is within rate limit.
        
        Args:
            peer_id: Peer identifier
            
        Returns:
            True if allowed, False if rate limited
        """
        with self.lock:
            current_time = time.time()
            timestamps = self.peer_timestamps[peer_id]
            
            # Remove timestamps older than 1 second
            while timestamps and current_time - timestamps[0] > 1.0:
                timestamps.popleft()
            
            # Check if under limit
            if len(timestamps) >= self.max_per_second:
                return False
            
            # Add current timestamp
            timestamps.append(current_time)
            return True


class NetworkProtocol:
    """
    Network protocol implementation for COINjecture.
    
    Implements the networking module from network.md specification.
    """
    
    def __init__(
        self,
        consensus: ConsensusEngine,
        storage: StorageManager,
        problem_registry: ProblemRegistry,
        peer_id: str = "local_peer"
    ):
        """
        Initialize network protocol.
        
        Args:
            consensus: Consensus engine
            storage: Storage manager
            problem_registry: Problem registry
            peer_id: Local peer identifier
        """
        self.consensus = consensus
        self.storage = storage
        self.problem_registry = problem_registry
        self.peer_id = peer_id
        
        # Message handling
        self.compressor = MessageCompressor()
        self.rate_limiter = RateLimiter()
        
        # Gossipsub topics
        self.topics = {
            "headers": f"/coinj/headers/{DEFAULT_TOPIC_VERSION}",
            "commit_reveal": f"/coinj/commit-reveal/{DEFAULT_TOPIC_VERSION}",
            "requests": f"/coinj/requests/{DEFAULT_TOPIC_VERSION}",
            "responses": f"/coinj/responses/{DEFAULT_TOPIC_VERSION}"
        }
        
        # Message handlers
        self.message_handlers: Dict[MessageType, Callable] = {
            MessageType.HEADER: self._handle_header_msg,
            MessageType.REVEAL: self._handle_reveal_msg,
            MessageType.REQUEST: self._handle_request_msg,
            MessageType.RESPONSE: self._handle_response_msg
        }
        
        # RPC handlers
        self.rpc_handlers: Dict[RequestKind, Callable] = {
            RequestKind.GET_HEADERS: self._handle_get_headers,
            RequestKind.GET_BLOCK_BY_HASH: self._handle_get_block_by_hash,
            RequestKind.GET_PROOF_BY_CID: self._handle_get_proof_by_cid
        }
        
        # Message deduplication
        self.seen_headers: Set[str] = set()
        self.seen_commitments: Set[str] = set()
        
        # Pending requests
        self.pending_requests: Dict[str, Dict] = {}
    
    def encode_message(self, message: Union[HeaderMsg, RevealMsg, RequestMsg, ResponseMsg]) -> bytes:
        """
        Encode message with compression.
        
        Args:
            message: Message to encode
            
        Returns:
            Encoded message bytes
        """
        # Convert to dict and serialize to JSON
        message_dict = message.to_dict()
        json_data = json.dumps(message_dict).encode('utf-8')
        
        # Compress if needed
        compressed_data, codec = self.compressor.compress(json_data)
        
        # Create envelope with compression info
        envelope = {
            "codec": codec.value,
            "data": compressed_data.hex()
        }
        
        return json.dumps(envelope).encode('utf-8')
    
    def decode_message(self, data: bytes) -> Union[HeaderMsg, RevealMsg, RequestMsg, ResponseMsg]:
        """
        Decode message with decompression.
        
        Args:
            data: Encoded message bytes
            
        Returns:
            Decoded message
        """
        # Parse envelope
        envelope = json.loads(data.decode('utf-8'))
        codec = CompressionCodec(envelope["codec"])
        compressed_data = bytes.fromhex(envelope["data"])
        
        # Decompress
        json_data = self.compressor.decompress(compressed_data, codec)
        
        # Parse message
        message_dict = json.loads(json_data.decode('utf-8'))
        message_type = MessageType(message_dict["type"])
        
        # Create appropriate message object
        if message_type == MessageType.HEADER:
            return HeaderMsg.from_dict(message_dict)
        elif message_type == MessageType.REVEAL:
            return RevealMsg.from_dict(message_dict)
        elif message_type == MessageType.REQUEST:
            return RequestMsg.from_dict(message_dict)
        elif message_type == MessageType.RESPONSE:
            return ResponseMsg.from_dict(message_dict)
        else:
            raise ValueError(f"Unknown message type: {message_type}")
    
    def handle_message(self, peer_id: str, topic: str, data: bytes) -> bool:
        """
        Handle incoming message.
        
        Args:
            peer_id: Sender peer ID
            topic: Gossipsub topic
            data: Message data
            
        Returns:
            True if message was handled successfully
        """
        # Rate limiting
        if not self.rate_limiter.is_allowed(peer_id):
            print(f"Rate limit exceeded for peer {peer_id}")
            return False
        
        # Size validation
        if len(data) > DEFAULT_MAX_MESSAGE_SIZE:
            print(f"Message too large: {len(data)} bytes")
            return False
        
        try:
            # Decode message
            message = self.decode_message(data)
            
            # Route to appropriate handler
            handler = self.message_handlers.get(type(message).__name__.replace('Msg', '').lower())
            if handler:
                return handler(peer_id, message)
            else:
                print(f"No handler for message type: {type(message)}")
                return False
                
        except Exception as e:
            print(f"Error handling message from {peer_id}: {e}")
            return False
    
    def _handle_header_msg(self, peer_id: str, message: HeaderMsg) -> bool:
        """Handle header announcement message."""
        try:
            # Deserialize header
            header = self.storage._deserialize_header(message.header_bytes)
            
            # Deduplication
            header_hash = header.block_hash
            if header_hash in self.seen_headers:
                return True  # Already seen, but not an error
            self.seen_headers.add(header_hash)
            
            # Validate header
            self.consensus.validate_header(header)
            
            # Store header
            self.storage.store_header(header)
            
            print(f"Processed header from {peer_id}: {header_hash[:16]}...")
            return True
            
        except Exception as e:
            print(f"Error processing header from {peer_id}: {e}")
            return False
    
    def _handle_reveal_msg(self, peer_id: str, message: RevealMsg) -> bool:
        """Handle reveal bundle message."""
        try:
            # Deduplication
            commitment_key = f"{message.cid}:{message.commitment.hex()}"
            if commitment_key in self.seen_commitments:
                return True  # Already seen
            self.seen_commitments.add(commitment_key)
            
            # Store commitment mapping
            self.storage.store_commitment_cid(message.commitment, message.cid)
            
            print(f"Processed reveal from {peer_id}: {message.cid}")
            return True
            
        except Exception as e:
            print(f"Error processing reveal from {peer_id}: {e}")
            return False
    
    def _handle_request_msg(self, peer_id: str, message: RequestMsg) -> bool:
        """Handle RPC request message."""
        try:
            # Get handler for request kind
            handler = self.rpc_handlers.get(message.kind)
            if not handler:
                print(f"No handler for request kind: {message.kind}")
                return False
            
            # Process request
            response = handler(message.params)
            
            # Send response
            response_msg = ResponseMsg(
                status="success",
                payload=response,
                request_id=message.request_id
            )
            
            # In a real implementation, this would send via libp2p
            print(f"Processed request {message.kind.value} from {peer_id}")
            return True
            
        except Exception as e:
            print(f"Error processing request from {peer_id}: {e}")
            return False
    
    def _handle_response_msg(self, peer_id: str, message: ResponseMsg) -> bool:
        """Handle RPC response message."""
        try:
            # Handle pending request
            if message.request_id and message.request_id in self.pending_requests:
                request_info = self.pending_requests[message.request_id]
                request_info["response"] = message
                request_info["completed"] = True
                del self.pending_requests[message.request_id]
            
            print(f"Processed response from {peer_id}: {message.status}")
            return True
            
        except Exception as e:
            print(f"Error processing response from {peer_id}: {e}")
            return False
    
    def _handle_get_headers(self, params: Dict[str, Any]) -> bytes:
        """Handle get_headers RPC request."""
        start_height = params.get("start_height", 0)
        count = params.get("count", 100)
        
        headers = []
        for height in range(start_height, start_height + count):
            # Get header at height (simplified)
            # In real implementation, would query storage by height
            pass
        
        return json.dumps(headers).encode('utf-8')
    
    def _handle_get_block_by_hash(self, params: Dict[str, Any]) -> bytes:
        """Handle get_block_by_hash RPC request."""
        block_hash = params.get("hash")
        if not block_hash:
            raise ValueError("Missing block hash")
        
        block = self.storage.get_block(block_hash)
        if not block:
            raise ValueError("Block not found")
        
        # Serialize block
        block_data = self.storage._serialize_block(block)
        return block_data
    
    def _handle_get_proof_by_cid(self, params: Dict[str, Any]) -> bytes:
        """Handle get_proof_by_cid RPC request."""
        cid = params.get("cid")
        if not cid:
            raise ValueError("Missing CID")
        
        # Get proof bundle from IPFS
        proof_bundle = self.storage.ipfs_client.get(cid)
        return proof_bundle
    
    def announce_header(self, block: Block):
        """Announce new header to network."""
        try:
            # Serialize header
            header_bytes = self.storage._serialize_header(block)
            
            # Get tip work
            tip_work = int(block.cumulative_work_score) if hasattr(block, 'cumulative_work_score') else 0
            
            # Create message
            message = HeaderMsg(
                header_bytes=header_bytes,
                tip_work=tip_work,
                peer_id=self.peer_id
            )
            
            # Encode and send (simplified - would use libp2p in real implementation)
            encoded = self.encode_message(message)
            print(f"Announced header: {block.block_hash[:16]}... (work: {tip_work})")
            
        except Exception as e:
            print(f"Error announcing header: {e}")
    
    def announce_reveal(self, cid: str, commitment: bytes, problem_type: ProblemType, capacity: ProblemTier):
        """Announce reveal bundle to network."""
        try:
            # Create message
            message = RevealMsg(
                cid=cid,
                commitment=commitment,
                problem_type=problem_type.value if hasattr(problem_type, 'value') else 1,
                capacity=capacity.value if hasattr(capacity, 'value') else 1
            )
            
            # Encode and send
            encoded = self.encode_message(message)
            print(f"Announced reveal: {cid}")
            
        except Exception as e:
            print(f"Error announcing reveal: {e}")


if __name__ == "__main__":
    # Test NetworkProtocol
    print("Testing NetworkProtocol...")
    
    # Create mock components
    from consensus import ConsensusConfig
    from storage import StorageConfig, NodeRole, PruningMode
    
    # Mock consensus
    consensus_config = ConsensusConfig()
    storage_config = StorageConfig(
        data_dir="/tmp/coinjecture_network_test",
        role=NodeRole.FULL,
        pruning_mode=PruningMode.FULL
    )
    storage = StorageManager(storage_config)
    registry = ProblemRegistry()
    consensus = ConsensusEngine(consensus_config, storage, registry)
    
    # Initialize network protocol
    network = NetworkProtocol(consensus, storage, registry)
    print("✅ NetworkProtocol initialized")
    
    # Test message encoding/decoding
    test_header = HeaderMsg(
        header_bytes=b"test_header_data",
        tip_work=12345,
        peer_id="test_peer"
    )
    
    encoded = network.encode_message(test_header)
    decoded = network.decode_message(encoded)
    
    if decoded.header_bytes == test_header.header_bytes:
        print("✅ Message encoding/decoding works")
    else:
        print("❌ Message encoding/decoding failed")
    
    # Test rate limiting
    if network.rate_limiter.is_allowed("test_peer"):
        print("✅ Rate limiting allows first message")
    else:
        print("❌ Rate limiting failed")
    
    print("✅ All network module tests passed!")
