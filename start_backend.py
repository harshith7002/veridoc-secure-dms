import subprocess
import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))

services = [
    ("audit-ledger-service", [os.path.join(base_dir, "audit-ledger-service", "venv", "Scripts", "python.exe"), "-m", "uvicorn", "main:app", "--port", "8010"]),
    ("identity-service", [os.path.join(base_dir, "identity-service", "venv", "Scripts", "python.exe"), "-m", "uvicorn", "main:app", "--port", "8011"]),
    ("documents-service", [os.path.join(base_dir, "documents-service", "venv", "Scripts", "python.exe"), "-m", "uvicorn", "main:app", "--port", "8012"]),
    ("search-service", [os.path.join(base_dir, "search-service", "venv", "Scripts", "python.exe"), "-m", "uvicorn", "main:app", "--port", "8013"]),
    ("cases-service", [os.path.join(base_dir, "cases-service", "venv", "Scripts", "python.exe"), "-m", "uvicorn", "main:app", "--port", "8014"]),
    ("gateway", [os.path.join(base_dir, "gateway", "venv", "Scripts", "python.exe"), "-m", "uvicorn", "main:app", "--port", "8000"]),
]

procs = []
for name, cmd in services:
    service_cwd = os.path.join(base_dir, name)
    print(f"Starting {name} on {cmd[-1]}...")
    p = subprocess.Popen(cmd, cwd=service_cwd)
    procs.append(p)

print("All 6 backend microservices are up and running.")
try:
    for p in procs:
        p.wait()
except Exception:
    for p in procs:
        p.terminate()
