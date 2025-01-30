#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import webbrowser


def check_python_dependencies():
    """Install required Python packages"""
    required_packages = ['flask', 'flask-cors']

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} already installed")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ {package} installed successfully")


def check_node():
    """Check if Node.js and npm are installed"""
    try:
        node_version = subprocess.run(
            ['node', '--version'], capture_output=True, text=True).stdout.strip()
        npm_version = subprocess.run(
            ['npm.cmd', '--version'], capture_output=True, text=True).stdout.strip()
        print(f"✓ Node.js {node_version} detected")
        print(f"✓ npm {npm_version} detected")
        return True
    except FileNotFoundError:
        print("✗ Node.js and npm are required but not found.")
        print("Please install Node.js from https://nodejs.org/")
        sys.exit(1)


def install_frontend_dependencies():
    """Install frontend npm dependencies"""
    os.chdir('frontend')
    print("\nInstalling frontend dependencies...")
    try:
        subprocess.run(['npm.cmd', 'install'], check=True, shell=True)
        print("✓ Frontend dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing frontend dependencies: {e}")
        sys.exit(1)
    finally:
        os.chdir('..')


def run_backend():
    """Start the Flask backend server"""
    print("\nStarting backend server...")
    backend_path = os.path.join(os.getcwd(), 'backend')
    return subprocess.Popen([sys.executable, 'app.py'], cwd=backend_path)


def run_frontend():
    """Start the React frontend development server"""
    print("Starting frontend server...")
    frontend_path = os.path.join(os.getcwd(), 'frontend')
    return subprocess.Popen('npm start', shell=True, cwd=frontend_path)


def main():
    if not os.path.exists('frontend') or not os.path.exists('backend'):
        print("✗ Error: Please run this script from the project root directory")
        sys.exit(1)

    print("Setting up chatbot application...\n")

    check_node()
    check_python_dependencies()

    install_frontend_dependencies()

    backend_process = run_backend()
    time.sleep(2)
    frontend_process = run_frontend()

    print("\nApplication is launching at:\n→ Frontend: http://localhost:3000\n→ Backend API: http://localhost:5001")

    time.sleep(3)
    webbrowser.open('http://localhost:3000')

    print("\nPress Ctrl+C to stop all servers.")

    try:
        while True:
            if backend_process.poll() is not None:
                print("\n✗ Backend server stopped unexpectedly!")
                frontend_process.terminate()
                sys.exit(1)
            if frontend_process.poll() is not None:
                print("\n✗ Frontend server stopped unexpectedly!")
                backend_process.terminate()
                sys.exit(1)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✓ Servers stopped successfully")
        sys.exit(0)


if __name__ == '__main__':
    main()
