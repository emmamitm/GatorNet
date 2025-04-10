#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import platform
import shutil
import re
import socket
import signal

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    """Kill the process using the specified port on Mac/Linux using lsof"""
    try:
        # For Mac/Linux
        if platform.system() != "Windows":
            # Find process using lsof command
            result = subprocess.run(
                ["lsof", "-i", f"tcp:{port}"], 
                capture_output=True, 
                text=True
            )
            
            # Parse output to get PID
            lines = result.stdout.strip().split('\n')
            if len(lines) <= 1:  # Just the header, no processes
                return False
                
            # Get PID from second line (first process entry)
            # Format is: COMMAND  PID  USER  FD  TYPE  DEVICE  SIZE/OFF  NODE  NAME
            parts = lines[1].split()
            if len(parts) < 2:
                return False
                
            pid = parts[1]
            
            # Kill the process
            print(f"Killing process {pid} using port {port}")
            os.kill(int(pid), signal.SIGTERM)
            time.sleep(1)  # Give it time to die
            
            # Check if it worked
            return not is_port_in_use(port)
        else:
            # Windows - use netstat and taskkill
            result = subprocess.run(
                ["netstat", "-ano", "|", "findstr", f":{port}"],
                shell=True,
                capture_output=True,
                text=True
            )
            lines = result.stdout.strip().split('\n')
            if not lines or not lines[0].strip():
                return False
                
            # Try to extract PID
            for line in lines:
                if f":{port}" in line:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        subprocess.run(["taskkill", "/F", "/PID", pid], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
                        time.sleep(1)
                        return not is_port_in_use(port)
                        
            return False
    except:
        return False

def create_virtual_environment():
    """Create a virtual environment for the application"""
    print("Setting up virtual environment...")
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        try:
            # Try to use python3 first
            subprocess.run(["python3", "-m", "venv", "venv"], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Fall back to just 'python'
                subprocess.run(["python", "-m", "venv", "venv"], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("✗ Error: Failed to create virtual environment.")
                print("Please make sure you have Python 3.10+ installed.")
                sys.exit(1)
                
    # Verify the virtual environment was created and find Python executable
    python_candidates = [
        os.path.join("venv", "bin", "python3"),
        os.path.join("venv", "bin", "python"),
        os.path.join("venv", "Scripts", "python.exe")
    ]
    
    venv_python = None
    for path in python_candidates:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            venv_python = abs_path
            print(f"✓ Found Python in virtual environment: {venv_python}")
            break
    
    if not venv_python:
        print("✗ Error: Virtual environment exists but Python executable not found.")
        sys.exit(1)
        
    return venv_python

def get_venv_pip(venv_python):
    """Get the pip executable from the virtual environment"""
    # Try several possible locations for pip
    pip_candidates = [
        os.path.join(os.path.dirname(venv_python), "pip3"),
        os.path.join(os.path.dirname(venv_python), "pip"),
        os.path.join(os.path.dirname(venv_python), "pip.exe")
    ]
    
    pip_exe = None
    for path in pip_candidates:
        if os.path.exists(path):
            pip_exe = path
            print(f"✓ Found pip in virtual environment: {pip_exe}")
            break
    
    if not pip_exe:
        print("Installing pip in virtual environment...")
        try:
            subprocess.run([venv_python, "-m", "ensurepip", "--upgrade"], check=True)
            
            # Check again for pip
            for path in pip_candidates:
                if os.path.exists(path):
                    pip_exe = path
                    print(f"✓ Installed pip in virtual environment: {pip_exe}")
                    break
                    
            # If still not found, use "python -m pip" approach
            if not pip_exe:
                print("Using 'python -m pip' as pip executable")
                return f"{venv_python} -m pip"
        except subprocess.CalledProcessError:
            print("✗ Error: Failed to install pip in virtual environment.")
            print("Using 'python -m pip' as fallback")
            return f"{venv_python} -m pip"
    
    return pip_exe

def run_pip_command(pip_exe, args):
    """Run a pip command, handling both string and path formats for pip"""
    if " -m pip" in pip_exe:
        # If we're using "python -m pip" format
        python_exe, rest = pip_exe.split(" -m pip")
        full_command = [python_exe, "-m", "pip"] + args
        subprocess.run(full_command, check=True)
    else:
        # Regular pip executable
        subprocess.run([pip_exe] + args, check=True)

def setup_ai_environment(venv_python, pip_exe):
    """Set up AI environment with all required dependencies for new AI model"""
    print("Setting up AI environment...")
    
    # First update pip itself
    print("Upgrading pip...")
    try:
        run_pip_command(pip_exe, ["install", "--upgrade", "pip"])
    except subprocess.CalledProcessError:
        print("Warning: Failed to upgrade pip, continuing anyway")
    
    # Install basic requirements
    print("Installing backend dependencies...")
    backend_packages = ["flask", "flask-cors", "flask-sqlalchemy", "PyJWT", "werkzeug"]
    for package in backend_packages:
        print(f"Installing {package}...")
        try:
            run_pip_command(pip_exe, ["install", package])
        except subprocess.CalledProcessError:
            print(f"Warning: Failed to install {package}")
    
    # Install AI requirements
    print("Installing AI requirements...")
    if os.path.exists("AI/requirements.txt"):
        try:
            run_pip_command(pip_exe, ["install", "-r", os.path.abspath("AI/requirements.txt")])
        except subprocess.CalledProcessError:
            print("Warning: Failed to install from requirements.txt")
    
    # Install specific requirements for the new AI
    required_packages = [
        "llama-cpp-python",  # For LLaMA 3 model
        "torch",
        "sentence-transformers",
        "scikit-learn",
        "spacy",
        "fuzzywuzzy",
        "python-Levenshtein",  # For faster fuzzy matching
        "hnswlib",
        "diskcache",
        "numpy",
        "pandas",
        "hydra-core",  # For hydra and omegaconf
        "loguru"       # For enhanced logging
    ]
    
    for package in required_packages:
        print(f"Installing {package}...")
        try:
            run_pip_command(pip_exe, ["install", package])
        except subprocess.CalledProcessError:
            print(f"Warning: Failed to install {package}, continuing anyway")
    
    # Download spaCy model if not present
    print("Installing spaCy English model...")
    try:
        subprocess.run([venv_python, "-m", "spacy", "download", "en_core_web_sm"], check=True)
    except subprocess.CalledProcessError:
        print("Warning: Failed to download spaCy model, some NLP features may be limited")
    
    # Create AI directories
    if not os.path.exists("chatbot/backend/AI"):
        os.makedirs("chatbot/backend/AI")
    
    if not os.path.exists("chatbot/backend/AI/__init__.py"):
        with open("chatbot/backend/AI/__init__.py", "w") as f:
            f.write("# AI package for backend\n")
    
    # Create models directory
    if not os.path.exists("chatbot/backend/AI/models"):
        os.makedirs("chatbot/backend/AI/models")
    
    # Copy AI model to backend
    print("Copying AI model to backend...")
    try:
        shutil.copy2("AI/AI_model.py", "chatbot/backend/AI/AI_model.py")
    except Exception as e:
        print(f"Warning: Could not copy AI model: {e}")
        try:
            with open("AI/AI_model.py", "r") as src:
                content = src.read()
                with open("chatbot/backend/AI/AI_model.py", "w") as dst:
                    dst.write(content)
        except Exception as e:
            print(f"Critical error: Could not copy AI model: {e}")
            sys.exit(1)
    
    # Copy model files if they exist
    if os.path.exists("AI/models"):
        print("Copying model files to backend...")
        os.makedirs("chatbot/backend/AI/models", exist_ok=True)
        model_files = os.listdir("AI/models")
        for model_file in model_files:
            source = os.path.join("AI/models", model_file)
            destination = os.path.join("chatbot/backend/AI/models", model_file)
            try:
                if os.path.isfile(source):
                    shutil.copy2(source, destination)
                    print(f"Copied {model_file}")
            except Exception as e:
                print(f"Warning: Could not copy model file {model_file}: {e}")
    
    print("✓ AI setup complete")

def run_backend(venv_python, port=5001):
    """Start the Flask backend server with Python from virtual environment"""
    print("\nStarting backend server...")
    backend_path = os.path.join(os.getcwd(), "chatbot/backend")
    
    # Check if port is in use
    if is_port_in_use(port):
        print(f"Warning: Port {port} is already in use")
        # Try to kill the process
        if kill_process_on_port(port):
            print(f"Successfully freed port {port}")
        else:
            # Find an available port
            for new_port in range(5002, 5010):
                if not is_port_in_use(new_port):
                    print(f"Using alternate port {new_port}")
                    port = new_port
                    break
            else:
                print("✗ Error: Could not find an available port")
                sys.exit(1)
    
    # Make sure database directory exists
    os.makedirs(os.path.join(backend_path, "instance"), exist_ok=True)
    
    # Skip preloading - it seems to be causing issues
    print("Starting backend directly (skipping preload)...")
    
    # Use absolute path for Python executable
    abs_venv_python = os.path.abspath(venv_python)
    
    # Create a simple env file for the backend
    env_file = os.path.join(backend_path, ".env")
    with open(env_file, "w") as f:
        f.write(f"PORT={port}\n")
    
    # Start the server
    print(f"Running backend with: {abs_venv_python}")
    # Pass port to app.py
    return subprocess.Popen([abs_venv_python, "app.py", "--port", str(port)], cwd=backend_path)

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

def run_frontend(backend_port=5001):
    """Start the React frontend development server"""
    print("Starting frontend server...")
    frontend_path = os.path.join(os.getcwd(), "chatbot/frontend")
    
    # Create/update .env file with the backend port
    env_path = os.path.join(frontend_path, ".env.local")
    with open(env_path, "w") as f:
        f.write(f"REACT_APP_API_URL=http://localhost:{backend_port}\n")
    
    if platform.system() == "Windows":
        return subprocess.Popen("npm start", shell=True, cwd=frontend_path)
    else:
        return subprocess.Popen(["npm", "start"], cwd=frontend_path)

def main():
    # Check if we're on a supported platform
    if platform.system() == "Windows":
        print("✗ This script is for Mac/Linux. Please use run_windows.py instead.")
        sys.exit(1)
        
    # Check if we're in the right directory
    if not os.path.exists("chatbot/frontend") or not os.path.exists("chatbot/backend") or not os.path.exists("AI"):
        print("✗ Error: Please run this script from the project root directory")
        print("Expected structure:")
        print("  ./chatbot/frontend/")
        print("  ./chatbot/backend/")
        print("  ./AI/")
        print("  ./run.py")
        sys.exit(1)

    print(f"Setting up chatbot application for {platform.system()}...\n")

    # Create a virtual environment first
    venv_python = create_virtual_environment()
    pip_exe = get_venv_pip(venv_python)
    
    # Check Node.js dependencies
    print("Checking dependencies...")
    check_node()
    
    # Set up AI environment using the virtual environment
    setup_ai_environment(venv_python, pip_exe)

    # Install frontend dependencies
    install_frontend_dependencies()

    # Kill any existing processes on port 5001
    backend_port = 5001
    if is_port_in_use(backend_port):
        print(f"Port {backend_port} is in use. Attempting to free it...")
        if not kill_process_on_port(backend_port):
            # If we couldn't kill it, find another port
            for new_port in range(5002, 5010):
                if not is_port_in_use(new_port):
                    backend_port = new_port
                    print(f"Using alternate port {backend_port}")
                    break
            else:
                print("✗ Error: Could not find an available port")
                sys.exit(1)

    # Start servers
    backend_process = run_backend(venv_python, backend_port)
    time.sleep(2)  # Give backend a moment to start
    frontend_process = run_frontend(backend_port)

    print("\nBoth servers are starting up...")
    print("\nYou can access the application at:")
    print("→ Frontend (Chat Interface): http://localhost:3000")
    print(f"→ Backend API: http://localhost:{backend_port}")

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