COINjecture devnet script spec (language-agnostic)

Purpose
- Launch a small local network (3–5 nodes) with mixed roles for testing

Topology (example)
- node1: full + miner, ports 4001 (p2p), 5001 (ipfs api)
- node2: full, ports 4002
- node3: light, ports 4003
- node4: archive, ports 4004

Operations
- start: spawn processes, create temp data dirs, write configs
- connect: add bootstrap peers
- mine: enable mining on one or more nodes
- teardown: stop processes and clean data dirs

Usage
- python scripts/devnet.py up --nodes 4
- python scripts/devnet.py down


