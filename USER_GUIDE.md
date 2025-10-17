# COINjecture User Guide
## Simple Steps for Everyone

Welcome to COINjecture! This guide will help you use our blockchain system step by step, even if you've never used blockchain technology before.

---

## 🚀 Getting Started (First Time Setup)

### Step 1: Set Up Your Computer
**What you need:** A computer with internet connection

**What to do:**
1. Open your computer's terminal/command prompt
2. Navigate to the COINjecture folder
3. Type this command and press Enter:
   ```
   python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['--help'])"
   ```

**What you should see:** A list of available commands

---

## 🏗️ Setting Up Your Node (Choose Your Role)

### Option A: I Want to Mine (Earn Rewards)
**When to choose:** You want to solve problems and earn rewards

**Step 1:** Initialize your mining node
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['init', '--role', 'miner', '--data-dir', './my_miner', '--config', 'miner_config.json'])"
```

**What happens:** Creates a mining setup for you

**Step 2:** Start mining
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['mine', '--config', 'miner_config.json', '--problem-type', 'subset_sum', '--tier', 'desktop'])"
```

**What happens:** Your computer starts solving problems and earning rewards

---

### Option B: I Want to Run a Full Node (Help the Network)
**When to choose:** You want to help keep the network running

**Step 1:** Initialize your full node
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['init', '--role', 'full', '--data-dir', './my_full_node', '--config', 'full_config.json'])"
```

**What happens:** Creates a full node setup

**Step 2:** Start your node
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['run', '--config', 'full_config.json'])"
```

**What happens:** Your node starts helping the network

---

### Option C: I Want a Light Node (Just Check Things)
**When to choose:** You just want to check blockchain data without heavy processing

**Step 1:** Initialize your light node
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['init', '--role', 'light', '--data-dir', './my_light_node', '--config', 'light_config.json'])"
```

**What happens:** Creates a lightweight setup

---

## 💰 Submitting Problems (Earn by Getting Problems Solved)

### Step 1: Submit a Problem You Need Solved
**When to use:** You have a computational problem and want to pay someone to solve it

**Command to use:**
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['submit-problem', '--type', 'subset_sum', '--template', '{\"numbers\": [1, 2, 3, 4, 5], \"target\": 7}', '--bounty', '100', '--strategy', 'BEST'])"
```

**What this means:**
- `--type subset_sum`: You're submitting a "subset sum" problem (finding numbers that add up to a target)
- `--template`: Your specific problem (numbers [1,2,3,4,5] need to add up to 7)
- `--bounty 100`: You're offering 100 tokens to whoever solves it
- `--strategy BEST`: You want the best solution found

**What happens:** Your problem gets added to the network for miners to solve

### Step 2: Check if Your Problem Was Solved
**Command to use:**
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['check-submission', '--id', 'submission-123'])"
```

**Replace `submission-123`** with the ID you got when you submitted your problem

**What you'll see:** Status of your problem (pending, solved, etc.)

### Step 3: See All Your Submitted Problems
**Command to use:**
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['list-submissions'])"
```

**What you'll see:** A list of all problems you've submitted

---

## 🔍 Checking the Blockchain

### Step 1: See the Latest Block
**When to use:** You want to see the most recent activity on the blockchain

**Command to use:**
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['get-block', '--latest', '--format', 'pretty'])"
```

**What you'll see:** Information about the newest block (like a page in a ledger)

### Step 2: Look Up a Specific Block
**When to use:** You know a specific block number and want to see its details

**Command to use:**
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['get-block', '--index', '1', '--format', 'pretty'])"
```

**Replace `1`** with the block number you want to see

### Step 3: Get Detailed Proof Data
**When to use:** You want to see the actual problem-solving work that was done

**Command to use:**
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['get-proof', '--cid', 'QmXyZ123', '--format', 'json'])"
```

**Replace `QmXyZ123`** with the proof ID you want to see

---

## 🌐 Network Management

### Step 1: Add a Friend's Node
**When to use:** You want to connect to a friend's COINjecture node

**Command to use:**
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['add-peer', '--multiaddr', '/ip4/127.0.0.1/tcp/8080'])"
```

**Replace the address** with your friend's node address

### Step 2: See Who You're Connected To
**Command to use:**
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['peers', '--format', 'table'])"
```

**What you'll see:** A table of all the nodes you're connected to

---

## 🆘 Getting Help

### If You Get Stuck
**Command to use:**
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['--help'])"
```

**What you'll see:** A complete list of all available commands

### If You Want Help with a Specific Command
**Command to use:**
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['submit-problem', '--help'])"
```

**Replace `submit-problem`** with any command you need help with

---

## 📋 Quick Reference: Common Tasks

### "I want to start mining"
1. Initialize: `init --role miner`
2. Start mining: `mine --config miner_config.json`

### "I want to submit a problem"
1. Submit: `submit-problem --type subset_sum --template '{"numbers": [1,2,3], "target": 3}' --bounty 50`
2. Check status: `check-submission --id [your-id]`

### "I want to see what's happening"
1. Latest block: `get-block --latest`
2. All submissions: `list-submissions`

### "I want to connect to friends"
1. Add peer: `add-peer --multiaddr [friend's-address]`
2. See connections: `peers`

---

## 🎯 Understanding the Output

### When You See "✅ Success"
**What it means:** Your command worked perfectly

### When You See "❌ Error"
**What it means:** Something went wrong, but the error message will tell you what

### When You See Numbers and Letters (like "QmXyZ123")
**What it means:** These are IDs or addresses - like a unique name for something

### When You See JSON (lots of { and })
**What it means:** This is structured data - like a form with lots of information

---

## 🔄 Daily Workflow Examples

### Example 1: The Problem Solver
**Morning:** Check for new problems to solve
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['list-submissions'])"
```

**During the day:** Mine and solve problems
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['mine', '--config', 'miner_config.json'])"
```

**Evening:** Check your earnings
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['get-block', '--latest'])"
```

### Example 2: The Problem Submitter
**When you have a problem:** Submit it with a bounty
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['submit-problem', '--type', 'subset_sum', '--template', '{\"numbers\": [10, 20, 30], \"target\": 40}', '--bounty', '200'])"
```

**Check progress:** See if it's been solved
```
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['check-submission', '--id', 'submission-123'])"
```

---

## 🎉 You're Ready!

You now have everything you need to use COINjecture. Start with the "Getting Started" section and work your way through the tasks that interest you.

Remember: If you get stuck, use the help commands or ask for assistance. The COINjecture community is here to help!

---

*This guide is designed to be simple and clear. Each command is ready to copy and paste into your terminal.*
