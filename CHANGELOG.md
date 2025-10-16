# Changelog

All notable changes to COINjecture will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.6] - 2025-10-15

### Fixed
- **IPFS health check method** now uses POST instead of GET for API calls
- **IPFS connectivity detection** fixed to properly check node health
- **Proof bundle storage** should now pass health checks and upload successfully

### Technical Details
- Fixed IPFS health check to use POST method for `/api/v0/id` endpoint
- IPFS API requires POST method for most endpoints, not GET
- Should resolve "IPFS not available" warnings and enable proof bundle uploads

#buildinginpublic #blockchain #bugfix

## [3.1.5] - 2025-10-15

### Fixed
- **IPFS client add method** now uses proper multipart form data for file uploads
- **IPFS upload functionality** fixed to work with IPFS API requirements
- **Proof bundle storage** should now successfully upload to IPFS on droplet

### Technical Details
- Fixed IPFS client `add` method to use `requests.files` parameter instead of raw bytes
- IPFS API requires multipart form data for file uploads, not raw POST data
- Should resolve "IPFS not available" warnings and enable actual proof bundle storage

#buildinginpublic #blockchain #bugfix

## [3.1.4] - 2025-10-15

### Fixed
- **Additional import fixes** for core.blockchain imports in ConsensusEngine
- **ProblemType import** in _build_genesis method now uses try-except pattern
- **subset_sum_complexity and EnergyMetrics imports** now use relative/absolute import fallback
- **Complete import resolution** for all consensus module dependencies

### Technical Details
- Fixed remaining hardcoded imports in _build_genesis method
- All core.blockchain imports now follow consistent try-except pattern
- Ensures consensus engine works on both local development and production deployments
- Resolves remaining `ModuleNotFoundError: No module named 'core'` issues

#buildinginpublic #blockchain #bugfix

## [3.1.3] - 2025-10-15

### Fixed
- **Critical import error** in ConsensusEngine preventing IPFS proof bundle uploads
- **Module resolution** - Added try-except import pattern for proof_bundler module
- **IPFS integration** now properly uploads genesis block proof data on droplet

### Technical Details
- Fixed import statement in `_build_genesis` method to follow relative/absolute import pattern
- Ensures IPFS proof bundles upload correctly when consensus engine initializes
- Resolves `ModuleNotFoundError: No module named 'api'` on production deployments

#buildinginpublic #blockchain #bugfix

## [3.1.2] - 2025-10-15

### Fixed
- **Critical dataclass field order fix** in Block class to resolve Python dataclass validation error
- **Cache service stability** - fixed service crashes due to field ordering issue
- **API availability** - resolved 502 errors caused by dataclass initialization failures

### Technical Details
- Moved `offchain_cid` field after `block_hash` in Block dataclass
- Fields with default values must come after fields without defaults in Python dataclasses
- This fix enables proper service startup and cache generation

#buildinginpublic #blockchain #bugfix

## [3.1.1] - 2025-10-15

### Added
- **Real NP-complete proof data exposure** in API responses
- **Automatic IPFS upload** of full proof bundles when blocks are created
- **`proof_summary` field** in block data with problem instances and solutions
- **`offchain_cid` field** in Block class for IPFS proof bundle storage
- **Proof bundler utility** (`src/api/proof_bundler.py`) for serializing complete proof data
- **Comprehensive proof data** including problem instances, solutions, computational metrics, and energy measurements

### Changed
- **API responses now include actual problem instances, solutions, and computational metrics**
- **Cache format updated** to include proof summary data with NP problem solving details
- **Block creation in ConsensusEngine** now uploads proof bundles to IPFS automatically
- **`/v1/data/block/latest` endpoint** returns real subset sum problems and solutions
- **Genesis block generation** now includes full proof data and IPFS upload

### Fixed
- **Genesis block now properly generates and stores proof data**
- **IPFS integration in StorageManager** properly utilized for proof storage
- **Block serialization** now includes offchain_cid field
- **Dataclass field order** in Block class to fix Python dataclass validation

### Documentation
- **API responses now demonstrate real NP-complete problem solving**
- **Full proof bundles accessible** via existing `/v1/data/ipfs/<cid>` endpoint
- **Real computational complexity metrics** exposed in API responses

#buildinginpublic #blockchain #NP-complete

## [3.1.0] - 2025-10-15

### Added
- **Faucet API Module** (`src/api/`) - Live blockchain data streaming API
  - Flask-based REST API server (`faucet_server.py`)
  - File-based cache manager (`cache_manager.py`) 
  - Background cache updater with IPFS integration (`update_cache.py`)
  - REST endpoints: `/v1/data/block/latest`, `/v1/data/block/{index}`, `/v1/data/blocks`
  - Health check endpoint (`/health`)
  - Rate limiting (100 requests/minute per IP)
  - CORS enabled for browser access
  - IPFS connectivity verification and CID validation
  - Real-time cache updates every 30 seconds
  - Comprehensive error handling with standard HTTP codes

### Changed
- Updated `requirements.txt` with Flask dependencies (Flask, Flask-CORS, Flask-Limiter)
- Added cache directory to `.gitignore` for data/cache/ files
- API uses capacity terminology throughout

### Fixed
- Import path issues in API modules
- IPFS health check method compatibility
- Flask-Limiter dependency installation
- All API components tested and verified working

### Documentation
- Complete API documentation in `FAUCET_API.README.md`
- Deployment files: `Procfile`, `runtime.txt`, `.env.example`
- Comprehensive deployment guide for DigitalOcean (`DEPLOYMENT.md`)
- All API endpoints include comprehensive docstrings
- Test suites for all API components

### Deployment
- Ready for DigitalOcean deployment (164.92.89.62)
- Production-ready with nginx reverse proxy configuration
- Systemd service files for auto-restart
- #buildinginpublic launch ready
- All endpoints tested and verified: health, latest block, specific block, block range
- Rate limiting tested and functional

## [3.0.4] - 2025-10-15

### Added
- **Network Module** (`src/network.py`) - Implements `docs/blockchain/network.md` specification
  - NetworkProtocol class for blockchain networking
  - Message schemas (HeaderMsg, RevealMsg, RequestMsg, ResponseMsg)
  - Gossipsub topics for headers, commit-reveal, requests, and responses
  - RPC handlers (get_headers, get_block_by_hash, get_proof_by_cid)
  - Message encoding/compression with zstd/snappy support
  - Rate limiting and message validation
  - Message deduplication by header_hash/commitment
  - Integration with Consensus, Storage, and POW modules

### Changed
- Network module uses capacity terminology throughout
- Message compression threshold set to 1KB
- Rate limiting set to 100 messages per second per peer

### Fixed
- Import errors for dataclasses field and typing imports
- Message serialization/deserialization
- RPC request/response handling

### Documentation
- Complete docstrings referencing network.md specification
- Inline comments for message handling and compression
- Test suite demonstrates network functionality

## [3.0.3] - 2025-10-15

### Added
- **Consensus Module** (`src/consensus.py`) - Implements `docs/blockchain/consensus.md` specification
  - ConsensusEngine class for blockchain consensus
  - Header validation pipeline (basic validation, commitment presence, difficulty check)
  - Reveal validation (commitment verification, solution verification)
  - Fork choice algorithm (cumulative work with tie-breaking)
  - Block tree management with BlockNode data structure
  - Genesis block generation (deterministic)
  - Chain reorganization handling with bounded depth
  - Finality tracking (k-deep confirmation)
  - Rate limiting for DOS protection

### Changed
- Consensus module uses capacity terminology throughout
- Integrates with POW and Storage modules seamlessly
- Includes comprehensive test suite

### Fixed
- Genesis block generation with proper EnergyMetrics
- Block tree cumulative work calculation

### Documentation
- Complete docstrings referencing consensus.md specification
- Inline comments for complex fork choice logic
- Test suite demonstrates consensus functionality

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
