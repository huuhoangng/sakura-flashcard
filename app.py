import subprocess
import os
import sys
import time

def main():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    BACKEND_DIR = os.path.join(BASE_DIR, "demo1")
    FRONTEND_DIR = os.path.join(BASE_DIR, "demo1-front")

    # 3. Verify the directories exist to prevent path bugs
    if not os.path.exists(BACKEND_DIR):
        print(f"Error: Backend directory not found at {BACKEND_DIR}")
        sys.exit(1)
    if not os.path.exists(FRONTEND_DIR):
        print(f"Error: Frontend directory not found at {FRONTEND_DIR}")
        sys.exit(1)

    print("Starting Backend (Flask) and Frontend (Reflex)...")
    print("-" * 50)

    backend_cmd = [sys.executable, "app.py"] 
    print(f"Starting Backend in: {BACKEND_DIR}")
    backend_process = subprocess.Popen(backend_cmd, cwd=BACKEND_DIR)

    time.sleep(2)

    frontend_cmd = [sys.executable, "-m", "reflex", "run"]
    print(f"Starting Frontend in: {FRONTEND_DIR}")
    frontend_process = subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR)

    print("-" * 50)
    print("Both services are running. Press Ctrl+C to stop both.")

    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down services...")
        backend_process.terminate()
        frontend_process.terminate()
        
        backend_process.wait()
        frontend_process.wait()
        print("Services stopped successfully.")

if __name__ == "__main__":
    main()