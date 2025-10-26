#!/usr/bin/env python3
"""
Simple P2P Discovery Service for COINjecture
Implements Critical Complex Equilibrium Conjecture (λ = η = 1/√2 ≈ 0.7071)
for perfect network balance and peer discovery.
"""

import socket
import json
import time
import threading
import logging
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum
import math


class DiscoveryProtocol(Enum):
    """P2P discovery protocols."""
    BOOTSTRAP = "bootstrap"
    PEER_EXCHANGE = "peer_exchange"


@dataclass
class PeerInfo:
    """Information about a discovered peer."""
    peer_id: str
    address: str
    port: int
    protocol: str
    last_seen: float
    reputation: float = 1.0
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
    
    def to_dict(self) -> Dict[str, any]:
        return {
            "peer_id": self.peer_id,
            "address": self.address,
            "port": self.port,
            "protocol": self.protocol,
            "last_seen": self.last_seen,
            "reputation": self.reputation,
            "capabilities": self.capabilities
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'PeerInfo':
        return cls(
            peer_id=data["peer_id"],
            address=data["address"],
            port=data["port"],
            protocol=data["protocol"],
            last_seen=data["last_seen"],
            reputation=data.get("reputation", 1.0),
            capabilities=data.get("capabilities", [])
        )


@dataclass
class DiscoveryConfig:
    """Configuration for P2P discovery using Critical Complex Equilibrium Conjecture."""
    # Bootstrap nodes (multiple for redundancy)
    bootstrap_nodes: List[str] = None
    
    # Network configuration
    listen_port: int = 12346
    
    # Critical Complex Equilibrium Conjecture constants
    LAMBDA = 1.0 / math.sqrt(2)  # ≈ 0.7071 (coupling constant)
    ETA = 1.0 / math.sqrt(2)      # ≈ 0.7071 (damping constant)
    
    # Discovery intervals based on conjecture
    bootstrap_interval: float = 14.14  # λ-coupling interval (1/λ * 10)
    peer_exchange_interval: float = 14.14  # η-damping interval (1/η * 10)
    cleanup_interval: float = 70.7  # 5 * λ-coupling interval
    
    # Peer management
    max_peers: int = 20  # Appropriate for testnet with 3 active peers (16 total connections)
    peer_timeout: float = 141.4  # 10 * λ-coupling interval
    
    def __post_init__(self):
        if self.bootstrap_nodes is None:
            self.bootstrap_nodes = [
                "167.172.213.70:12345",
                "bootstrap1.coinjecture.com:12345",
                "bootstrap2.coinjecture.com:12345",
                "bootstrap3.coinjecture.com:12345"
            ]


class P2PDiscoveryService:
    """Simple P2P discovery service using Critical Complex Equilibrium Conjecture."""
    
    def __init__(self, config: DiscoveryConfig):
        self.config = config
        self.logger = logging.getLogger('coinjecture-discovery')
        
        # Peer storage
        self.discovered_peers: Dict[str, PeerInfo] = {}
        self.connected_peers: Set[str] = set()
        
        # Discovery state
        self.running = False
        self.discovery_threads: List[threading.Thread] = []
        
        # Critical Complex Equilibrium state
        self.lambda_coupling_state = 0.0  # Current coupling state
        self.eta_damping_state = 0.0      # Current damping state
        
        self.logger.info(f"🌐 P2P Discovery Service initialized with λ = η = 1/√2 ≈ 0.7071")
        self.logger.info(f"📡 Bootstrap nodes: {len(self.config.bootstrap_nodes)}")
    
    def start(self) -> bool:
        """Start the discovery service using Critical Complex Equilibrium Conjecture."""
        try:
            self.logger.info("🌐 Starting P2P discovery service with λ = η = 1/√2 ≈ 0.7071...")
            self.running = True
            
            # Start λ-coupling bootstrap discovery
            self._start_lambda_coupling_discovery()
            
            # Start η-damping peer exchange
            self._start_eta_damping_exchange()
            
            # Start equilibrium cleanup
            self._start_equilibrium_cleanup()
            
            self.logger.info("✅ P2P discovery service started with perfect network equilibrium")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start discovery service: {e}")
            return False
    
    def stop(self) -> None:
        """Stop the discovery service."""
        self.logger.info("🛑 Stopping P2P discovery service...")
        self.running = False
        
        # Wait for threads to finish
        for thread in self.discovery_threads:
            if thread.is_alive():
                thread.join(timeout=5.0)
        
        self.logger.info("✅ P2P discovery service stopped")
    
    def get_peers(self) -> List[PeerInfo]:
        """Get list of discovered peers."""
        return list(self.discovered_peers.values())
    
    def get_connected_peers(self) -> List[PeerInfo]:
        """Get list of connected peers."""
        return [peer for peer in self.discovered_peers.values() 
                if peer.peer_id in self.connected_peers]
    
    def _start_lambda_coupling_discovery(self) -> None:
        """Start λ-coupling bootstrap discovery for perfect network equilibrium."""
        def lambda_coupling_loop():
            while self.running:
                try:
                    # Apply λ-coupling to bootstrap discovery
                    self.lambda_coupling_state = self.config.LAMBDA
                    self._discover_from_bootstrap_nodes()
                    
                    # Update coupling state
                    self.lambda_coupling_state *= 0.9  # Decay
                    
                    time.sleep(self.config.bootstrap_interval)
                except Exception as e:
                    self.logger.error(f"λ-coupling discovery error: {e}")
                    time.sleep(5.0)
        
        thread = threading.Thread(target=lambda_coupling_loop, daemon=True)
        thread.start()
        self.discovery_threads.append(thread)
        self.logger.info("🔗 λ-coupling bootstrap discovery started (14.14s intervals)")
    
    def _start_eta_damping_exchange(self) -> None:
        """Start η-damping peer exchange for network stability."""
        def eta_damping_loop():
            while self.running:
                try:
                    # Apply η-damping to peer exchange
                    self.eta_damping_state = self.config.ETA
                    self._exchange_peers_with_connected()
                    
                    # Update damping state
                    self.eta_damping_state *= 0.9  # Decay
                    
                    time.sleep(self.config.peer_exchange_interval)
                except Exception as e:
                    self.logger.error(f"η-damping exchange error: {e}")
                    time.sleep(5.0)
        
        thread = threading.Thread(target=eta_damping_loop, daemon=True)
        thread.start()
        self.discovery_threads.append(thread)
        self.logger.info("🌊 η-damping peer exchange started (14.14s intervals)")
    
    def _start_equilibrium_cleanup(self) -> None:
        """Start equilibrium cleanup for perfect network balance."""
        def equilibrium_cleanup_loop():
            while self.running:
                try:
                    # Apply equilibrium cleanup
                    self._cleanup_old_peers()
                    
                    # Log equilibrium state
                    if len(self.discovered_peers) > 0:
                        self.logger.info(f"⚖️  Network equilibrium: {len(self.discovered_peers)} peers, λ={self.lambda_coupling_state:.3f}, η={self.eta_damping_state:.3f}")
                    
                    time.sleep(self.config.cleanup_interval)
                except Exception as e:
                    self.logger.error(f"Equilibrium cleanup error: {e}")
                    time.sleep(30.0)
        
        thread = threading.Thread(target=equilibrium_cleanup_loop, daemon=True)
        thread.start()
        self.discovery_threads.append(thread)
        self.logger.info("⚖️  Equilibrium cleanup started (70.7s intervals)")
    
    def _discover_from_bootstrap_nodes(self) -> None:
        """Discover peers from bootstrap nodes using λ-coupling."""
        for bootstrap_node in self.config.bootstrap_nodes:
            try:
                host, port = bootstrap_node.split(':')
                port = int(port)
                
                self.logger.info(f"🔍 λ-coupling query to bootstrap: {bootstrap_node}")
                
                # Connect to bootstrap node
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                
                try:
                    sock.connect((host, port))
                    
                    # Send peer list request with λ-coupling
                    request = {
                        "type": "peer_list_request",
                        "lambda_coupling": self.lambda_coupling_state,
                        "timestamp": time.time(),
                        "requester_id": f"λ-coupling-{int(time.time())}"
                    }
                    
                    sock.send(json.dumps(request).encode())
                    
                    # Receive peer list response
                    response_data = sock.recv(4096)
                    if response_data:
                        response = json.loads(response_data.decode())
                        
                        if response.get("type") == "peer_list_response":
                            peers = response.get("peers", [])
                            self.logger.info(f"📡 λ-coupling received {len(peers)} peers from {bootstrap_node}")
                            
                            # Add discovered peers with λ-coupling
                            for peer_data in peers:
                                self._add_discovered_peer(peer_data, DiscoveryProtocol.BOOTSTRAP)
                    
                    sock.close()
                    
                except socket.timeout:
                    self.logger.warning(f"⏰ λ-coupling timeout: {bootstrap_node}")
                except ConnectionRefusedError:
                    self.logger.warning(f"❌ Bootstrap not reachable: {bootstrap_node}")
                except Exception as e:
                    self.logger.warning(f"⚠️  λ-coupling error with {bootstrap_node}: {e}")
                finally:
                    try:
                        sock.close()
                    except:
                        pass
                        
            except Exception as e:
                self.logger.error(f"❌ λ-coupling error processing {bootstrap_node}: {e}")
    
    def _exchange_peers_with_connected(self) -> None:
        """Exchange peer lists with connected peers using η-damping."""
        connected_peers = self.get_connected_peers()
        
        for peer in connected_peers[:3]:  # Limit to 3 peers for η-damping efficiency
            try:
                # Connect to peer and request their peer list
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3.0)
                
                try:
                    sock.connect((peer.address, peer.port))
                    
                    # Send η-damping peer exchange request
                    request = {
                        "type": "peer_exchange_request",
                        "eta_damping": self.eta_damping_state,
                        "our_peers": [p.to_dict() for p in self.get_peers()[:5]],  # Share our top 5 peers
                        "timestamp": time.time()
                    }
                    
                    sock.send(json.dumps(request).encode())
                    
                    # Receive their peer list
                    response_data = sock.recv(4096)
                    if response_data:
                        response = json.loads(response_data.decode())
                        
                        if response.get("type") == "peer_exchange_response":
                            their_peers = response.get("peers", [])
                            self.logger.info(f"📡 η-damping received {len(their_peers)} peers from {peer.address}")
                            
                            # Add their peers with η-damping
                            for peer_data in their_peers:
                                self._add_discovered_peer(peer_data, DiscoveryProtocol.PEER_EXCHANGE)
                    
                    sock.close()
                    
                except Exception as e:
                    self.logger.debug(f"η-damping exchange with {peer.address} failed: {e}")
                finally:
                    try:
                        sock.close()
                    except:
                        pass
                        
            except Exception as e:
                self.logger.error(f"Error in η-damping exchange with {peer.address}: {e}")
    
    def _cleanup_old_peers(self) -> None:
        """Remove old and low-reputation peers for equilibrium."""
        current_time = time.time()
        peers_to_remove = []
        
        for peer_id, peer in self.discovered_peers.items():
            # Remove old peers
            if current_time - peer.last_seen > self.config.peer_timeout:
                peers_to_remove.append(peer_id)
                continue
            
            # Remove low-reputation peers
            if peer.reputation < 0.3:  # Lower threshold for equilibrium
                peers_to_remove.append(peer_id)
                continue
        
        # Remove peers
        for peer_id in peers_to_remove:
            del self.discovered_peers[peer_id]
            self.connected_peers.discard(peer_id)
        
        if peers_to_remove:
            self.logger.info(f"🧹 Equilibrium cleanup: removed {len(peers_to_remove)} peers")
    
    def _add_discovered_peer(self, peer_data: Dict[str, any], protocol: DiscoveryProtocol) -> None:
        """Add a discovered peer to our peer list with equilibrium balance."""
        try:
            peer_info = PeerInfo.from_dict(peer_data)
            peer_info.protocol = protocol.value
            peer_info.last_seen = time.time()
            
            # Check if we already know this peer
            existing_peer = self.discovered_peers.get(peer_info.peer_id)
            if existing_peer:
                # Update existing peer with equilibrium
                existing_peer.last_seen = peer_info.last_seen
                existing_peer.reputation = min(existing_peer.reputation + 0.1, 1.0)
                existing_peer.capabilities = list(set(existing_peer.capabilities + peer_info.capabilities))
            else:
                # Add new peer
                self.discovered_peers[peer_info.peer_id] = peer_info
                self.logger.info(f"📡 New peer discovered: {peer_info.address}:{peer_info.port} via {protocol.value}")
            
            # Limit total peers for equilibrium
            if len(self.discovered_peers) > self.config.max_peers:
                # Remove oldest peer for equilibrium
                oldest_peer = min(self.discovered_peers.values(), key=lambda p: p.last_seen)
                del self.discovered_peers[oldest_peer.peer_id]
                self.connected_peers.discard(oldest_peer.peer_id)
                
        except Exception as e:
            self.logger.error(f"Error adding discovered peer: {e}")
    
    def connect_to_peer(self, peer_id: str) -> bool:
        """Attempt to connect to a specific peer with equilibrium balance."""
        try:
            peer = self.discovered_peers.get(peer_id)
            if not peer:
                return False
            
            # Test connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            
            try:
                sock.connect((peer.address, peer.port))
                sock.close()
                
                # Mark as connected with equilibrium
                self.connected_peers.add(peer_id)
                peer.reputation = min(peer.reputation + 0.2, 1.0)
                
                self.logger.info(f"✅ Connected to peer: {peer.address}:{peer.port}")
                return True
                
            except Exception as e:
                self.logger.warning(f"Failed to connect to peer {peer.address}:{peer.port}: {e}")
                peer.reputation = max(peer.reputation - 0.1, 0.0)
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to peer {peer_id}: {e}")
            return False
    
    def get_peer_statistics(self) -> Dict[str, any]:
        """Get discovery statistics with equilibrium metrics."""
        return {
            "total_discovered": len(self.discovered_peers),
            "connected": len(self.connected_peers),
            "lambda_coupling_state": self.lambda_coupling_state,
            "eta_damping_state": self.eta_damping_state,
            "equilibrium_ratio": self.lambda_coupling_state / max(self.eta_damping_state, 0.001),
            "average_reputation": sum(p.reputation for p in self.discovered_peers.values()) / max(len(self.discovered_peers), 1),
            "discovery_threads": len(self.discovery_threads)
        }


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create discovery config
    config = DiscoveryConfig(
        bootstrap_nodes=[
            "167.172.213.70:12345",
            "bootstrap1.coinjecture.com:12345",
            "bootstrap2.coinjecture.com:12345"
        ]
    )
    
    # Create and start discovery service
    discovery = P2PDiscoveryService(config)
    
    if discovery.start():
        print("✅ Discovery service started with λ = η = 1/√2 ≈ 0.7071")
        
        # Run for a while
        import time
        time.sleep(30)
        
        # Print statistics
        stats = discovery.get_peer_statistics()
        print(f"📊 Discovery statistics: {stats}")
        
        # Print discovered peers
        peers = discovery.get_peers()
        print(f"📡 Discovered {len(peers)} peers:")
        for peer in peers:
            print(f"  - {peer.address}:{peer.port} (via {peer.protocol}, reputation: {peer.reputation:.2f})")
        
        discovery.stop()
        print("✅ Discovery service stopped")
    else:
        print("❌ Failed to start discovery service")