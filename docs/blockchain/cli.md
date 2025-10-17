COINjecture CLI spec (language-agnostic)

Responsibilities
- Provide user-facing commands to run nodes and interact with the chain

Commands
- coinjectured init --role [light|full|miner|archive] --data-dir DIR
- coinjectured run --config PATH
- coinjectured mine --config PATH --problem-type subset_sum --tier desktop
- coinjectured get-block --hash HEX
- coinjectured get-proof --cid CID
- coinjectured add-peer --multiaddr ADDR
- coinjectured peers

Exit codes and errors
- Non-zero on network/storage failures; structured stderr

Cross-language notes
- Keep flags and subcommands identical across implementations for portability


