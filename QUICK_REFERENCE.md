# COINjecture Quick Reference
## Copy & Paste Commands

---

## 🚀 First Time Setup

### Check if everything works
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['--help'])"
```

---

## 🏗️ Node Setup (Choose One)

### Option 1: Mining Node (Earn Rewards)
```bash
# Initialize
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['init', '--role', 'miner', '--data-dir', './my_miner', '--config', 'miner_config.json'])"

# Start mining
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['mine', '--config', 'miner_config.json', '--problem-type', 'subset_sum', '--tier', 'desktop'])"
```

### Option 2: Full Node (Help Network)
```bash
# Initialize
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['init', '--role', 'full', '--data-dir', './my_full_node', '--config', 'full_config.json'])"

# Start node
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['run', '--config', 'full_config.json'])"
```

### Option 3: Light Node (Just Check Things)
```bash
# Initialize
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['init', '--role', 'light', '--data-dir', './my_light_node', '--config', 'light_config.json'])"
```

---

## 💰 Submit Problems (Pay Others to Solve)

### Submit a Problem
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['submit-problem', '--type', 'subset_sum', '--template', '{\"numbers\": [1, 2, 3, 4, 5], \"target\": 7}', '--bounty', '100', '--strategy', 'BEST'])"
```

### Check Your Submission Status
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['check-submission', '--id', 'submission-123'])"
```

### List All Your Submissions
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['list-submissions'])"
```

---

## 🔍 Check Blockchain

### See Latest Block
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['get-block', '--latest', '--format', 'pretty'])"
```

### Look Up Specific Block
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['get-block', '--index', '1', '--format', 'pretty'])"
```

### Get Proof Details
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['get-proof', '--cid', 'QmXyZ123', '--format', 'json'])"
```

---

## 🌐 Network Management

### Add a Friend's Node
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['add-peer', '--multiaddr', '/ip4/127.0.0.1/tcp/8080'])"
```

### See Connected Peers
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['peers', '--format', 'table'])"
```

---

## 🆘 Get Help

### General Help
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['--help'])"
```

### Help for Specific Command
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['submit-problem', '--help'])"
```

---

## 🎯 Common Workflows

### Daily Mining Routine
```bash
# Check for problems
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['list-submissions'])"

# Start mining
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['mine', '--config', 'miner_config.json'])"

# Check latest activity
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['get-block', '--latest'])"
```

### Problem Submission Workflow
```bash
# Submit problem
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['submit-problem', '--type', 'subset_sum', '--template', '{\"numbers\": [10, 20, 30], \"target\": 40}', '--bounty', '200'])"

# Check status (replace with your submission ID)
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['check-submission', '--id', 'submission-123'])"
```

---

## 📝 Customize Your Commands

### Change Problem Template
Replace `{\"numbers\": [1, 2, 3, 4, 5], \"target\": 7}` with your own numbers and target

### Change Bounty Amount
Replace `--bounty 100` with your desired amount (e.g., `--bounty 500`)

### Change Strategy
Replace `--strategy BEST` with:
- `--strategy ANY` (first solution wins)
- `--strategy MULTIPLE` (collect multiple solutions)
- `--strategy STATISTICAL` (collect for analysis)

### Change Mining Tier
Replace `--tier desktop` with:
- `--tier mobile` (for phones/tablets)
- `--tier server` (for powerful computers)
- `--tier gpu` (for graphics cards)

---

## 🔧 Troubleshooting

### If Command Doesn't Work
1. Make sure you're in the COINjecture folder
2. Try the help command first
3. Check if you have Python 3 installed

### If You Get Permission Errors
Make sure you have write permissions in the folder

### If You Get Import Errors
Make sure all files are in the right place and you're running from the correct directory

---

*All commands are ready to copy and paste. Just replace the placeholder values with your own data.*
