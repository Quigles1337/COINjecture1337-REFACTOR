#!/bin/bash

# COINjecture Kaggle Export Setup Script
# Sets up automatic export of computational data to Kaggle

set -e

echo "🚀 COINjecture Kaggle Export Setup"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "blockchain.db" ]; then
    echo "❌ blockchain.db not found. Please run this script from the COINjecture project directory."
    exit 1
fi

echo "📦 Installing required Python packages..."

# Install required packages
pip install pandas numpy schedule kaggle

echo "✅ Python packages installed"

# Create kaggle data directory
mkdir -p kaggle_data

# Make scripts executable
chmod +x scripts/export_computational_data.py
chmod +x scripts/kaggle_auto_updater.py

echo "✅ Scripts made executable"

# Create initial export
echo "📊 Creating initial export..."
python3 scripts/export_computational_data.py

if [ $? -eq 0 ]; then
    echo "✅ Initial export completed"
    echo "📁 Data exported to: kaggle_data/"
    echo "📦 Archive created: coinjecture_computational_data.zip"
else
    echo "❌ Initial export failed"
    exit 1
fi

# Create systemd service for auto-updater (Linux)
if command -v systemctl &> /dev/null; then
    echo "🔧 Creating systemd service for auto-updater..."
    
    cat > /tmp/coinjecture-kaggle-updater.service << EOF
[Unit]
Description=COINjecture Kaggle Auto-Updater
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(which python3) scripts/kaggle_auto_updater.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

    sudo mv /tmp/coinjecture-kaggle-updater.service /etc/systemd/system/
    sudo systemctl daemon-reload
    
    echo "✅ Systemd service created"
    echo "📝 To start the service: sudo systemctl start coinjecture-kaggle-updater"
    echo "📝 To enable auto-start: sudo systemctl enable coinjecture-kaggle-updater"
fi

# Create cron job for auto-updater (alternative)
echo "⏰ Setting up cron job for auto-updater..."
(crontab -l 2>/dev/null; echo "0 */6 * * * cd $(pwd) && python3 scripts/kaggle_auto_updater.py --once >> kaggle_updater.log 2>&1") | crontab -

echo "✅ Cron job created (runs every 6 hours)"

# Create configuration file
echo "⚙️  Creating configuration file..."
cat > kaggle_config.json << EOF
{
  "update_interval_minutes": 360,
  "database_path": "blockchain.db",
  "output_directory": "kaggle_data",
  "kaggle_username": "",
  "kaggle_dataset": "coinjecture-computational-data",
  "max_blocks_per_update": 1000,
  "enable_auto_upload": false
}
EOF

echo "✅ Configuration file created: kaggle_config.json"
echo "📝 Edit kaggle_config.json to configure your settings"

# Create README for the export system
cat > KAGGLE_EXPORT_README.md << EOF
# COINjecture Kaggle Export System

## Overview
This system automatically exports computational data from the COINjecture blockchain to Kaggle datasets for research purposes.

## Files Created
- \`kaggle_data/\` - Directory containing exported datasets
- \`coinjecture_computational_data.zip\` - Compressed archive for easy upload
- \`kaggle_config.json\` - Configuration file
- \`kaggle_updater.log\` - Log file for the auto-updater

## Datasets Exported

### 1. coinjecture_computational_data.csv
Main dataset with computational problem and solution data:
- Block metadata (height, timestamp, CID)
- Problem data (size, difficulty, type, constraints)
- Solution data (solve time, verify time, memory, energy, quality, algorithm)
- Complexity metrics (time asymmetry, space asymmetry, problem weight, complexity multiplier)

### 2. coinjecture_gas_calculation.csv
Gas calculation data showing dynamic gas costs:
- Gas usage per block
- Complexity-based gas calculation
- Gas efficiency metrics

### 3. coinjecture_complexity_analysis.csv
Computational complexity analysis:
- Problem complexity scores
- Time and space complexity metrics
- Complexity correlation data

### 4. coinjecture_mining_efficiency.csv
Mining efficiency and work score data:
- Work scores per block
- Mining efficiency metrics
- Miner performance data

## Usage

### Manual Export
\`\`\`bash
python3 scripts/export_computational_data.py
\`\`\`

### Auto-Updater (Run Once)
\`\`\`bash
python3 scripts/kaggle_auto_updater.py --once
\`\`\`

### Auto-Updater (Continuous)
\`\`\`bash
python3 scripts/kaggle_auto_updater.py
\`\`\`

### Systemd Service (Linux)
\`\`\`bash
sudo systemctl start coinjecture-kaggle-updater
sudo systemctl enable coinjecture-kaggle-updater
\`\`\`

## Configuration
Edit \`kaggle_config.json\` to configure:
- Update interval (default: 6 hours)
- Database path
- Output directory
- Kaggle credentials (for auto-upload)
- Maximum blocks per update

## Kaggle Upload
To enable automatic upload to Kaggle:
1. Install Kaggle API: \`pip install kaggle\`
2. Set up Kaggle credentials: \`kaggle datasets create\`
3. Edit \`kaggle_config.json\`:
   - Set \`kaggle_username\` to your Kaggle username
   - Set \`kaggle_dataset\` to your dataset name
   - Set \`enable_auto_upload\` to \`true\`

## Research Applications
This dataset is valuable for studying:
- Computational complexity in blockchain systems
- Dynamic gas calculation algorithms
- IPFS-based data storage patterns
- Mining efficiency optimization
- Problem-solving algorithm performance
- Energy consumption in computational work

## Data Privacy
All data is extracted from the public blockchain and contains no private information.
IPFS CIDs are public identifiers and computational data is anonymized.

## Version
Export System Version: 1.0
COINjecture Version: 3.13.14
Last Updated: $(date)
EOF

echo "✅ README created: KAGGLE_EXPORT_README.md"

echo ""
echo "🎉 Kaggle export system setup completed!"
echo ""
echo "📊 Next steps:"
echo "1. Check the exported data in kaggle_data/"
echo "2. Upload coinjecture_computational_data.zip to Kaggle"
echo "3. Configure kaggle_config.json for your needs"
echo "4. Start the auto-updater if desired"
echo ""
echo "📝 For more information, see KAGGLE_EXPORT_README.md"
echo ""
echo "🚀 Ready to export computational data to Kaggle!"
