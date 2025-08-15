#!/usr/bin/env python3
"""
UpdateEngine.exe - Separate process for safe file replacement
This runs as a separate process to handle updates without blocking the launcher
"""

import sys
import os
import shutil
import json
import time
import subprocess
import tempfile
from pathlib import Path

class UpdateEngine:
    def __init__(self):
        self.temp_dir = None
        self.install_path = None
        self.backup_path = None
        self.update_manifest = None
    
    def run(self, args):
        """Main entry point for update engine"""
        if len(args) < 3:
            print("Usage: UpdateEngine.exe <install_path> <temp_update_dir> [manifest_file]")
            return 1
        
        self.install_path = args[1]
        self.temp_dir = args[2]
        manifest_file = args[3] if len(args) > 3 else None
        
        try:
            # Load update manifest if provided
            if manifest_file and os.path.exists(manifest_file):
                with open(manifest_file, 'r') as f:
                    self.update_manifest = json.load(f)
            
            # Create backup
            self.create_backup()
            
            # Apply updates
            self.apply_updates()
            
            # Clean up
            self.cleanup()
            
            print("Update completed successfully")
            return 0
            
        except Exception as e:
            print(f"Update failed: {e}")
            self.rollback()
            return 1
    
    def create_backup(self):
        """Create backup of current files"""
        try:
            self.backup_path = os.path.join(self.install_path, "backups", f"backup_{int(time.time())}")
            os.makedirs(self.backup_path, exist_ok=True)
            
            # Backup critical files
            critical_files = ["CFCMonitor.exe", "config.json", "version.txt"]
            
            for file in critical_files:
                src = os.path.join(self.install_path, file)
                if os.path.exists(src):
                    dst = os.path.join(self.backup_path, file)
                    shutil.copy2(src, dst)
            
            print(f"Backup created at: {self.backup_path}")
            
        except Exception as e:
            raise Exception(f"Failed to create backup: {e}")
    
    def apply_updates(self):
        """Apply updates from temp directory"""
        try:
            # Wait a moment for processes to release file handles
            time.sleep(2)
            
            # Find all files to update
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, self.temp_dir)
                    dst_path = os.path.join(self.install_path, rel_path)
                    
                    # Skip non-executable/library files unless specified
                    if not any(file.endswith(ext) for ext in ['.exe', '.dll', '.json', '.txt']):
                        continue
                    
                    # Ensure destination directory exists
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    
                    # Replace file
                    self.safe_replace_file(src_path, dst_path)
                    print(f"Updated: {rel_path}")
            
        except Exception as e:
            raise Exception(f"Failed to apply updates: {e}")
    
    def safe_replace_file(self, src_path, dst_path):
        """Safely replace a file that might be in use"""
        max_retries = 5
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # If destination exists, move it to backup location
                if os.path.exists(dst_path):
                    temp_backup = dst_path + f".backup.{int(time.time())}"
                    shutil.move(dst_path, temp_backup)
                
                # Copy new file
                shutil.copy2(src_path, dst_path)
                
                # Remove temporary backup if successful
                if os.path.exists(temp_backup):
                    os.remove(temp_backup)
                
                return
                
            except PermissionError as e:
                if attempt < max_retries - 1:
                    print(f"File in use, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise Exception(f"Could not replace {dst_path} after {max_retries} attempts: {e}")
            except Exception as e:
                # Restore backup if copy failed
                temp_backup = dst_path + f".backup.{int(time.time())}"
                if os.path.exists(temp_backup):
                    shutil.move(temp_backup, dst_path)
                raise e
    
    def rollback(self):
        """Rollback to backup if update fails"""
        try:
            if self.backup_path and os.path.exists(self.backup_path):
                print("Rolling back changes...")
                
                for root, dirs, files in os.walk(self.backup_path):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, self.backup_path)
                        dst_path = os.path.join(self.install_path, rel_path)
                        
                        shutil.copy2(src_path, dst_path)
                
                print("Rollback completed")
        except Exception as e:
            print(f"Rollback failed: {e}")
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            # Keep backup for a while, clean up temp files
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Cleanup warning: {e}")

def main():
    """Main entry point"""
    engine = UpdateEngine()
    return engine.run(sys.argv)

if __name__ == "__main__":
    sys.exit(main())
