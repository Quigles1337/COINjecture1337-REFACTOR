# Changelog

All notable changes to COINjecture will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.2] - 2025-10-15

### Added
- **POW Module** (`src/pow.py`) - Implements `docs/blockchain/pow.md` specification
  - ProblemRegistry class with generate/solve/verify methods
  - Commit-reveal protocol helpers (derive_epoch_salt, create_commitment, verify_commitment)
  - Problem encoding/decoding for deterministic serialization
  - DifficultyAdjuster class with EWMA-based adjustment
  - Work score calculation integration
  - Anti-grinding mechanisms
- **Storage Module** (`src/storage.py`) - Implements `docs/blockchain/storage.md` specification
  - StorageManager class with SQLite database backend
  - IPFS client integration for proof bundle storage
  - Node role support (light, full, miner, archive)
  - Pruning strategies per node role
  - Database schema with column families (headers, blocks, tips, work_index, commit_index, peer_index)
  - Batch write operations and durability features
- `requirements.txt` file documenting external dependencies

### Changed
- Storage module uses capacity terminology throughout
- POW module wraps existing problem-solving functions
- Both modules include comprehensive test suites

### Fixed
- Missing requests dependency handled gracefully with proper error messages
- Import errors resolved with type hints and fallback imports

### Documentation
- All code includes docstrings referencing specifications
- Comprehensive inline comments for complex logic
- Test suites demonstrate proper usage

## [3.0.1] - 2025-10-15

### Added
- Diversity bonus mechanism for underrepresented capacities
  - 50% bonus for <5% market share
  - 30% bonus for <10% market share
  - 15% bonus for <15% market share
  - 10% penalty for >40% market share
- Hardware capability-based capacity selection logic
- Improved status messages showing active balancing

### Changed
- **BREAKING**: Renamed `mining_tier` to `mining_capacity` in Block class and API responses
- **BREAKING**: Changed capacity selection from profitability-driven to hardware capability-based
- Updated capability thresholds (0.3, 0.5, 0.7, 0.9) for better distribution
- Reward calculation now includes diversity bonus factor
- Status messages now indicate active balancing instead of suggestions

### Fixed
- Tier condensation issue where all miners rushed to highest tier
- Missing TIER_2_DESKTOP in capacity distribution
- Profitability now output-only metric instead of selection driver

### Documentation
- Updated DYNAMIC_TOKENOMICS.README.md with diversity bonus section
- Updated FAUCET_API.README.md to use "mining_capacity" terminology
- Updated code comments to use "hardware capacity" terminology

## [3.0.0] - 2025-01-XX

### Added
- Complete architectural refactor with utility-based design
- Dynamic work score tokenomics system
- User submissions system with aggregation strategies
- Comprehensive NP-Complete problem support
- Hardware-class-relative competition model
- Language-agnostic API specifications
- Emergent tokenomics (no predetermined schedules)
- Tier system for hardware compatibility categories
- Commit-reveal protocol for anti-grinding
- IPFS integration for proof storage
- Comprehensive documentation suite

### Changed
- **BREAKING**: Complete rewrite from testnet implementation
- **BREAKING**: New architecture focuses on verifiable computational work
- **BREAKING**: Tokenomics now emerge from network behavior
- **BREAKING**: Competition model changed to within-tier optimization

### Architecture
- **Core Module**: BlockHeader, Block, CommitmentLeaf structures
- **Consensus Module**: Cumulative work-based fork choice
- **PoW Module**: NP-Complete problem registry and work score calculation
- **Network Module**: libp2p integration with gossipsub
- **Storage Module**: IPFS integration with pruning strategies
- **Node Module**: Role-based node configuration (light, full, miner, archive)
- **CLI Module**: User-facing commands for node management

### Problem Support
- **Production Ready**: Subset Sum (O(2^n) solve, O(n) verify)
- **In Development**: Knapsack, Graph Coloring, SAT, TSP
- **Research**: Factorization, Lattice, Clique, Vertex Cover, Hamiltonian Path, Set Cover, Bin Packing, Job Scheduling

### Tokenomics
- Work score calculation based on measured complexity
- Dynamic block rewards based on network state
- Natural deflation through cumulative work growth
- Market-driven tier selection
- Hardware profile-based profitability estimation

### User Submissions
- Problem submission with bounty system
- Aggregation strategies: ANY, BEST, MULTIPLE, STATISTICAL
- Solution recording with quality metrics
- Problem pool management

### Documentation
- **MANIFESTO.md**: Vision and principles
- **ARCHITECTURE.README.md**: Complete system architecture
- **API.README.md**: Language-agnostic API specifications
- **DYNAMIC_TOKENOMICS.README.md**: Tokenomics system details
- Module-specific documentation in docs/blockchain/
- Development and testing guides

### Security
- Commit-reveal protocol prevents grinding attacks
- Epoch-based salt derivation
- Bounded reorg depth
- DOS protection with rate limiting

### Performance
- Measured complexity metrics
- Energy efficiency scoring
- Hardware capability assessment
- Market equilibrium mechanisms

## [2.x.x] - Previous Testnet Implementation

### Note
The previous testnet implementation (v2.x.x) has been archived. This version included:
- Web-based testnet DApp
- Basic subset sum PoW
- Docker deployment
- CLI tools
- PWA support

The v3.0.0 architecture represents a complete redesign focusing on:
- Utility-based design
- Emergent tokenomics
- Distributed participation
- Language-agnostic specifications

## [1.x.x] - Initial Research

### Note
Early research and proof-of-concept implementations. These versions focused on:
- Basic subset sum problem implementation
- Initial work score calculations
- Research into NP-Complete problem applications
- Theoretical framework development

---

## Version History Summary

- **v3.0.0**: Complete architectural refactor with utility-based design
- **v2.x.x**: Testnet implementation (archived)
- **v1.x.x**: Initial research and proof-of-concept (archived)

## Future Roadmap

### v3.1.0 (Planned)
- Additional NP-Complete problem implementations
- Performance optimizations
- Enhanced security features
- Multi-language implementations

### v3.2.0 (Planned)
- Advanced aggregation strategies
- Machine learning integration
- Cross-chain compatibility
- Enterprise features

### v4.0.0 (Future)
- Mainnet launch
- Production deployment
- Ecosystem development
- Community governance
