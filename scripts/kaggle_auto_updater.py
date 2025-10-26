#!/usr/bin/env python3
"""
COINjecture Kaggle Auto-Updater

Automatically exports new computational data to Kaggle dataset
Runs periodically to keep the dataset updated with latest blockchain data
"""

import os
import sys
import time
import schedule
import subprocess
from datetime import datetime
from pathlib import Path
import json
import logging

class KaggleAutoUpdater:
    def __init__(self, config_file="kaggle_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        
    def load_config(self):
        """Load configuration from file"""
        default_config = {
            "update_interval_minutes": 60,  # Update every hour
            "database_path": "blockchain.db",
            "output_directory": "kaggle_data",
            "kaggle_username": "",
            "kaggle_dataset": "coinjecture-computational-data",
            "max_blocks_per_update": 1000,
            "enable_auto_upload": False
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                print(f"⚠️  Error loading config: {e}")
                return default_config
        else:
            # Create default config file
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"📝 Created default config file: {self.config_file}")
            return default_config
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('kaggle_updater.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log(self, message, level="INFO"):
        """Log message"""
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    def check_for_new_data(self):
        """Check if there's new data to export"""
        try:
            # Check if database exists and has new data
            if not os.path.exists(self.config["database_path"]):
                self.log("❌ Database not found", "ERROR")
                return False
            
            # Get last export timestamp
            last_export_file = Path(self.config["output_directory"]) / "last_export.json"
            if last_export_file.exists():
                with open(last_export_file, 'r') as f:
                    last_export = json.load(f)
                last_export_time = last_export.get('timestamp', 0)
            else:
                last_export_time = 0
            
            # Check database for new blocks
            import sqlite3
            conn = sqlite3.connect(self.config["database_path"])
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM blocks 
                WHERE timestamp > ?
            """, (last_export_time,))
            
            new_blocks = cursor.fetchone()[0]
            conn.close()
            
            if new_blocks > 0:
                self.log(f"📊 Found {new_blocks} new blocks to export")
                return True
            else:
                self.log("ℹ️  No new data to export")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking for new data: {e}", "ERROR")
            return False
    
    def export_new_data(self):
        """Export new computational data"""
        try:
            self.log("🚀 Starting incremental data export...")
            
            # Run the export script
            result = subprocess.run([
                sys.executable, 
                "scripts/export_computational_data.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ Data export completed successfully")
                
                # Update last export timestamp
                self.update_last_export_time()
                
                # Upload to Kaggle if enabled
                if self.config.get("enable_auto_upload", False):
                    self.upload_to_kaggle()
                
                return True
            else:
                self.log(f"❌ Export failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error during export: {e}", "ERROR")
            return False
    
    def update_last_export_time(self):
        """Update last export timestamp"""
        try:
            last_export_data = {
                'timestamp': time.time(),
                'date': datetime.now().isoformat(),
                'version': '3.13.14'
            }
            
            last_export_file = Path(self.config["output_directory"]) / "last_export.json"
            last_export_file.parent.mkdir(exist_ok=True)
            
            with open(last_export_file, 'w') as f:
                json.dump(last_export_data, f, indent=2)
            
            self.log("📝 Updated last export timestamp")
            
        except Exception as e:
            self.log(f"⚠️  Error updating timestamp: {e}", "WARNING")
    
    def upload_to_kaggle(self):
        """Upload dataset to Kaggle"""
        try:
            if not self.config.get("kaggle_username") or not self.config.get("kaggle_dataset"):
                self.log("⚠️  Kaggle credentials not configured", "WARNING")
                return False
            
            self.log("📤 Uploading to Kaggle...")
            
            # Create kaggle metadata
            self.create_kaggle_metadata()
            
            # Upload using kaggle API
            result = subprocess.run([
                "kaggle", "datasets", "create", "-p", self.config["output_directory"]
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ Successfully uploaded to Kaggle")
                return True
            else:
                self.log(f"❌ Kaggle upload failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error uploading to Kaggle: {e}", "ERROR")
            return False
    
    def create_kaggle_metadata(self):
        """Create Kaggle dataset metadata"""
        try:
            metadata = {
                "title": "COINjecture Computational Data",
                "id": f"{self.config['kaggle_username']}/{self.config['kaggle_dataset']}",
                "licenses": [{"name": "MIT"}],
                "keywords": [
                    "blockchain", "computational-complexity", "gas-calculation", 
                    "ipfs", "mining", "cryptocurrency", "proof-of-work"
                ],
                "collaborators": [],
                "data": []
            }
            
            # Add data files
            output_dir = Path(self.config["output_directory"])
            for file_path in output_dir.glob("*.csv"):
                metadata["data"].append({
                    "name": file_path.name,
                    "totalBytes": file_path.stat().st_size,
                    "columns": self.get_csv_columns(file_path)
                })
            
            # Save metadata
            with open(output_dir / "dataset-metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.log("📝 Created Kaggle metadata")
            
        except Exception as e:
            self.log(f"⚠️  Error creating metadata: {e}", "WARNING")
    
    def get_csv_columns(self, csv_file):
        """Get CSV column information"""
        try:
            import pandas as pd
            df = pd.read_csv(csv_file, nrows=0)  # Read just headers
            return list(df.columns)
        except Exception:
            return []
    
    def run_update_cycle(self):
        """Run one update cycle"""
        self.log("🔄 Starting update cycle...")
        
        try:
            if self.check_for_new_data():
                success = self.export_new_data()
                if success:
                    self.log("✅ Update cycle completed successfully")
                else:
                    self.log("❌ Update cycle failed", "ERROR")
            else:
                self.log("ℹ️  No new data to process")
                
        except Exception as e:
            self.log(f"❌ Update cycle error: {e}", "ERROR")
    
    def start_scheduler(self):
        """Start the automatic scheduler"""
        self.log("🚀 Starting Kaggle auto-updater...")
        self.log(f"⏰ Update interval: {self.config['update_interval_minutes']} minutes")
        
        # Schedule the update
        schedule.every(self.config["update_interval_minutes"]).minutes.do(self.run_update_cycle)
        
        # Run initial update
        self.run_update_cycle()
        
        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.log("🛑 Auto-updater stopped by user")
        except Exception as e:
            self.log(f"❌ Scheduler error: {e}", "ERROR")
    
    def run_once(self):
        """Run update once and exit"""
        self.log("🔄 Running single update...")
        self.run_update_cycle()
        self.log("✅ Single update completed")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="COINjecture Kaggle Auto-Updater")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--config", default="kaggle_config.json", help="Config file path")
    
    args = parser.parse_args()
    
    print("🚀 COINjecture Kaggle Auto-Updater")
    print("=" * 50)
    
    # Create updater
    updater = KaggleAutoUpdater(args.config)
    
    if args.once:
        updater.run_once()
    else:
        updater.start_scheduler()

if __name__ == "__main__":
    main()
