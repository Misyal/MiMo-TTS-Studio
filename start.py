"""MiMo TTS Studio - One-click launcher.
Checks dependencies, starts backend + frontend.

Usage:
    python start.py          # dev mode (frontend dev server + backend)
    python start.py --prod   # prod mode (build frontend, serve from backend)
"""
import subprocess
import sys
import os
import time
import shutil
import signal
import atexit
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
PROD_MODE = "--prod" in sys.argv

# Global refs for cleanup
_backend_proc = None
_frontend_proc = None
_log_file = None


def _assign_to_job_object(proc):
    """On Windows, assign process to a Job Object so it auto-dies with parent."""
    if sys.platform != "win32" or proc is None:
        return
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        job = kernel32.CreateJobObjectW(None, None)

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.POINTER(wintypes.ULONG)),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        kernel32.SetInformationJobObject(
            job, 9, ctypes.byref(info), ctypes.sizeof(info)
        )

        handle = kernel32.OpenProcess(0x1F0FFF, False, proc.pid)
        if handle:
            kernel32.AssignProcessToJobObject(job, handle)
            kernel32.CloseHandle(handle)
    except Exception:
        pass


def _kill_proc_tree(proc):
    """Force-kill a process and all its children (Windows-safe)."""
    if proc is None:
        return
    try:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _cleanup():
    """Kill backend + frontend processes on exit."""
    _kill_proc_tree(_backend_proc)
    _kill_proc_tree(_frontend_proc)
    if _log_file:
        try:
            _log_file.close()
        except Exception:
            pass


atexit.register(_cleanup)


def _signal_handler(sig, frame):
    _cleanup()
    sys.exit(0)


for _sig in (signal.SIGTERM, signal.SIGINT):
    try:
        signal.signal(_sig, _signal_handler)
    except (OSError, ValueError):
        pass


def check_python():
    v = sys.version_info
    if v < (3, 9):
        print(f"[ERROR] Python 3.9+ required, found {v.major}.{v.minor}")
        sys.exit(1)
    print(f"[OK] Python {v.major}.{v.minor}.{v.micro}")


NPM_CMD = "npm"


def check_node():
    global NPM_CMD

    if shutil.which("node") is None:
        print("[ERROR] Node.js not found.")
        print("       Install from https://nodejs.org/")
        sys.exit(1)
    r = subprocess.run(["node", "--version"], capture_output=True, text=True)
    print(f"[OK] Node.js {r.stdout.strip()}")

    npm_path = shutil.which("npm")
    if npm_path is None:
        candidates = [
            os.path.join(os.environ.get("PROGRAMFILES", ""), "nodejs", "npm.cmd"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "nodejs", "npm.cmd"),
            os.path.join(os.environ.get("APPDATA", ""), "npm", "npm.cmd"),
            os.path.expanduser(r"~\AppData\Roaming\npm\npm.cmd"),
            os.path.expanduser(r"~\AppData\Local\Programs\node\npm.cmd"),
        ]
        for c in candidates:
            if c and os.path.isfile(c):
                npm_path = c
                break

    if npm_path is None:
        print("[ERROR] npm not found.")
        print("       Reinstall Node.js from https://nodejs.org/")
        sys.exit(1)

    NPM_CMD = npm_path
    r = subprocess.run([npm_path, "--version"], capture_output=True, text=True)
    print(f"[OK] npm {r.stdout.strip()} (at {npm_path})")


def install_pip_deps():
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
        import httpx  # noqa: F401
        import pydantic  # noqa: F401
        import aiosqlite  # noqa: F401
        print("[OK] Python dependencies installed")
    except ImportError as e:
        print(f"[INFO] Missing: {e} - installing...")
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r",
             os.path.join(ROOT, "requirements.txt")],
            cwd=ROOT
        )
        if r.returncode != 0:
            print("[ERROR] Failed to install Python dependencies")
            sys.exit(1)


def install_npm_deps():
    node_modules = os.path.join(ROOT, "frontend", "node_modules")
    if os.path.isdir(node_modules):
        print("[OK] Frontend dependencies installed")
        return
    print("[INFO] Installing frontend dependencies (first time, please wait)...")
    r = subprocess.run([NPM_CMD, "install"], cwd=os.path.join(ROOT, "frontend"))
    if r.returncode != 0:
        print("[ERROR] Failed to install frontend dependencies")
        sys.exit(1)


def create_data_dirs():
    for d in ["data/audio", "data/preview", "data/logs"]:
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    print("[OK] Data directories ready")


def build_frontend():
    print("[INFO] Building frontend...")
    r = subprocess.run([NPM_CMD, "run", "build"], cwd=os.path.join(ROOT, "frontend"))
    if r.returncode != 0:
        print("[ERROR] Frontend build failed")
        sys.exit(1)
    print("[OK] Frontend built")


def start_backend():
    global _backend_proc, _log_file
    log_path = os.path.join(ROOT, "data", "logs", "backend.log")
    log_file = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=ROOT,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    _backend_proc = proc
    _log_file = log_file
    _assign_to_job_object(proc)
    return proc, log_file, log_path


def wait_for_backend(timeout=10):
    for _ in range(timeout * 2):
        try:
            urllib.request.urlopen("http://127.0.0.1:18700/api/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    global _frontend_proc

    mode = "Production" if PROD_MODE else "Development"
    print()
    print("=" * 44)
    print(f"   MiMo TTS Studio ({mode})")
    print("=" * 44)
    print()

    print("[1/5] Checking Python...")
    check_python()
    print("[2/5] Checking Node.js...")
    check_node()

    print("[3/5] Checking dependencies...")
    install_pip_deps()
    install_npm_deps()

    print("[4/5] Preparing data directories...")
    create_data_dirs()

    if PROD_MODE:
        build_frontend()

    print("[5/5] Starting services...")
    print()

    backend_proc, log_file, log_path = start_backend()
    print(f"  Backend PID: {backend_proc.pid}  Log: {log_path}")
    print("  Waiting for backend...")

    if wait_for_backend():
        print("  Backend is ready!")
    else:
        if backend_proc.poll() is not None:
            print(f"\n  [ERROR] Backend crashed (exit code {backend_proc.returncode})")
            print(f"  Log file: {log_path}")
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f.readlines()[-20:]:
                        print(f"  | {line.rstrip()}")
            except Exception:
                pass
            sys.exit(1)
        print("  [WARN] Backend may still be starting...")

    print()

    if PROD_MODE:
        print("=" * 44)
        print("  Open: http://127.0.0.1:18700")
        print("  Press Ctrl+C to stop")
        print("=" * 44)
        print()
        try:
            backend_proc.wait()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            _cleanup()
            print("Done.")
    else:
        print("=" * 44)
        print("  Backend:  http://127.0.0.1:18700")
        print("  Frontend: http://localhost:5173")
        print("  Press Ctrl+C to stop")
        print("=" * 44)
        print()

        _frontend_proc = subprocess.Popen(
            [NPM_CMD, "run", "dev"],
            cwd=os.path.join(ROOT, "frontend"),
        )

        try:
            _frontend_proc.wait()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            _cleanup()
            print("Done.")


if __name__ == "__main__":
    main()
