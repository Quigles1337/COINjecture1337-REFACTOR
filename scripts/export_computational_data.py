#!/usr/bin/env python3
"""
COINjecture Computational Data Exporter for Kaggle

Exports all computational data from the blockchain including:
- IPFS CID data (problem/solution data)
- Computational complexity metrics
- Gas calculation data
- Mining work scores
- Block metadata

This creates a comprehensive dataset for researchers studying:
- Computational complexity in blockchain systems
- Dynamic gas calculation algorithms
- IPFS-based data storage patterns
- Mining efficiency metrics
"""

import sqlite3
import json
import pandas as pd
import os
import sys
from datetime import datetime
from pathlib import Path
import hashlib
import numpy as np

class ComputationalDataExporter:
    def __init__(self, db_path="blockchain.db"):
        self.db_path = db_path
        self.output_dir = Path("kaggle_data")
        self.output_dir.mkdir(exist_ok=True)
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def extract_computational_data(self):
        """Extract all computational data from blockchain"""
        self.log("🔍 Extracting computational data from blockchain...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all blocks with their data
        cursor.execute("""
            SELECT height, block_bytes, timestamp, gas_used, work_score
            FROM blocks 
            ORDER BY height
        """)
        
        blocks = cursor.fetchall()
        conn.close()
        
        self.log(f"📊 Found {len(blocks)} blocks to process")
        
        computational_data = []
        gas_data = []
        complexity_data = []
        mining_data = []
        
        for block in blocks:
            height, block_bytes, timestamp, gas_used, work_score = block
            
            try:
                # Parse block data
                block_data = json.loads(block_bytes.decode('utf-8'))
                
                # Extract computational data
                cid = block_data.get('cid', '')
                problem_data = block_data.get('problem_data', {})
                solution_data = block_data.get('solution_data', {})
                
                # Generate computational complexity metrics (same as in gas calculation)
                if cid and problem_data and solution_data:
                    complexity_metrics = self.calculate_complexity_metrics(problem_data, solution_data)
                    
                    # Computational data entry
                    computational_data.append({
                        'block_height': height,
                        'timestamp': timestamp,
                        'cid': cid,
                        'problem_size': problem_data.get('size', 0),
                        'problem_difficulty': problem_data.get('difficulty', 0.0),
                        'problem_type': problem_data.get('type', ''),
                        'problem_constraints': problem_data.get('constraints', 0),
                        'solve_time': solution_data.get('solve_time', 0.0),
                        'verify_time': solution_data.get('verify_time', 0.0),
                        'memory_used': solution_data.get('memory_used', 0),
                        'energy_used': solution_data.get('energy_used', 0.0),
                        'solution_quality': solution_data.get('quality', 0.0),
                        'algorithm': solution_data.get('algorithm', ''),
                        'time_asymmetry': complexity_metrics.get('time_asymmetry', 0.0),
                        'space_asymmetry': complexity_metrics.get('space_asymmetry', 0.0),
                        'problem_weight': complexity_metrics.get('problem_weight', 0.0),
                        'complexity_multiplier': complexity_metrics.get('complexity_multiplier', 0.0)
                    })
                    
                    # Gas calculation data
                    gas_data.append({
                        'block_height': height,
                        'timestamp': timestamp,
                        'cid': cid,
                        'gas_used': gas_used,
                        'base_gas': 1000,  # Base mining gas
                        'complexity_multiplier': complexity_metrics.get('complexity_multiplier', 0.0),
                        'calculated_gas': 1000 * (1 + complexity_metrics.get('complexity_multiplier', 0.0)),
                        'gas_efficiency': gas_used / (1000 * (1 + complexity_metrics.get('complexity_multiplier', 0.0))) if complexity_metrics.get('complexity_multiplier', 0.0) > 0 else 1.0
                    })
                    
                    # Complexity analysis data
                    complexity_data.append({
                        'block_height': height,
                        'timestamp': timestamp,
                        'cid': cid,
                        'problem_size': problem_data.get('size', 0),
                        'problem_difficulty': problem_data.get('difficulty', 0.0),
                        'solve_time': solution_data.get('solve_time', 0.0),
                        'memory_used': solution_data.get('memory_used', 0),
                        'time_asymmetry': complexity_metrics.get('time_asymmetry', 0.0),
                        'space_asymmetry': complexity_metrics.get('space_asymmetry', 0.0),
                        'problem_weight': complexity_metrics.get('problem_weight', 0.0),
                        'complexity_score': complexity_metrics.get('time_asymmetry', 0.0) * 
                                          np.sqrt(complexity_metrics.get('space_asymmetry', 0.0)) * 
                                          complexity_metrics.get('problem_weight', 0.0)
                    })
                
                # Mining data
                mining_data.append({
                    'block_height': height,
                    'timestamp': timestamp,
                    'cid': cid,
                    'work_score': work_score,
                    'gas_used': gas_used,
                    'miner_address': block_data.get('miner_address', ''),
                    'block_hash': block_data.get('hash', ''),
                    'previous_hash': block_data.get('previous_hash', ''),
                    'mining_efficiency': work_score / gas_used if gas_used > 0 else 0.0
                })
                
            except Exception as e:
                self.log(f"⚠️  Error processing block {height}: {e}")
                continue
        
        self.log(f"✅ Extracted {len(computational_data)} computational records")
        return computational_data, gas_data, complexity_data, mining_data
    
    def calculate_complexity_metrics(self, problem_data, solution_data):
        """Calculate complexity metrics (same as in gas calculation)"""
        try:
            # Time asymmetry: ratio of solve time to verify time
            solve_time = solution_data.get('solve_time', 1.0)
            verify_time = solution_data.get('verify_time', 0.1)
            time_asymmetry = solve_time / max(verify_time, 0.01)
            
            # Space asymmetry: memory usage relative to problem size
            problem_size = problem_data.get('size', 10)
            memory_used = solution_data.get('memory_used', 100)
            space_asymmetry = memory_used / max(problem_size, 1)
            
            # Problem weight: difficulty and constraints
            difficulty = problem_data.get('difficulty', 1.0)
            constraints = problem_data.get('constraints', 1)
            problem_weight = difficulty * (1 + constraints * 0.1)
            
            # Complexity multiplier
            complexity_multiplier = time_asymmetry * np.sqrt(space_asymmetry) * problem_weight
            
            return {
                'time_asymmetry': time_asymmetry,
                'space_asymmetry': space_asymmetry,
                'problem_weight': problem_weight,
                'complexity_multiplier': complexity_multiplier
            }
        except Exception as e:
            self.log(f"⚠️  Error calculating complexity metrics: {e}")
            return {
                'time_asymmetry': 1.0,
                'space_asymmetry': 1.0,
                'problem_weight': 1.0,
                'complexity_multiplier': 1.0
            }
    
    def create_kaggle_datasets(self, computational_data, gas_data, complexity_data, mining_data):
        """Create Kaggle-ready datasets"""
        self.log("📊 Creating Kaggle datasets...")
        
        # 1. Main computational dataset
        df_computational = pd.DataFrame(computational_data)
        df_computational.to_csv(self.output_dir / "coinjecture_computational_data.csv", index=False)
        self.log(f"✅ Created computational dataset: {len(df_computational)} records")
        
        # 2. Gas calculation dataset
        df_gas = pd.DataFrame(gas_data)
        df_gas.to_csv(self.output_dir / "coinjecture_gas_calculation.csv", index=False)
        self.log(f"✅ Created gas calculation dataset: {len(df_gas)} records")
        
        # 3. Complexity analysis dataset
        df_complexity = pd.DataFrame(complexity_data)
        df_complexity.to_csv(self.output_dir / "coinjecture_complexity_analysis.csv", index=False)
        self.log(f"✅ Created complexity analysis dataset: {len(df_complexity)} records")
        
        # 4. Mining efficiency dataset
        df_mining = pd.DataFrame(mining_data)
        df_mining.to_csv(self.output_dir / "coinjecture_mining_efficiency.csv", index=False)
        self.log(f"✅ Created mining efficiency dataset: {len(df_mining)} records")
        
        # 5. Summary statistics
        self.create_summary_statistics(df_computational, df_gas, df_complexity, df_mining)
        
        return df_computational, df_gas, df_complexity, df_mining
    
    def create_summary_statistics(self, df_comp, df_gas, df_complexity, df_mining):
        """Create summary statistics for the datasets"""
        self.log("📈 Creating summary statistics...")
        
        summary = {
            'dataset_info': {
                'total_blocks': len(df_comp),
                'date_range': {
                    'start': df_comp['timestamp'].min() if len(df_comp) > 0 else 'N/A',
                    'end': df_comp['timestamp'].max() if len(df_comp) > 0 else 'N/A'
                },
                'unique_cids': df_comp['cid'].nunique() if len(df_comp) > 0 else 0,
                'unique_problem_types': df_comp['problem_type'].nunique() if len(df_comp) > 0 else 0
            },
            'computational_metrics': {
                'avg_problem_size': df_comp['problem_size'].mean() if len(df_comp) > 0 else 0,
                'avg_difficulty': df_comp['problem_difficulty'].mean() if len(df_comp) > 0 else 0,
                'avg_solve_time': df_comp['solve_time'].mean() if len(df_comp) > 0 else 0,
                'avg_memory_used': df_comp['memory_used'].mean() if len(df_comp) > 0 else 0,
                'avg_complexity_multiplier': df_comp['complexity_multiplier'].mean() if len(df_comp) > 0 else 0
            },
            'gas_metrics': {
                'avg_gas_used': df_gas['gas_used'].mean() if len(df_gas) > 0 else 0,
                'min_gas_used': df_gas['gas_used'].min() if len(df_gas) > 0 else 0,
                'max_gas_used': df_gas['gas_used'].max() if len(df_gas) > 0 else 0,
                'avg_gas_efficiency': df_gas['gas_efficiency'].mean() if len(df_gas) > 0 else 0
            },
            'mining_metrics': {
                'avg_work_score': df_mining['work_score'].mean() if len(df_mining) > 0 else 0,
                'avg_mining_efficiency': df_mining['mining_efficiency'].mean() if len(df_mining) > 0 else 0,
                'total_work_score': df_mining['work_score'].sum() if len(df_mining) > 0 else 0
            }
        }
        
        # Save summary
        with open(self.output_dir / "dataset_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Create README for Kaggle
        self.create_kaggle_readme(summary)
        
        self.log("✅ Created summary statistics and documentation")
    
    def create_kaggle_readme(self, summary):
        """Create README for Kaggle dataset"""
        readme_content = f"""# COINjecture Computational Data Dataset

## Overview
This dataset contains computational data from the COINjecture blockchain, featuring dynamic gas calculation based on IPFS-stored computational complexity data.

## Dataset Information
- **Total Blocks**: {summary['dataset_info']['total_blocks']}
- **Date Range**: {summary['dataset_info']['date_range']['start']} to {summary['dataset_info']['date_range']['end']}
- **Unique CIDs**: {summary['dataset_info']['unique_cids']}
- **Problem Types**: {summary['dataset_info']['unique_problem_types']}

## Files Description

### 1. coinjecture_computational_data.csv
Main dataset containing computational problem and solution data:
- `block_height`: Blockchain block number
- `timestamp`: Block creation timestamp
- `cid`: IPFS Content Identifier
- `problem_size`: Size of the computational problem
- `problem_difficulty`: Difficulty level (1.0-3.0)
- `problem_type`: Type of problem (subset_sum, knapsack, etc.)
- `solve_time`: Time to solve the problem
- `verify_time`: Time to verify the solution
- `memory_used`: Memory consumption during solving
- `energy_used`: Energy consumption estimate
- `solution_quality`: Quality of the solution (0.7-1.0)
- `algorithm`: Algorithm used for solving
- `time_asymmetry`: Ratio of solve time to verify time
- `space_asymmetry`: Memory usage relative to problem size
- `problem_weight`: Difficulty and constraints weight
- `complexity_multiplier`: Overall complexity multiplier

### 2. coinjecture_gas_calculation.csv
Gas calculation data showing dynamic gas costs:
- `block_height`: Blockchain block number
- `timestamp`: Block creation timestamp
- `cid`: IPFS Content Identifier
- `gas_used`: Actual gas used in the block
- `base_gas`: Base gas cost (1000)
- `complexity_multiplier`: Complexity-based multiplier
- `calculated_gas`: Calculated gas based on complexity
- `gas_efficiency`: Ratio of actual to calculated gas

### 3. coinjecture_complexity_analysis.csv
Computational complexity analysis:
- `block_height`: Blockchain block number
- `timestamp`: Block creation timestamp
- `cid`: IPFS Content Identifier
- `problem_size`: Size of the computational problem
- `problem_difficulty`: Difficulty level
- `solve_time`: Time to solve
- `memory_used`: Memory consumption
- `time_asymmetry`: Time complexity metric
- `space_asymmetry`: Space complexity metric
- `problem_weight`: Problem weight factor
- `complexity_score`: Overall complexity score

### 4. coinjecture_mining_efficiency.csv
Mining efficiency and work score data:
- `block_height`: Blockchain block number
- `timestamp`: Block creation timestamp
- `cid`: IPFS Content Identifier
- `work_score`: Mining work score
- `gas_used`: Gas consumed
- `miner_address`: Address of the miner
- `block_hash`: Block hash
- `previous_hash`: Previous block hash
- `mining_efficiency`: Work score per gas unit

## Key Metrics
- **Average Problem Size**: {summary['computational_metrics']['avg_problem_size']:.2f}
- **Average Difficulty**: {summary['computational_metrics']['avg_difficulty']:.2f}
- **Average Solve Time**: {summary['computational_metrics']['avg_solve_time']:.2f}s
- **Average Memory Used**: {summary['computational_metrics']['avg_memory_used']:.2f} MB
- **Average Gas Used**: {summary['gas_metrics']['avg_gas_used']:.2f}
- **Gas Range**: {summary['gas_metrics']['min_gas_used']:.2f} - {summary['gas_metrics']['max_gas_used']:.2f}
- **Average Work Score**: {summary['mining_metrics']['avg_work_score']:.2f}

## Research Applications
This dataset is valuable for studying:
- Computational complexity in blockchain systems
- Dynamic gas calculation algorithms
- IPFS-based data storage patterns
- Mining efficiency optimization
- Problem-solving algorithm performance
- Energy consumption in computational work

## Data Collection Method
Data is extracted from the COINjecture blockchain database, which stores:
- IPFS CIDs linking to computational problem/solution data
- Dynamic gas calculation based on computational complexity
- Real-time mining metrics and work scores
- Block metadata and timestamps

## Version
Dataset Version: 1.0
Export Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
COINjecture Version: 3.13.14

## License
This dataset is provided for research purposes under the COINjecture project license.

## Contact
For questions about this dataset, please refer to the COINjecture project documentation.
"""
        
        with open(self.output_dir / "README.md", 'w') as f:
            f.write(readme_content)
        
        self.log("✅ Created Kaggle README")
    
    def export_to_kaggle(self):
        """Main export function"""
        self.log("🚀 Starting COINjecture computational data export to Kaggle...")
        
        try:
            # Extract data
            computational_data, gas_data, complexity_data, mining_data = self.extract_computational_data()
            
            # Create datasets
            df_comp, df_gas, df_complexity, df_mining = self.create_kaggle_datasets(
                computational_data, gas_data, complexity_data, mining_data
            )
            
            # Create archive
            self.create_archive()
            
            self.log("🎉 Export completed successfully!")
            self.log(f"📁 Output directory: {self.output_dir.absolute()}")
            self.log(f"📊 Total records exported: {len(computational_data)}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Export failed: {e}")
            return False
    
    def create_archive(self):
        """Create compressed archive for easy upload"""
        import zipfile
        
        archive_path = self.output_dir.parent / "coinjecture_computational_data.zip"
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.output_dir.rglob('*'):
                if file_path.is_file():
                    zipf.write(file_path, file_path.relative_to(self.output_dir.parent))
        
        self.log(f"📦 Created archive: {archive_path.absolute()}")

def main():
    """Main function"""
    print("🚀 COINjecture Computational Data Exporter for Kaggle")
    print("=" * 60)
    
    # Check if database exists
    db_path = "blockchain.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Please run this script from the COINjecture project directory")
        sys.exit(1)
    
    # Create exporter
    exporter = ComputationalDataExporter(db_path)
    
    # Export data
    success = exporter.export_to_kaggle()
    
    if success:
        print("\n✅ Export completed successfully!")
        print("📁 Check the 'kaggle_data' directory for exported files")
        print("📦 Use 'coinjecture_computational_data.zip' for easy upload to Kaggle")
    else:
        print("\n❌ Export failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
