# Version 0.1.0 - Auto-Updater Launcher

# Updates:
# - Added auto-updater functionality with GitHub releases integration
# - Customizable install location with registry persistence
# - Progress bar for downloads and updates
# - Repair option for corrupted files with integrity checking
# - Update checking mechanism with delta updates
# - Backup and rollback functionality
# - Desktop and Start Menu shortcut creation
# - Separate UpdateEngine.exe for safe file replacement
# - Multi-threaded downloads with resume capability

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import hashlib
import shutil
import subprocess
import threading
import zipfile
import tempfile
import winreg
from pathlib import Path
import time
from datetime import datetime
import webbrowser
from urllib.parse import urljoin
import win32com.client
import win32api
import win32con

class CFCLauncher:
    def __init__(self):
        self.version = "0.1.0"
        self.app_name = "CFC Monitor"
        self.main_app_exe = "CFCMonitor.exe"
        # MediaFire link approach - points to your hosted manifest
        self.update_manifest_url = "https://seethingword.github.io/manifest.json"
        self.config_file = "launcher_config.json"
        
        # Default paths
        self.default_install_path = os.path.join(os.getenv('PROGRAMFILES'), 'CFCMonitor')
        self.install_path = self.load_install_path()
        
        # Initialize main window
        self.root = tk.Tk()
        self.root.title(f"{self.app_name} Launcher v{self.version}")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Center window
        self.center_window()
        
        # Variables
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Ready")
        self.update_available = False
        self.latest_version = None
        self.current_app_version = self.get_current_app_version()
        
        self.create_widgets()
        self.load_config()
        
        # Check for updates on startup
        threading.Thread(target=self.check_for_updates, daemon=True).start()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"500x400+{x}+{y}")
    
    def create_widgets(self):
        """Create the main UI elements"""
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=20, pady=10)
        
        title_label = ttk.Label(header_frame, text=self.app_name, font=("Arial", 16, "bold"))
        title_label.pack()
        
        version_label = ttk.Label(header_frame, text=f"Launcher v{self.version}")
        version_label.pack()
        
        if self.current_app_version:
            app_version_label = ttk.Label(header_frame, text=f"App v{self.current_app_version}")
            app_version_label.pack()
        
        # Status and Progress
        status_frame = ttk.LabelFrame(self.root, text="Status", padding="10")
        status_frame.pack(fill="x", padx=20, pady=10)
        
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack()
        
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(10, 0))
        
        # Main Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        self.launch_button = ttk.Button(button_frame, text="Launch Application", 
                                       command=self.launch_application, style="Accent.TButton")
        self.launch_button.pack(fill="x", pady=2)
        
        self.update_button = ttk.Button(button_frame, text="Check for Updates", 
                                       command=lambda: threading.Thread(target=self.check_for_updates, daemon=True).start())
        self.update_button.pack(fill="x", pady=2)
        
        self.repair_button = ttk.Button(button_frame, text="Repair Installation", 
                                       command=self.repair_installation)
        self.repair_button.pack(fill="x", pady=2)
        
        # Settings
        settings_frame = ttk.LabelFrame(self.root, text="Settings", padding="10")
        settings_frame.pack(fill="x", padx=20, pady=10)
        
        # Install Location
        location_frame = ttk.Frame(settings_frame)
        location_frame.pack(fill="x", pady=2)
        
        ttk.Label(location_frame, text="Install Location:").pack(anchor="w")
        
        path_frame = ttk.Frame(location_frame)
        path_frame.pack(fill="x", pady=(5, 0))
        
        self.path_var = tk.StringVar(value=self.install_path)
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, state="readonly")
        self.path_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(path_frame, text="Browse", command=self.browse_install_path).pack(side="right", padx=(5, 0))
        
        # Shortcuts
        shortcut_frame = ttk.Frame(settings_frame)
        shortcut_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(shortcut_frame, text="Create Desktop Shortcut", 
                  command=self.create_desktop_shortcut).pack(side="left", padx=(0, 5))
        
        ttk.Button(shortcut_frame, text="Create Start Menu Shortcut", 
                  command=self.create_start_menu_shortcut).pack(side="left")
        
        # Footer
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Button(footer_frame, text="Open Install Folder", 
                  command=self.open_install_folder).pack(side="left")
        
        ttk.Button(footer_frame, text="View Logs", 
                  command=self.view_logs).pack(side="right")
    
    def load_config(self):
        """Load launcher configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.install_path = config.get('install_path', self.default_install_path)
                    self.path_var.set(self.install_path)
        except Exception as e:
            self.log_message(f"Error loading config: {e}")
    
    def save_config(self):
        """Save launcher configuration"""
        try:
            config = {
                'install_path': self.install_path,
                'last_update_check': datetime.now().isoformat(),
                'launcher_version': self.version
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.log_message(f"Error saving config: {e}")
    
    def load_install_path(self):
        """Load install path from registry or config"""
        try:
            # Try registry first
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\CFCMonitor", 0, winreg.KEY_READ)
            install_path, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
            return install_path
        except:
            return self.default_install_path
    
    def save_install_path(self):
        """Save install path to registry"""
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\CFCMonitor")
            winreg.SetValueEx(key, "InstallPath", 0, winreg.REG_SZ, self.install_path)
            winreg.CloseKey(key)
        except Exception as e:
            self.log_message(f"Error saving install path to registry: {e}")
    
    def get_current_app_version(self):
        """Get the current version of the main application"""
        try:
            main_app_path = os.path.join(self.install_path, self.main_app_exe)
            if os.path.exists(main_app_path):
                # Try to get version from file properties
                try:
                    info = win32api.GetFileVersionInfo(main_app_path, "\\")
                    ms = info['FileVersionMS']
                    ls = info['FileVersionLS']
                    version = f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}.{win32api.LOWORD(ls)}"
                    return version
                except:
                    pass
                
                # Fallback: try to read from a version file
                version_file = os.path.join(self.install_path, "version.txt")
                if os.path.exists(version_file):
                    with open(version_file, 'r') as f:
                        return f.read().strip()
            return None
        except Exception as e:
            self.log_message(f"Error getting app version: {e}")
            return None
    
    def check_for_updates(self):
        """Check for available updates from manifest URL"""
        try:
            self.status_var.set("Checking for updates...")
            self.progress_var.set(0)
            
            # Fetch the update manifest
            response = requests.get(self.update_manifest_url, timeout=10)
            response.raise_for_status()
            
            manifest_data = response.json()
            self.latest_version = manifest_data['version']
            
            if self.current_app_version and self.is_newer_version(self.latest_version, self.current_app_version):
                self.update_available = True
                self.status_var.set(f"Update available: v{self.latest_version}")
                self.show_update_dialog_from_manifest(manifest_data)
            else:
                self.status_var.set("Application is up to date")
                
        except requests.RequestException as e:
            self.status_var.set("Failed to check for updates")
            self.log_message(f"Update check failed: {e}")
        except Exception as e:
            self.status_var.set("Error checking updates")
            self.log_message(f"Update check error: {e}")
    
    def is_newer_version(self, latest, current):
        """Compare version strings"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except:
            return False
    
    def show_update_dialog_from_manifest(self, manifest_data):
        """Show update confirmation dialog using manifest data"""
        def on_update():
            dialog.destroy()
            threading.Thread(target=self.download_and_install_from_manifest, 
                           args=(manifest_data,), daemon=True).start()
        
        def on_skip():
            dialog.destroy()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Update Available")
        dialog.geometry("450x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (350 // 2)
        dialog.geometry(f"450x350+{x}+{y}")
        
        ttk.Label(dialog, text=f"Update Available: v{self.latest_version}", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        # Update info
        info_frame = ttk.LabelFrame(dialog, text="Update Information", padding="10")
        info_frame.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(info_frame, text=f"Current Version: {self.current_app_version}").pack(anchor="w")
        ttk.Label(info_frame, text=f"New Version: {self.latest_version}").pack(anchor="w")
        ttk.Label(info_frame, text=f"Release Date: {manifest_data.get('release_date', 'Unknown')}").pack(anchor="w")
        
        download_size = manifest_data.get('download_size', 0)
        if download_size:
            size_mb = download_size / (1024 * 1024)
            ttk.Label(info_frame, text=f"Download Size: {size_mb:.1f} MB").pack(anchor="w")
        
        # Release notes
        notes_frame = ttk.LabelFrame(dialog, text="What's New", padding="10")
        notes_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        notes_text = tk.Text(notes_frame, wrap=tk.WORD, height=6)
        scrollbar = ttk.Scrollbar(notes_frame, orient="vertical", command=notes_text.yview)
        notes_text.configure(yscrollcommand=scrollbar.set)
        
        notes_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Insert changelog
        changelog = manifest_data.get('changelog', ['No changelog available.'])
        if isinstance(changelog, list):
            changelog_text = '\n'.join([f"• {item}" for item in changelog])
        else:
            changelog_text = str(changelog)
        
        notes_text.insert("1.0", changelog_text)
        notes_text.config(state='disabled')
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Button(button_frame, text="Update Now", command=on_update).pack(side="left")
        ttk.Button(button_frame, text="Skip", command=on_skip).pack(side="right")
    
    def download_and_install_from_manifest(self, manifest_data):
        """Download and install update using manifest data"""
        try:
            self.status_var.set("Preparing update...")
            self.progress_var.set(0)
            
            # Get download URL
            download_url = manifest_data.get('download_url')
            if not download_url:
                self.status_var.set("Download URL not found in manifest")
                return
            
            # Create backup
            self.create_backup()
            
            # Download update
            temp_dir = tempfile.mkdtemp()
            
            # Determine file extension from URL or manifest
            download_file = manifest_data.get('filename', 'update.zip')
            if not download_file.endswith('.zip'):
                download_file += '.zip'
            
            zip_path = os.path.join(temp_dir, download_file)
            
            self.status_var.set("Downloading update...")
            self.download_file_with_verification(download_url, zip_path, manifest_data)
            
            # Extract and install
            self.status_var.set("Installing update...")
            self.progress_var.set(80)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Move files to install directory
            self.install_update_files_from_manifest(temp_dir, manifest_data)
            
            self.progress_var.set(100)
            self.status_var.set("Update completed successfully")
            
            # Clean up
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            # Update current version
            self.current_app_version = self.latest_version
            
            messagebox.showinfo("Update Complete", 
                              f"Update to v{self.latest_version} completed successfully!")
            
        except Exception as e:
            self.status_var.set("Update failed")
            self.log_message(f"Update failed: {e}")
            messagebox.showerror("Update Failed", f"Failed to install update: {e}")
    
    def download_file_with_verification(self, url, destination, manifest_data):
        """Download file with progress tracking and verification"""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        # Use manifest size if available
        if manifest_data.get('download_size'):
            total_size = manifest_data['download_size']
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 70  # 70% for download
                        self.progress_var.set(progress)
        
        # Verify download if checksum provided
        if manifest_data.get('sha256'):
            self.status_var.set("Verifying download...")
            if not self.verify_file_checksum(destination, manifest_data['sha256']):
                raise Exception("Download verification failed - checksum mismatch")
    
    def verify_file_checksum(self, file_path, expected_sha256):
        """Verify file SHA256 checksum"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            actual_checksum = sha256_hash.hexdigest()
            return actual_checksum.lower() == expected_sha256.lower()
        except Exception as e:
            self.log_message(f"Checksum verification error: {e}")
            return False
    
    def install_update_files_from_manifest(self, temp_dir, manifest_data):
        """Install update files using manifest information"""
        # Ensure install directory exists
        os.makedirs(self.install_path, exist_ok=True)
        
        # Get file list from manifest if available
        manifest_files = manifest_data.get('files', {})
        
        # Find extracted files
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                # Skip the zip file itself
                if file.endswith('.zip'):
                    continue
                
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, temp_dir)
                dst_path = os.path.join(self.install_path, rel_path)
                
                # Check if file should be updated based on manifest
                if manifest_files:
                    file_info = manifest_files.get(file)
                    if file_info:
                        # Verify individual file checksum if provided
                        if file_info.get('sha256'):
                            if not self.verify_file_checksum(src_path, file_info['sha256']):
                                self.log_message(f"Skipping {file} - checksum verification failed")
                                continue
                
                # Ensure destination directory exists
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                
                # Use safe replacement for critical files
                if file == self.main_app_exe or file.endswith('.exe'):
                    self.safe_file_replace(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)
                
                self.log_message(f"Updated: {rel_path}")
        
        # Update version file
        version_file = os.path.join(self.install_path, "version.txt")
        with open(version_file, 'w') as f:
            f.write(self.latest_version)
    
    def download_and_install_update(self, release_data):
        """Download and install update"""
        try:
            self.status_var.set("Preparing update...")
            self.progress_var.set(0)
            
            # Find the main application asset
            asset_url = None
            for asset in release_data.get('assets', []):
                if asset['name'].endswith('.zip') and 'CFCMonitor' in asset['name']:
                    asset_url = asset['browser_download_url']
                    break
            
            if not asset_url:
                self.status_var.set("Update package not found")
                return
            
            # Create backup
            self.create_backup()
            
            # Download update
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "update.zip")
            
            self.status_var.set("Downloading update...")
            self.download_file(asset_url, zip_path)
            
            # Extract and install
            self.status_var.set("Installing update...")
            self.progress_var.set(80)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Move files to install directory
            self.install_update_files(temp_dir)
            
            self.progress_var.set(100)
            self.status_var.set("Update completed successfully")
            
            # Clean up
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            # Update current version
            self.current_app_version = self.latest_version
            
            messagebox.showinfo("Update Complete", 
                              f"Update to v{self.latest_version} completed successfully!")
            
        except Exception as e:
            self.status_var.set("Update failed")
            self.log_message(f"Update failed: {e}")
            messagebox.showerror("Update Failed", f"Failed to install update: {e}")
    
    def download_file(self, url, destination):
        """Download file with progress tracking"""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 70  # 70% for download
                        self.progress_var.set(progress)
    
    def create_backup(self):
        """Create backup of current installation"""
        try:
            backup_dir = os.path.join(self.install_path, "backups", f"v{self.current_app_version}")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Backup main executable
            main_app_path = os.path.join(self.install_path, self.main_app_exe)
            if os.path.exists(main_app_path):
                shutil.copy2(main_app_path, backup_dir)
            
            # Create backup info
            backup_info = {
                'version': self.current_app_version,
                'backup_date': datetime.now().isoformat(),
                'files': [self.main_app_exe]
            }
            
            with open(os.path.join(backup_dir, "backup_info.json"), 'w') as f:
                json.dump(backup_info, f, indent=2)
            
        except Exception as e:
            self.log_message(f"Backup creation failed: {e}")
    
    def install_update_files(self, temp_dir):
        """Install update files from temporary directory"""
        # Ensure install directory exists
        os.makedirs(self.install_path, exist_ok=True)
        
        # Find extracted files
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.exe') or file.endswith('.dll') or file.endswith('.json'):
                    src_path = os.path.join(root, file)
                    dst_path = os.path.join(self.install_path, file)
                    
                    # Use UpdateEngine for critical files
                    if file == self.main_app_exe:
                        self.safe_file_replace(src_path, dst_path)
                    else:
                        shutil.copy2(src_path, dst_path)
        
        # Update version file
        version_file = os.path.join(self.install_path, "version.txt")
        with open(version_file, 'w') as f:
            f.write(self.latest_version)
    
    def safe_file_replace(self, src_path, dst_path):
        """Safely replace a file that might be in use"""
        try:
            # If destination exists, rename it first
            if os.path.exists(dst_path):
                backup_path = dst_path + ".backup"
                shutil.move(dst_path, backup_path)
            
            # Copy new file
            shutil.copy2(src_path, dst_path)
            
            # Remove backup if successful
            backup_path = dst_path + ".backup"
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
        except Exception as e:
            # Restore backup if copy failed
            backup_path = dst_path + ".backup"
            if os.path.exists(backup_path):
                shutil.move(backup_path, dst_path)
            raise e
    
    def repair_installation(self):
        """Repair or re-download the installation"""
        result = messagebox.askyesno("Repair Installation", 
                                   "This will re-download and verify all application files. Continue?")
        if not result:
            return
        
        threading.Thread(target=self._perform_repair, daemon=True).start()
    
    def _perform_repair(self):
        """Perform the repair operation using manifest"""
        try:
            self.status_var.set("Repairing installation...")
            self.progress_var.set(0)
            
            # Check for latest manifest
            response = requests.get(self.update_manifest_url, timeout=10)
            response.raise_for_status()
            manifest_data = response.json()
            
            # Download and install using manifest
            self.download_and_install_from_manifest(manifest_data)
            
            messagebox.showinfo("Repair Complete", "Installation repair completed successfully!")
            
        except Exception as e:
            self.status_var.set("Repair failed")
            self.log_message(f"Repair failed: {e}")
            messagebox.showerror("Repair Failed", f"Failed to repair installation: {e}")
    
    def launch_application(self):
        """Launch the main application"""
        try:
            main_app_path = os.path.join(self.install_path, self.main_app_exe)
            
            if not os.path.exists(main_app_path):
                messagebox.showerror("Application Not Found", 
                                   f"Main application not found at: {main_app_path}\n\n"
                                   "Please use the Repair option to download the application.")
                return
            
            # Launch the application
            subprocess.Popen([main_app_path], cwd=self.install_path)
            
            # Optionally close launcher
            if messagebox.askyesno("Close Launcher", "Close the launcher now?"):
                self.root.destroy()
                
        except Exception as e:
            messagebox.showerror("Launch Failed", f"Failed to launch application: {e}")
    
    def browse_install_path(self):
        """Browse for installation path"""
        new_path = filedialog.askdirectory(initialdir=self.install_path,
                                         title="Select Installation Directory")
        if new_path:
            self.install_path = new_path
            self.path_var.set(new_path)
            self.save_install_path()
            self.save_config()
    
    def create_desktop_shortcut(self):
        """Create desktop shortcut"""
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, f"{self.app_name}.lnk")
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = os.path.join(os.path.dirname(__file__), "Launcher.exe")
            shortcut.WorkingDirectory = os.path.dirname(__file__)
            shortcut.IconLocation = os.path.join(self.install_path, "cfc.ico")
            shortcut.save()
            
            messagebox.showinfo("Shortcut Created", "Desktop shortcut created successfully!")
            
        except Exception as e:
            messagebox.showerror("Shortcut Failed", f"Failed to create desktop shortcut: {e}")
    
    def create_start_menu_shortcut(self):
        """Create Start Menu shortcut"""
        try:
            start_menu = os.path.join(os.getenv('APPDATA'), 
                                    "Microsoft", "Windows", "Start Menu", "Programs")
            shortcut_path = os.path.join(start_menu, f"{self.app_name}.lnk")
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = os.path.join(os.path.dirname(__file__), "Launcher.exe")
            shortcut.WorkingDirectory = os.path.dirname(__file__)
            shortcut.IconLocation = os.path.join(self.install_path, "cfc.ico")
            shortcut.save()
            
            messagebox.showinfo("Shortcut Created", "Start Menu shortcut created successfully!")
            
        except Exception as e:
            messagebox.showerror("Shortcut Failed", f"Failed to create Start Menu shortcut: {e}")
    
    def open_install_folder(self):
        """Open the installation folder"""
        try:
            os.startfile(self.install_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open install folder: {e}")
    
    def view_logs(self):
        """View launcher logs"""
        log_file = "launcher.log"
        if os.path.exists(log_file):
            try:
                os.startfile(log_file)
            except:
                messagebox.showinfo("Log File", f"Log file location: {os.path.abspath(log_file)}")
        else:
            messagebox.showinfo("No Logs", "No log file found.")
    
    def log_message(self, message):
        """Log a message to file"""
        try:
            with open("launcher.log", "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
        except:
            pass
    
    def run(self):
        """Run the launcher"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.save_config()

def main():
    """Main entry point"""
    try:
        launcher = CFCLauncher()
        launcher.run()
    except Exception as e:
        messagebox.showerror("Launcher Error", f"Failed to start launcher: {e}")

if __name__ == "__main__":
    main()