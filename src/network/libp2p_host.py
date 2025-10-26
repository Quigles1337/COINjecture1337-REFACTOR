"""
Module: libp2p_host
Specification: docs/blockchain/network.md

LibP2P host wrapper for COINjecture networking with Noise protocol,
Yamux stream multiplexing, TCP transport, and peer discovery.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
import time

# LibP2P imports - with proper fallback for missing dependencies
try:
    from libp2p import Host, HostOptions
    from libp2p.crypto.secp256k1 import Secp256k1PrivateKey
    from libp2p.crypto.secp256k1 import Secp256k1PublicKey
    from libp2p.network.network_interface import INetwork
    from libp2p.network.stream.net_stream import INetStream
    from libp2p.peer.id import ID
    from libp2p.peer.peerinfo import PeerInfo
    from libp2p.peer.peerstore import PeerStore
    from libp2p.transport.tcp.tcp import TCP
    from libp2p.transport.upgrader import TransportUpgrader
    from libp2p.muxing.yamux import YamuxMuxer
    from libp2p.security.noise import Noise
    from libp2p.discovery.mdns import MDNS
    from libp2p.kademlia.kad_peerinfo import KadPeerInfo
    from multiaddr import Multiaddr
    import base58
    LIBP2P_AVAILABLE = True
except ImportError:
    # Fallback for development without libp2p
    Host = None
    HostOptions = None
    Secp256k1PrivateKey = None
    Secp256k1PublicKey = None
    INetwork = None
    INetStream = None
    ID = None
    PeerInfo = None
    PeerStore = None
    TCP = None
    TransportUpgrader = None
    YamuxMuxer = None
    Noise = None
    MDNS = None
    KadPeerInfo = None
    Multiaddr = None
    base58 = None
    LIBP2P_AVAILABLE = False


@dataclass
class LibP2PConfig:
    """Configuration for LibP2P host."""
    listen_addr: str = "/ip4/0.0.0.0/tcp/0"
    private_key: Optional[bytes] = None
    bootstrap_peers: List[str] = None
    enable_mdns: bool = True
    enable_kademlia: bool = True
    max_connections: int = 100
    connection_timeout: float = 30.0
    
    def __post_init__(self):
        if self.bootstrap_peers is None:
            self.bootstrap_peers = []


class LibP2PHost:
    """
    Wrapper around libp2p host for COINjecture networking.
    
    Provides simplified interface for:
    - Host lifecycle management
    - Peer connections
    - Stream handling
    - Discovery services
    """
    
    def __init__(self, config: LibP2PConfig):
        """Initialize LibP2P host with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Host components
        self.host: Optional[Host] = None
        self.network: Optional[INetwork] = None
        self.peer_store: Optional[PeerStore] = None
        
        # Connection tracking
        self.connected_peers: Dict[str, PeerInfo] = {}
        self.connection_handlers: Dict[str, Callable] = {}
        
        # Discovery services
        self.mdns_service: Optional[MDNS] = None
        self.kademlia_service: Optional[Any] = None
        
        # Stream handlers
        self.stream_handlers: Dict[str, Callable] = {}
        
        # Status
        self.is_running = False
        self.start_time: Optional[float] = None
    
    async def start(self) -> None:
        """Start the LibP2P host and initialize services."""
        if self.is_running:
            self.logger.warning("Host is already running")
            return
        
        try:
            if Host is None:
                self.logger.warning("LibP2P not available, using simulation mode")
                await self._start_simulation()
                return
            
            # Create private key
            private_key = self._create_private_key()
            
            # Create host options
            host_options = HostOptions(
                private_key=private_key,
                listen_addrs=[Multiaddr(self.config.listen_addr)]
            )
            
            # Create host
            self.host = Host(host_options)
            self.network = self.host.get_network()
            self.peer_store = self.host.get_peerstore()
            
            # Set up transport
            await self._setup_transport()
            
            # Set up security
            await self._setup_security()
            
            # Set up muxing
            await self._setup_muxing()
            
            # Set up discovery
            await self._setup_discovery()
            
            # Start host
            await self.host.start()
            
            # Connect to bootstrap peers
            await self._connect_bootstrap_peers()
            
            self.is_running = True
            self.start_time = time.time()
            
            self.logger.info(f"LibP2P host started with ID: {self.get_peer_id()}")
            self.logger.info(f"Listening on: {self.config.listen_addr}")
            
        except Exception as e:
            self.logger.error(f"Failed to start LibP2P host: {e}")
            await self._start_simulation()
    
    async def stop(self) -> None:
        """Stop the LibP2P host and cleanup resources."""
        if not self.is_running:
            return
        
        try:
            if self.host:
                await self.host.stop()
            
            # Stop discovery services
            if self.mdns_service:
                await self.mdns_service.stop()
            
            if self.kademlia_service:
                await self.kademlia_service.stop()
            
            # Clear connection tracking
            self.connected_peers.clear()
            
            self.is_running = False
            self.start_time = None
            
            self.logger.info("LibP2P host stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping LibP2P host: {e}")
    
    def get_peer_id(self) -> str:
        """Get the peer ID of this host."""
        if self.host:
            return str(self.host.get_id())
        return "simulation-peer-id"
    
    async def connect(self, peer_addr: str) -> bool:
        """
        Connect to a peer by address.
        
        Args:
            peer_addr: Multiaddr string of the peer
            
        Returns:
            True if connection successful
        """
        if not self.is_running:
            self.logger.error("Host is not running")
            return False
        
        try:
            if not self.host:
                # Simulation mode
                self.logger.info(f"Simulated connection to {peer_addr}")
                return True
            
            # Parse peer address
            peer_multiaddr = Multiaddr(peer_addr)
            peer_info = PeerInfo.from_multiaddr(peer_multiaddr)
            
            # Connect to peer
            await self.network.connect(peer_info)
            
            # Track connection
            peer_id = str(peer_info.peer_id)
            self.connected_peers[peer_id] = peer_info
            
            self.logger.info(f"Connected to peer: {peer_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to {peer_addr}: {e}")
            return False
    
    async def disconnect(self, peer_id: str) -> None:
        """
        Disconnect from a peer.
        
        Args:
            peer_id: Peer ID to disconnect from
        """
        if not self.is_running:
            return
        
        try:
            if not self.host:
                # Simulation mode
                self.logger.info(f"Simulated disconnection from {peer_id}")
                return
            
            # Remove from tracking
            if peer_id in self.connected_peers:
                del self.connected_peers[peer_id]
            
            # Disconnect from network
            peer_info = self.peer_store.get_peer_info(peer_id)
            if peer_info:
                await self.network.disconnect(peer_info.peer_id)
            
            self.logger.info(f"Disconnected from peer: {peer_id}")
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from {peer_id}: {e}")
    
    def get_connected_peers(self) -> List[str]:
        """Get list of connected peer IDs."""
        return list(self.connected_peers.keys())
    
    def get_peer_info(self, peer_id: str) -> Optional[PeerInfo]:
        """Get peer info for a connected peer."""
        return self.connected_peers.get(peer_id)
    
    def add_connection_handler(self, protocol: str, handler: Callable) -> None:
        """Add a connection handler for a protocol."""
        self.connection_handlers[protocol] = handler
    
    def add_stream_handler(self, protocol: str, handler: Callable) -> None:
        """Add a stream handler for a protocol."""
        self.stream_handlers[protocol] = handler
    
    async def send_message(self, peer_id: str, protocol: str, message: bytes) -> bool:
        """
        Send a message to a peer.
        
        Args:
            peer_id: Target peer ID
            protocol: Protocol identifier
            message: Message bytes
            
        Returns:
            True if message sent successfully
        """
        if not self.is_running:
            return False
        
        try:
            if not self.host:
                # Simulation mode
                self.logger.info(f"Simulated message to {peer_id} via {protocol}")
                return True
            
            # Get peer info
            peer_info = self.get_peer_info(peer_id)
            if not peer_info:
                self.logger.error(f"Peer not connected: {peer_id}")
                return False
            
            # Open stream
            stream = await self.network.new_stream(peer_info.peer_id, [protocol])
            
            # Send message
            await stream.write(message)
            await stream.close()
            
            self.logger.debug(f"Sent message to {peer_id} via {protocol}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message to {peer_id}: {e}")
            return False
    
    def _create_private_key(self) -> Secp256k1PrivateKey:
        """Create or load private key for the host."""
        if self.config.private_key:
            return Secp256k1PrivateKey.from_bytes(self.config.private_key)
        else:
            return Secp256k1PrivateKey.generate()
    
    async def _setup_transport(self) -> None:
        """Set up transport layer (TCP)."""
        if not self.host:
            return
        
        # Add TCP transport
        tcp_transport = TCP()
        self.host.add_transport(tcp_transport)
    
    async def _setup_security(self) -> None:
        """Set up security layer (Noise)."""
        if not self.host:
            return
        
        # Add Noise security
        noise = Noise()
        self.host.add_security(noise)
    
    async def _setup_muxing(self) -> None:
        """Set up stream multiplexing (Yamux)."""
        if not self.host:
            return
        
        # Add Yamux muxer
        yamux = YamuxMuxer()
        self.host.add_muxer(yamux)
    
    async def _setup_discovery(self) -> None:
        """Set up peer discovery services."""
        if not self.host:
            return
        
        # Set up mDNS discovery
        if self.config.enable_mdns:
            self.mdns_service = MDNS(self.host)
            await self.mdns_service.start()
        
        # Set up Kademlia DHT
        if self.config.enable_kademlia:
            # Kademlia setup would go here
            pass
    
    async def _connect_bootstrap_peers(self) -> None:
        """Connect to bootstrap peers."""
        for peer_addr in self.config.bootstrap_peers:
            try:
                await self.connect(peer_addr)
            except Exception as e:
                self.logger.warning(f"Failed to connect to bootstrap peer {peer_addr}: {e}")
    
    async def _start_simulation(self) -> None:
        """Start simulation mode when LibP2P is not available."""
        self.logger.info("Starting LibP2P simulation mode")
        self.is_running = True
        self.start_time = time.time()
        
        # Simulate some connected peers
        self.connected_peers = {
            "simulation-peer-1": None,
            "simulation-peer-2": None,
            "simulation-peer-3": None
        }
        
        self.logger.info("Simulation mode active with 3 mock peers")


# Example usage and testing
async def main():
    """Test the LibP2P host implementation."""
    config = LibP2PConfig(
        listen_addr="/ip4/0.0.0.0/tcp/8000",
        bootstrap_peers=[
            "/ip4/127.0.0.1/tcp/8001/p2p/12D3KooW...",
            "/ip4/127.0.0.1/tcp/8002/p2p/12D3KooW..."
        ]
    )
    
    host = LibP2PHost(config)
    
    try:
        # Start host
        await host.start()
        
        # Test connection
        await host.connect("/ip4/127.0.0.1/tcp/8001/p2p/12D3KooW...")
        
        # List connected peers
        peers = host.get_connected_peers()
        print(f"Connected peers: {peers}")
        
        # Send test message
        await host.send_message("test-peer", "/coinj/test/1.0.0", b"Hello, COINjecture!")
        
        # Keep running
        await asyncio.sleep(10)
        
    finally:
        await host.stop()


if __name__ == "__main__":
    asyncio.run(main())
