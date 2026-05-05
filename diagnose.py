"""MiMo TTS Studio - Diagnose tool. Run: python diagnose.py"""
import sys
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))

print("=" * 44)
print("   MiMo TTS Studio - Diagnose")
print("=" * 44)
print()

# 1. Python
print(f"[1] Python: {sys.version}")
if sys.version_info < (3, 9):
    print("    [WARN] Python 3.9+ recommended")
print()

# 2. pip
print("[2] pip:")
r = subprocess.run([sys.executable, "-m", "pip", "--version"],
                    capture_output=True, text=True)
print(f"    {r.stdout.strip() if r.returncode == 0 else 'NOT FOUND'}")
print()

# 3. Node.js
print("[3] Node.js:")
node = shutil.which("node")
if node:
    r = subprocess.run(["node", "--version"], capture_output=True, text=True)
    print(f"    {r.stdout.strip()}")
else:
    print("    NOT FOUND")
npm = shutil.which("npm")
if npm:
    r = subprocess.run(["npm", "--version"], capture_output=True, text=True)
    print(f"    npm {r.stdout.strip()}")
print()

# 4. Project files
print("[4] Project files:")
files = [
    "run.py", "requirements.txt", "start.py",
    "backend/__init__.py", "backend/main.py", "backend/config.py",
    "backend/database.py", "backend/models.py",
    "backend/routers/__init__.py", "backend/routers/synthesize.py",
    "backend/routers/voices.py", "backend/routers/history.py",
    "backend/routers/settings.py",
    "backend/services/__init__.py", "backend/services/tts_client.py",
    "backend/services/audio_processor.py",
    "frontend/package.json", "frontend/vite.config.js", "frontend/index.html",
    "frontend/src/main.js", "frontend/src/App.vue",
]
for f in files:
    exists = os.path.exists(os.path.join(ROOT, f))
    status = "[OK]" if exists else "[MISSING]"
    print(f"    {status} {f}")
print()

# 5. Python dependencies
print("[5] Python dependencies:")
deps = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("httpx", "httpx"),
    ("pydantic", "pydantic"),
    ("pydantic_settings", "pydantic-settings"),
    ("aiosqlite", "aiosqlite"),
]
for mod, pip_name in deps:
    try:
        __import__(mod)
        print(f"    [OK] {pip_name}")
    except ImportError:
        print(f"    [MISSING] {pip_name}  ->  pip install {pip_name}")

# pywebview is optional for dev mode
try:
    import webview  # noqa: F401
    print("    [OK] pywebview (desktop mode)")
except ImportError:
    print("    [SKIP] pywebview not installed (desktop mode unavailable, dev mode OK)")
print()

# 6. Test import
print("[6] Testing backend import:")
try:
    os.chdir(ROOT)
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from backend.main import app  # noqa: F401
    print("    [OK] backend.main imported successfully")
except Exception as e:
    print(f"    [FAIL] {e}")
    import traceback
    traceback.print_exc()
print()

# 7. Data directory
print("[7] Data directory:")
data_dir = os.path.join(ROOT, "data")
if os.path.isdir(data_dir):
    for sub in ["audio", "preview", "logs"]:
        p = os.path.join(data_dir, sub)
        print(f"    {'[OK]' if os.path.isdir(p) else '[MISSING]'} data/{sub}")
else:
    print("    [INFO] data/ does not exist (will be created on start)")

print()
print("=" * 44)
print("   Diagnose complete")
print("=" * 44)
input("\nPress Enter to exit...")
