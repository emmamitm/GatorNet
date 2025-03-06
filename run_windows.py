#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import platform
import shutil

def setup_ai_environment():
    """Set up AI environment and load models (Windows version)"""
    print("Setting up AI environment...")
    
    # Create venv if not exists and install requirements
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    # Determine the correct pip path
    pip_path = os.path.join("venv", "Scripts", "pip")
    
    # Install AI requirements
    print("Installing AI requirements...")
    if os.path.exists("AI/requirements.txt"):
        subprocess.run([pip_path, "install", "-r", "AI/requirements.txt"], check=True)
    else:
        print("Warning: AI/requirements.txt not found, skipping AI requirements installation")
    
    # Create directory if it doesn't exist
    if not os.path.exists("chatbot/backend/AI"):
        os.makedirs("chatbot/backend/AI")
    
    if not os.path.exists("chatbot/backend/AI/__init__.py"):
        with open("chatbot/backend/AI/__init__.py", "w") as f:
            f.write("# AI package for backend\n")
    
    # Copy AI model to backend if it exists
    if os.path.exists("AI/AI_model.py"):
        print("Copying AI model to backend...")
        with open("AI/AI_model.py", "r") as src:
            content = src.read()
            with open("chatbot/backend/AI/AI_model.py", "w") as dst:
                dst.write(content)
        print("✓ AI model copied successfully")
    else:
        print("Warning: AI/AI_model.py not found, skipping copy operation")
    
    print("✓ AI setup complete")

def check_python_dependencies():
    """Install required Python packages"""
    required_packages = ["flask", "flask-cors", "flask-sqlalchemy", "PyJWT", "werkzeug"]

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package} already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ {package} installed successfully")


def check_node():
    """Check if Node.js and npm are installed and return npm command"""
    try:
        # First check if node is available
        node_version = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, check=True
        ).stdout.strip()
        
        # Try different npm command variations
        npm_cmds = ["npm", "npm.cmd"]
        npm_cmd = None
        npm_version = None
        
        for cmd in npm_cmds:
            try:
                npm_version = subprocess.run(
                    [cmd, "--version"], capture_output=True, text=True, check=True
                ).stdout.strip()
                npm_cmd = cmd
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        if npm_cmd is None:
            print("✗ npm command not found. Node.js is installed but npm is not accessible.")
            print("Please ensure npm is in your PATH or reinstall Node.js from https://nodejs.org/")
            sys.exit(1)
            
        print(f"✓ Node.js {node_version} detected")
        print(f"✓ npm {npm_version} detected (using command: {npm_cmd})")
        return npm_cmd
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Node.js and npm are required but not found.")
        print("Please install Node.js from https://nodejs.org/")
        sys.exit(1)


def install_frontend_dependencies(npm_cmd):
    """Install frontend npm dependencies"""
    frontend_path = os.path.join(os.getcwd(), "chatbot", "frontend")
    
    if not os.path.exists(frontend_path):
        print(f"✗ Error: Frontend directory not found at {frontend_path}")
        sys.exit(1)
        
    os.chdir(frontend_path)
    print(f"\nInstalling frontend dependencies in {frontend_path}...")
    
    try:
        print(f"Running '{npm_cmd} install'...")
        subprocess.run([npm_cmd, "install"], check=True)
        print("✓ Frontend dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing frontend dependencies: {e}")
        sys.exit(1)
    finally:
        os.chdir("../..")


def run_backend():
    """Start the Flask backend server"""
    print("\nStarting backend server...")
    backend_path = os.path.join(os.getcwd(), "chatbot", "backend")
    
    if not os.path.exists(backend_path):
        print(f"✗ Error: Backend directory not found at {backend_path}")
        sys.exit(1)
    
    if not os.path.exists(os.path.join(backend_path, "app.py")):
        print(f"✗ Error: app.py not found in {backend_path}")
        sys.exit(1)
    
    # Use the venv python for backend on Windows
    python_path = os.path.join("../..", "venv", "Scripts", "python")
    if not os.path.exists(os.path.normpath(os.path.join(backend_path, python_path))):
        print(f"Warning: Virtual environment python not found at {python_path}")
        print("Falling back to system Python")
        python_path = sys.executable
    
    return subprocess.Popen([python_path, "app.py"], cwd=backend_path)


def run_frontend(npm_cmd):
    """Start the React frontend development server"""
    print("Starting frontend server...")
    frontend_path = os.path.join(os.getcwd(), "chatbot", "frontend")
    
    if not os.path.exists(frontend_path):
        print(f"✗ Error: Frontend directory not found at {frontend_path}")
        sys.exit(1)
    
    return subprocess.Popen([npm_cmd, "start"], cwd=frontend_path)


def main():
    # Make sure we're on Windows
    if platform.system() != "Windows":
        print("✗ Error: This script is for Windows only.")
        print("Please use run.py for Mac/Linux systems.")
        sys.exit(1)

    # Check if we're in the right directory
    expected_dirs = ["chatbot/frontend", "chatbot/backend", "AI"]
    missing_dirs = [d for d in expected_dirs if not os.path.exists(d)]
    
    if missing_dirs:
        print("✗ Error: Please run this script from the project root directory")
        print("Expected structure:")
        print("  ./chatbot/frontend/")
        print("  ./chatbot/backend/")
        print("  ./AI/")
        print("  ./run_windows.py")
        print("\nMissing directories:", ", ".join(missing_dirs))
        sys.exit(1)

    print("Setting up chatbot application for Windows...\n")

    # Check dependencies
    print("Checking dependencies...")
    npm_cmd = check_node()
    check_python_dependencies()
    
    # Set up AI environment for Windows
    setup_ai_environment()

    # Install frontend dependencies
    install_frontend_dependencies(npm_cmd)

    # Start servers
    backend_process = run_backend()
    time.sleep(2)  # Give backend a moment to start
    frontend_process = run_frontend(npm_cmd)

    print("\nBoth servers are starting up...")
    print("\nYou can access the application at:")
    print("→ Frontend (Chat Interface): http://localhost:3000")
    print("→ Backend API: http://localhost:5001")

    print("\nPress Ctrl+C to stop all servers.")

    try:
        while True:
            # Check if either process has crashed
            if backend_process.poll() is not None:
                print("\n✗ Error: Backend server stopped unexpectedly!")
                frontend_process.terminate()
                sys.exit(1)

            if frontend_process.poll() is not None:
                print("\n✗ Error: Frontend server stopped unexpectedly!")
                backend_process.terminate()
                sys.exit(1)

            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✓ Servers stopped successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()