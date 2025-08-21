#!/usr/bin/env python3
"""
Quick start script for Knowledge Graph Construction Project
"""
import os
import sys
import subprocess
import json
from pathlib import Path

def print_header():
    """Print project header"""
    print("🧠 Knowledge Graph Construction Project")
    print("=====================================")
    print()

def check_environment():
    """Check if environment is properly set up"""
    print("🔍 Checking environment...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("📝 Please copy .env.example to .env and configure API keys")
        return False
    
    # Check if virtual environment is activated
    if not os.environ.get('VIRTUAL_ENV'):
        print("⚠️  Virtual environment not detected")
        print("💡 Consider activating virtual environment: source venv/bin/activate")
    
    # Check if required packages are installed
    try:
        import openai
        import anthropic
        import google.generativeai
        import pandas
        import streamlit
        print("✅ Core dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Run: pip install -r requirements.txt")
        return False

def create_sample_data():
    """Create sample data for testing"""
    print("📊 Creating sample data...")
    
    sample_data = {
        "achievement_standards": [
            {
                "standard_code": "2수01-01",
                "content": "수의 필요성을 인식하면서 0과 100까지의 수 개념을 이해하고, 수를 세고 읽고 쓸 수 있다.",
                "domain": "수와 연산",
                "grade": "초등 1-2학년군"
            },
            {
                "standard_code": "2수01-04", 
                "content": "하나의 수를 두 수로 분해하고 두 수를 하나의 수로 합성하는 활동을 통하여 수 감각을 기른다.",
                "domain": "수와 연산",
                "grade": "초등 1-2학년군"
            }
        ]
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/sample_curriculum_data.json', 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    print("✅ Sample data created")

def run_quick_test():
    """Run a quick functionality test"""
    print("🧪 Running quick test...")
    
    try:
        # Test configuration loading
        sys.path.append('.')
        from config.settings import config
        print("✅ Configuration loaded")
        
        # Test data manager
        from src.data_manager import CurriculumDataProcessor
        print("✅ Data manager imported")
        
        # Test AI models (without API calls)
        from src.ai_models import AIModelManager
        manager = AIModelManager()
        print("✅ AI models initialized")
        
        print("✅ Quick test passed")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

def show_menu():
    """Show interactive menu"""
    print("\n🚀 What would you like to do?")
    print("1. Run full pipeline")
    print("2. Run specific phase")
    print("3. Start dashboard")
    print("4. Run tests")
    print("5. View logs")
    print("6. Exit")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    return choice

def run_full_pipeline():
    """Run the full pipeline"""
    print("🚀 Starting full pipeline...")
    print("⚠️  This will use AI APIs and incur costs!")
    
    confirm = input("Continue? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Pipeline cancelled")
        return
    
    try:
        result = subprocess.run([sys.executable, 'main.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Pipeline completed successfully")
            print(result.stdout)
        else:
            print("❌ Pipeline failed")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")

def run_specific_phase():
    """Run a specific phase"""
    print("\n📋 Available phases:")
    print("1. Foundation Design (Gemini 2.5 Pro)")
    print("2. Relationship Extraction (GPT-5)")
    print("3. Advanced Refinement (Claude Sonnet 4)")
    print("4. Validation & Optimization (Claude Opus 4.1)")
    
    phase_choice = input("Enter phase number (1-4): ").strip()
    
    if phase_choice in ['1', '2', '3', '4']:
        try:
            result = subprocess.run([sys.executable, 'main.py', '--phase-only', phase_choice],
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Phase {phase_choice} completed")
                print(result.stdout)
            else:
                print(f"❌ Phase {phase_choice} failed")
                print(result.stderr)
                
        except Exception as e:
            print(f"❌ Error running phase: {e}")
    else:
        print("❌ Invalid phase selection")

def start_dashboard():
    """Start the Streamlit dashboard"""
    print("🌐 Starting dashboard...")
    
    try:
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'dashboard.py'])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

def run_tests():
    """Run the test suite"""
    print("🧪 Running tests...")
    
    try:
        result = subprocess.run([sys.executable, '-m', 'pytest', 'tests/', '-v'],
                              capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
            
        if result.returncode == 0:
            print("✅ All tests passed")
        else:
            print("❌ Some tests failed")
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")

def view_logs():
    """View recent logs"""
    print("📋 Recent logs:")
    
    logs_dir = Path('logs')
    if not logs_dir.exists():
        print("❌ No logs directory found")
        return
    
    log_files = list(logs_dir.glob('*.log'))
    if not log_files:
        print("❌ No log files found")
        return
    
    # Get the most recent log file
    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
    
    print(f"📄 Showing {latest_log.name}:")
    print("-" * 50)
    
    try:
        with open(latest_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Show last 20 lines
            for line in lines[-20:]:
                print(line.rstrip())
    except Exception as e:
        print(f"❌ Error reading log file: {e}")

def main():
    """Main function"""
    print_header()
    
    # Check environment
    if not check_environment():
        print("\n🛠️  Please fix environment issues before continuing")
        return
    
    # Create sample data if needed
    if not os.path.exists('data/sample_curriculum_data.json'):
        create_sample_data()
    
    # Run quick test
    if not run_quick_test():
        print("\n⚠️  Some issues detected, but you can still continue")
    
    # Interactive menu
    while True:
        choice = show_menu()
        
        if choice == '1':
            run_full_pipeline()
        elif choice == '2':
            run_specific_phase()
        elif choice == '3':
            start_dashboard()
        elif choice == '4':
            run_tests()
        elif choice == '5':
            view_logs()
        elif choice == '6':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice, please try again")
        
        print()  # Add spacing

if __name__ == "__main__":
    main()
