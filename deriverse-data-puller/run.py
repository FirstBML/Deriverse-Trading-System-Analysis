#!/usr/bin/env python
"""
Deriverse Trading System - Interactive Runner
Interactive menu system for managing data and running the pipeline.
"""

# Fix Unicode encoding for Windows console
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import subprocess
import time
import shutil
from pathlib import Path
import os

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print the application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        🚀 DERIVERSE TRADING SYSTEM - INTERACTIVE MENU        ║
║                                                               ║
║           Complete Pipeline Management & Data Control         ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def print_menu():
    """Display the main menu."""
    menu = """
┌───────────────────────────────────────────────────────────────┐
│                        MAIN MENU                              │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  1. 🚀 Run Complete Pipeline (Generate Data + Dashboard)     │
│  2. 📊 Run Pipeline Only (No Dashboard)                      │
│  3. 🌐 Launch Dashboard Only                                 │
│                                                               │
│  4. 🧹 Clean All Data (Complete Reset)                       │
│  5. 🧹 Clean Analytics Only (Keep Raw Events)                │
│  6. 🧹 Clean Trader Notes Only                               │
│  7. 🧹 Clean Normalized Events Only                          │
│                                                               │
│  8. 📋 View Data Status                                      │
│  9. ⚙️  Advanced Options                                      │
│                                                               │
│  0. 🚪 Exit                                                   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
"""
    print(menu)

def print_step(text):
    """Print a step message."""
    print(f"\n📋 {text}...")

def print_success(text):
    """Print a success message."""
    print(f"✅ {text}")

def print_warning(text):
    """Print a warning message."""
    print(f"⚠️  {text}")

def print_error(text):
    """Print an error message."""
    print(f"❌ {text}")

def print_info(text):
    """Print an info message."""
    print(f"ℹ️  {text}")

def pause():
    """Pause and wait for user to press Enter."""
    input("\n Press Enter to continue...")

def confirm_action(action_description):
    """Ask user to confirm a potentially destructive action."""
    print(f"\n⚠️  WARNING: {action_description}")
    response = input("   Are you sure you want to proceed? (yes/no): ").strip().lower()
    return response in ['yes', 'y']

def run_command(cmd, description):
    """Run a command and handle errors."""
    print_step(description)
    try:
        # Set PYTHONIOENCODING for subprocess on Windows
        env = None
        if sys.platform == 'win32':
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True,
            env=env,
            encoding='utf-8'
        )
        print_success(f"{description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Error during {description}")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import streamlit, pandas, plotly
        return True
    except ImportError:
        return False

def get_data_status():
    """Get status of generated data."""
    data_dir = Path("data")
    status = {
        'analytics': False,
        'normalized': False,
        'notes': False,
        'total_size': 0
    }
    
    if not data_dir.exists():
        return status
    
    # Check analytics
    analytics_dir = data_dir / "analytics_output"
    if analytics_dir.exists():
        csv_files = list(analytics_dir.glob("*.csv"))
        status['analytics'] = len(csv_files) > 0
        status['analytics_count'] = len(csv_files)
        status['total_size'] += sum(f.stat().st_size for f in csv_files)
    
    # Check normalized
    norm_dir = data_dir / "normalized"
    if norm_dir.exists():
        json_files = list(norm_dir.glob("*.json"))
        status['normalized'] = len(json_files) > 0
        status['normalized_count'] = len(json_files)
        status['total_size'] += sum(f.stat().st_size for f in json_files)
    
    # Check notes
    notes_dir = data_dir / "trader_notes"
    if notes_dir.exists():
        note_files = list(notes_dir.glob("*.json"))
        status['notes'] = len(note_files) > 0
        status['notes_count'] = len(note_files)
        status['total_size'] += sum(f.stat().st_size for f in note_files)
    
    return status

def display_data_status():
    """Display current data status."""
    clear_screen()
    print_banner()
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║                      DATA STATUS                             ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    status = get_data_status()
    
    # Analytics
    if status['analytics']:
        print(f"  ✅ Analytics Data:     {status['analytics_count']} files")
    else:
        print(f"  ❌ Analytics Data:     No data")
    
    # Normalized
    if status['normalized']:
        print(f"  ✅ Normalized Events:  {status['normalized_count']} files")
    else:
        print(f"  ❌ Normalized Events:  No data")
    
    # Notes
    if status['notes']:
        print(f"  ✅ Trader Notes:       {status['notes_count']} files")
    else:
        print(f"  ❌ Trader Notes:       No data")
    
    # Total size
    size_mb = status['total_size'] / (1024 * 1024)
    print(f"\n  💾 Total Size:         {size_mb:.2f} MB")
    
    # Check if ready to run dashboard
    print("\n" + "─" * 63)
    if status['analytics']:
        print("  🌐 Status: Ready to launch dashboard")
    else:
        print("  ⚠️  Status: Run pipeline to generate data first")
    print("─" * 63)
    
    pause()

def cleanup_data(clean_level):
    """Clean up generated data based on level."""
    data_dir = Path("data")
    
    if clean_level == "all":
        if not confirm_action("This will delete ALL generated data"):
            print_warning("Operation cancelled")
            return False
        
        print_step("Removing ALL generated data")
        if data_dir.exists():
            shutil.rmtree(data_dir)
            print_success("All data removed")
        else:
            print_warning("No data directory found")
    
    elif clean_level == "analytics":
        print_step("Removing analytics outputs")
        analytics_dir = data_dir / "analytics_output"
        if analytics_dir.exists():
            shutil.rmtree(analytics_dir)
            print_success("Analytics outputs removed")
        else:
            print_warning("No analytics outputs found")
    
    elif clean_level == "notes":
        if not confirm_action("This will delete all trader notes"):
            print_warning("Operation cancelled")
            return False
        
        print_step("Removing trader notes")
        notes_dir = data_dir / "trader_notes"
        if notes_dir.exists():
            shutil.rmtree(notes_dir)
            print_success("Trader notes removed")
        else:
            print_warning("No trader notes found")
    
    elif clean_level == "normalized":
        print_step("Removing normalized events")
        norm_dir = data_dir / "normalized"
        if norm_dir.exists():
            shutil.rmtree(norm_dir)
            print_success("Normalized events removed")
        else:
            print_warning("No normalized events found")
    
    # Recreate necessary directories
    if clean_level in ["all", "analytics", "normalized", "notes"]:
        data_dir.mkdir(exist_ok=True)
        (data_dir / "analytics_output").mkdir(exist_ok=True)
        (data_dir / "normalized").mkdir(exist_ok=True)
        (data_dir / "trader_notes").mkdir(exist_ok=True)
        print_success("Data directories recreated")
    
    pause()
    return True

def run_pipeline(launch_dashboard=True):
    """Run the complete pipeline."""
    clear_screen()
    print_banner()
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║                   RUNNING PIPELINE                            ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    # Check dependencies
    if not check_dependencies():
        print_error("Missing dependencies!")
        print_info("Run: uv pip install -e .")
        pause()
        return False
    
    print_success("Dependencies verified")
    
    # Step 1: Generate mock data
    if not run_command("python -m scripts.generate_mock_data", "Generating mock data"):
        pause()
        return False
    
    # Step 2: Run ingestion
    if not run_command("python -m scripts.run_ingestion", "Ingesting events"):
        pause()
        return False
    
    # Step 3: Run analytics
    if not run_command("python -m scripts.run_analytics", "Computing analytics"):
        pause()
        return False
    
    # Show summary
    print("\n" + "═" * 63)
    print("  📊 DATA GENERATION COMPLETE")
    print("═" * 63)
    
    status = get_data_status()
    if status['analytics']:
        print(f"  ✅ Generated {status['analytics_count']} analytics files")
    
    # Launch dashboard if requested
    if launch_dashboard:
        print("\n" + "═" * 63)
        print("  🌐 LAUNCHING DASHBOARD")
        print("═" * 63)
        print("\n  💡 Tips:")
        print("     • Admin access: add ?admin=1 to URL")
        print("     • Example: http://localhost:8501/?admin=1")
        print("     • Press Ctrl+C to stop the dashboard\n")
        print("═" * 63)
        
        input("\nPress Enter to launch dashboard (or Ctrl+C to cancel)...")
        
        # Set environment variable for dashboard subprocess
        env = None
        if sys.platform == 'win32':
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
        
        try:
            subprocess.run("streamlit run dashboards/app.py", shell=True, env=env)
        except KeyboardInterrupt:
            print("\n\n⚠️  Dashboard stopped by user")
    else:
        print("\n  ✅ Pipeline complete! Dashboard not launched.")
        pause()
    
    return True

def launch_dashboard_only():
    """Launch the dashboard without running the pipeline."""
    clear_screen()
    print_banner()
    
    # Check if data exists
    status = get_data_status()
    if not status['analytics']:
        print_error("No analytics data found!")
        print_info("Run the complete pipeline first (Option 1)")
        pause()
        return
    
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║                   LAUNCHING DASHBOARD                         ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    print("  💡 Tips:")
    print("     • Admin access: add ?admin=1 to URL")
    print("     • Example: http://localhost:8501/?admin=1")
    print("     • Press Ctrl+C to stop the dashboard\n")
    print("═" * 63)
    
    input("\nPress Enter to launch dashboard (or Ctrl+C to cancel)...")
    
    # Set environment variable for dashboard subprocess
    env = None
    if sys.platform == 'win32':
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
    
    try:
        subprocess.run("streamlit run dashboards/app.py", shell=True, env=env)
    except KeyboardInterrupt:
        print("\n\n⚠️  Dashboard stopped by user")
    
    pause()

def advanced_options():
    """Display advanced options menu."""
    while True:
        clear_screen()
        print_banner()
        print("\n╔═══════════════════════════════════════════════════════════════╗")
        print("║                    ADVANCED OPTIONS                           ║")
        print("╚═══════════════════════════════════════════════════════════════╝\n")
        
        print("  1. 🔄 Run Pipeline with Validation")
        print("  2. 🧪 Generate Mock Data Only")
        print("  3. 📥 Run Ingestion Only")
        print("  4. 📊 Run Analytics Only")
        print("  5. ✔️  Validate Analytics Data")
        print("  6. 🔧 Check System Dependencies")
        print("\n  0. ⬅️  Back to Main Menu\n")
        print("─" * 63)
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            clear_screen()
            print_banner()
            run_pipeline(launch_dashboard=False)
            run_command("python -m scripts.validate_analytics", "Validating analytics")
            pause()
        
        elif choice == '2':
            clear_screen()
            print_banner()
            run_command("python -m scripts.generate_mock_data", "Generating mock data")
            pause()
        
        elif choice == '3':
            clear_screen()
            print_banner()
            run_command("python -m scripts.run_ingestion", "Running ingestion")
            pause()
        
        elif choice == '4':
            clear_screen()
            print_banner()
            run_command("python -m scripts.run_analytics", "Running analytics")
            pause()
        
        elif choice == '5':
            clear_screen()
            print_banner()
            run_command("python -m scripts.validate_analytics", "Validating analytics")
            pause()
        
        elif choice == '6':
            clear_screen()
            print_banner()
            print("\n╔═══════════════════════════════════════════════════════════════╗")
            print("║                  SYSTEM DEPENDENCIES                          ║")
            print("╚═══════════════════════════════════════════════════════════════╝\n")
            
            deps = {
                'streamlit': 'Dashboard framework',
                'pandas': 'Data processing',
                'plotly': 'Charting library',
                'pyyaml': 'Configuration files',
                'python-dotenv': 'Environment variables'
            }
            
            for package, description in deps.items():
                try:
                    __import__(package)
                    print(f"  ✅ {package:20} - {description}")
                except ImportError:
                    print(f"  ❌ {package:20} - {description} (MISSING)")
            
            print("\n  To install missing dependencies:")
            print("  $ uv pip install -e .")
            pause()
        
        elif choice == '0':
            break
        
        else:
            print_error("Invalid option")
            time.sleep(1)

def main():
    """Main interactive loop."""
    # Check if running in the right directory
    if not Path("pyproject.toml").exists():
        clear_screen()
        print_banner()
        print_error("Please run this script from the project root directory")
        print_info("Current directory should contain: pyproject.toml, dashboards/, scripts/")
        pause()
        sys.exit(1)
    
    while True:
        clear_screen()
        print_banner()
        print_menu()
        
        choice = input("Select option (0-9): ").strip()
        
        if choice == '1':
            # Run complete pipeline
            run_pipeline(launch_dashboard=True)
        
        elif choice == '2':
            # Run pipeline only
            run_pipeline(launch_dashboard=False)
        
        elif choice == '3':
            # Launch dashboard only
            launch_dashboard_only()
        
        elif choice == '4':
            # Clean all data
            clear_screen()
            print_banner()
            cleanup_data("all")
        
        elif choice == '5':
            # Clean analytics only
            clear_screen()
            print_banner()
            cleanup_data("analytics")
        
        elif choice == '6':
            # Clean notes only
            clear_screen()
            print_banner()
            cleanup_data("notes")
        
        elif choice == '7':
            # Clean normalized events only
            clear_screen()
            print_banner()
            cleanup_data("normalized")
        
        elif choice == '8':
            # View data status
            display_data_status()
        
        elif choice == '9':
            # Advanced options
            advanced_options()
        
        elif choice == '0':
            # Exit
            clear_screen()
            print_banner()
            print("\n  👋 Thank you for using Deriverse Trading System!")
            print("\n" + "═" * 63 + "\n")
            break
        
        else:
            print_error("Invalid option. Please select 0-9.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Program interrupted by user")
        print("\n  👋 Goodbye!\n")
        sys.exit(0)