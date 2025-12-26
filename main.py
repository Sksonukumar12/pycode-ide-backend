from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import subprocess
import os
import time
import uuid

app = FastAPI()

# =========================
# CONFIG
# =========================
BASE_DIR = os.getenv("PYCODE_BASE_DIR", "/tmp/pycode_users")
DEFAULT_EXEC_TIMEOUT = int(os.getenv("PYCODE_EXEC_TIMEOUT", "5"))
DEFAULT_INSTALL_TIMEOUT = int(os.getenv("PYCODE_INSTALL_TIMEOUT", "30"))

os.makedirs(BASE_DIR, exist_ok=True)

# =========================
# MODELS
# =========================
class RunRequest(BaseModel):
    user_id: str
    code: str
    timeout: int | None = None


class InstallRequest(BaseModel):
    user_id: str
    package: str
    timeout: int | None = None


class UninstallRequest(BaseModel):
    user_id: str
    package: str
    timeout: int | None = None


class LibsRequest(BaseModel):
    user_id: str


# =========================
# SECURITY
# =========================
PROTECTED_PACKAGES = {"pip", "setuptools", "wheel"}

# =========================
# UTIL
# =========================
def get_user_env(user_id: str):
    safe_user = "".join(c for c in user_id if c.isalnum() or c in "_-")
    user_dir = os.path.join(BASE_DIR, safe_user)
    venv_dir = os.path.join(user_dir, "venv")

    if not os.path.exists(venv_dir):
        os.makedirs(user_dir, exist_ok=True)
        subprocess.run(["python3", "-m", "venv", venv_dir], check=True)

    python_path = os.path.join(venv_dir, "bin", "python")
    pip_path = os.path.join(venv_dir, "bin", "pip")

    return python_path, pip_path, user_dir


# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"status": "running"}


# =========================
# INSTALL
# =========================
@app.post("/install")
def install_package(req: InstallRequest):
    _, pip_path, _ = get_user_env(req.user_id)
    timeout = req.timeout or DEFAULT_INSTALL_TIMEOUT

    try:
        r = subprocess.run(
            [pip_path, "install", req.package],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {"success": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}

    except subprocess.TimeoutExpired:
        return {"success": False, "stderr": "Installation timed out"}


# =========================
# UNINSTALL
# =========================
@app.post("/uninstall")
def uninstall_package(req: UninstallRequest):

    pkg = req.package.strip().lower()

    if pkg in PROTECTED_PACKAGES:
        return {"success": False, "stderr": "Protected package"}

    _, pip_path, _ = get_user_env(req.user_id)
    timeout = req.timeout or DEFAULT_INSTALL_TIMEOUT

    try:
        r = subprocess.run(
            [pip_path, "uninstall", "-y", pkg],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {"success": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}

    except subprocess.TimeoutExpired:
        return {"success": False, "stderr": "Uninstall timed out"}


# =========================
# RUN CODE
# =========================
@app.post("/run")
def run_code(req: RunRequest):

    python_path, _, user_dir = get_user_env(req.user_id)
    timeout = req.timeout or DEFAULT_EXEC_TIMEOUT

    file_path = os.path.join(user_dir, f"{uuid.uuid4()}.py")
    with open(file_path, "w") as f:
        f.write(req.code)

    try:
        r = subprocess.run(
            [python_path, file_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {"stdout": r.stdout, "stderr": r.stderr, "exit_code": r.returncode}

    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Execution timed out"}

    finally:
        try:
            os.remove(file_path)
        except:
            pass


# =========================
# LIST LIBS
# =========================
@app.post("/libs")
def list_libs(req: LibsRequest):
    _, pip_path, _ = get_user_env(req.user_id)

    r = subprocess.run(
        [pip_path, "list", "--format=json"],
        capture_output=True,
        text=True,
        timeout=10
    )

    return {"libs": r.stdout}
    
