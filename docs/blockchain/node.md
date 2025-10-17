COINjecture node module spec (language-agnostic)

Responsibilities
- Node configuration, role selection, lifecycle management
- Compose services: networking, consensus, storage, pow engine (for miners)

Roles and capabilities
- light: subscribe headers; validate commitments; request bundles on demand
- full: validate headers + reveals; selective bundle fetch; participate in fork choice
- miner: run commit–reveal loop; publish headers and reveals
- archive: validate and pin all bundles; serve data to peers

Config keys (examples)
- network_id, listen_addr, bootstrap_peers[]
- role: light|full|miner|archive
- ipfs_api_url, pin_policy, pruning_mode
- target_block_interval_secs, difficulty_window
- log_level, metrics_port

Lifecycle
- init -> start storage -> start p2p -> sync headers -> participate per role

Cross-language notes
- Keep configuration in a simple format (TOML/YAML) and load into a strict struct


