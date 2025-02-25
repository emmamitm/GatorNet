#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import platform

def setup_ai_environment():
    """Set up AI environment and load models (Windows version)"""
    print("Setting up AI environment...")
    
    # Create venv if not exists and install requirements
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    # Install AI requirements
    print("Installing AI requirements...")
    subprocess.run([os.path.join("venv", "Scripts", "pip"), "install", "-r", "AI/requirements.txt"], check=True)
    
    # Copy AI_model.py to backend/AI folder
    if not os.path.exists("chatbot/backend/AI"):
        os.makedirs("chatbot/backend/AI")
    
    if not os.path.exists("chatbot/backend/AI/__init__.py"):
        with open("chatbot/backend/AI/__init__.py", "w") as f:
            f.write("# AI package for backend\n")
    
    print("Copying AI model to backend...")
    with open("AI/AI_model.py", "r") as src:
        content = src.read()
        with open("chatbot/backend/AI/AI_model.py", "w") as dst:
            dst.write(content)
    
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
    """Check if Node.js and npm are installed"""
    try:
        node_version = subprocess.run(
            ["node", "--version"], capture_output=True, text=True
        ).stdout.strip()
        npm_version = ""
        try:
            npm_version = subprocess.run(
                ["npm.cmd", "--version"], capture_output=True, text=True
            ).stdout.strip()
        except:
            npm_version = subprocess.run(
                ["npm", "--version"], capture_output=True, text=True
            ).stdout.strip()
        print(f"✓ Node.js {node_version} detected")
        print(f"✓ npm {npm_version} detected")
        return True
    except FileNotFoundError:
        print("✗ Node.js and npm are required but not found.")
        print("Please install Node.js from https://nodejs.org/")
        sys.exit(1)


def install_frontend_dependencies():
    """Install frontend npm dependencies"""
    os.chdir("chatbot/frontend")
    print("\nInstalling frontend dependencies...")
    try:
        subprocess.run(["npm", "install"], check=True)
        print("✓ Frontend dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing frontend dependencies: {e}")
        sys.exit(1)
    finally:
        os.chdir("../..")


def run_backend():
    """Start the Flask backend server"""
    print("\nStarting backend server...")
    backend_path = os.path.join(os.getcwd(), "chatbot/backend")
    
    # Use the venv python for backend on Windows
    return subprocess.Popen([os.path.join("../..", "venv", "Scripts", "python"), "app.py"], cwd=backend_path)


def run_frontend():
    """Start the React frontend development server"""
    print("Starting frontend server...")
    frontend_path = os.path.join(os.getcwd(), "chatbot/frontend")
    return subprocess.Popen("npm start", shell=True, cwd=frontend_path)


def main():
    # Make sure we're on Windows
    if platform.system() != "Windows":
        print("✗ Error: This script is for Windows only.")
        print("Please use run.py for Mac/Linux systems.")
        sys.exit(1)

    # Check if we're in the right directory
    if not os.path.exists("chatbot/frontend") or not os.path.exists("chatbot/backend") or not os.path.exists("AI"):
        print("✗ Error: Please run this script from the project root directory")
        print("Expected structure:")
        print("  ./chatbot/frontend/")
        print("  ./chatbot/backend/")
        print("  ./AI/")
        print("  ./run_windows.py")
        sys.exit(1)

    print("Setting up chatbot application for Windows...\n")

    # Check dependencies
    print("Checking dependencies...")
    check_node()
    check_python_dependencies()
    
    # Set up AI environment for Windows
    setup_ai_environment()

    # Install frontend dependencies
    install_frontend_dependencies()

    # Start servers
    backend_process = run_backend()
    time.sleep(2)  # Give backend a moment to start
    frontend_process = run_frontend()

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