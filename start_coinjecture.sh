#!/bin/bash
echo "🚀 Starting COINjecture..."
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['interactive'])"
