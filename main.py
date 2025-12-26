from fastapi import FastAPI, Query, Header    
from fastapi.responses import StreamingResponse    
from pydantic import BaseModel    
import subprocess    
import tempfile    
import os    
import time    
import uuid    
    
app = FastAPI()    
    
# =========================    
# DYNAMIC CONFIG (ENV BASED)    
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
    
    
class LibsRequest(BaseModel):    
    user_id: str    
    
    
# =========================    
# UTILITIES    
# =========================    
def get_user_env(user_id: str):    
    safe_user = "".join(c for c in user_id if c.isalnum() or c in "_-")    
    user_dir = os.path.join(BASE_DIR, safe_user)    
    venv_dir = os.path.join(user_dir, "venv")    
    
    if not os.path.exists(venv_dir):    
        os.makedirs(user_dir, exist_ok=True)    
        subprocess.run(    
            ["python3", "-m", "venv", venv_dir],    
            check=True    
        )    
    
    python_path = os.path.join(venv_dir, "bin", "python")    
    pip_path = os.path.join(venv_dir, "bin", "pip")    
    
    return python_path, pip_path, user_dir    
    
    
# =========================    
# ROOT    
# =========================    
@app.get("/")    
def root():    
    return {    
        "status": "running",    
        "base_dir": BASE_DIR    
    }    
    
    
# =========================    
# INSTALL (NORMAL – DYNAMIC)    
# =========================    
@app.post("/install")    
def install_package(req: InstallRequest):    
    
    _, pip_path, _ = get_user_env(req.user_id)    
    timeout = req.timeout or DEFAULT_INSTALL_TIMEOUT    
    
    try:    
        result = subprocess.run(    
            [pip_path, "install", req.package],    
            capture_output=True,    
            text=True,    
            timeout=timeout    
        )    
    
        return {    
            "success": result.returncode == 0,    
            "stdout": result.stdout,    
            "stderr": result.stderr    
        }    
    
    except subprocess.TimeoutExpired:    
        return {"success": False, "stderr": "Installation timed out"}    
    
    except Exception as e:    
        return {"success": False, "stderr": str(e)}    
    
    
# =========================    
# INSTALL (LIVE STREAM – DYNAMIC)    
# =========================    
def pip_install_stream(user_id: str, package: str):    
    
    _, pip_path, _ = get_user_env(user_id)    
    
    process = subprocess.Popen(    
        [    
            pip_path,    
            "install",    
            package,    
            "--progress-bar",    
            "off"    
        ],    
        stdout=subprocess.PIPE,    
        stderr=subprocess.STDOUT,    
        text=True,    
        bufsize=1    
    )    
    
    last_ping = time.time()    
    
    for line in iter(process.stdout.readline, ""):    
        yield f"data: {line}\n\n"    
    
        if time.time() - last_ping >= 1:    
            yield "data: \n\n"    
            last_ping = time.time()    
    
    yield "data: __DONE__\n\n"    
    
    
@app.get("/install/stream")    
def install_stream(    
    user_id: str = Query(...),    
    package: str = Query(...)    
):    
    return StreamingResponse(    
        pip_install_stream(user_id, package),    
        media_type="text/event-stream",    
        headers={    
            "Cache-Control": "no-cache",    
            "Connection": "keep-alive",    
            "X-Accel-Buffering": "no"    
        }    
    )    
    
    
# =========================    
# RUN CODE (DYNAMIC)    
# =========================    
@app.post("/run")    
def run_code(req: RunRequest):    
    
    python_path, _, user_dir = get_user_env(req.user_id)    
    timeout = req.timeout or DEFAULT_EXEC_TIMEOUT    
    
    file_id = str(uuid.uuid4())    
    file_path = os.path.join(user_dir, f"{file_id}.py")    
    
    with open(file_path, "w") as f:    
        f.write(req.code)    
    
    try:    
        result = subprocess.run(    
            [python_path, file_path],    
            capture_output=True,    
            text=True,    
            timeout=timeout    
        )    
    
        return {    
            "stdout": result.stdout,    
            "stderr": result.stderr,    
            "exit_code": result.returncode    
        }    
    
    except subprocess.TimeoutExpired:    
        return {"stdout": "", "stderr": "Execution timed out"}    
    
    except Exception as e:    
        return {"stdout": "", "stderr": str(e)}    
    
    finally:    
        try:    
            os.remove(file_path)    
        except:    
            pass    
    
    
# =========================    
# INSTALLED LIBS (DYNAMIC)    
# =========================    
@app.post("/libs")    
def list_installed_libs(req: LibsRequest):    
    
    _, pip_path, _ = get_user_env(req.user_id)    
    
    try:    
        result = subprocess.run(    
            [pip_path, "list", "--format=json"],    
            capture_output=True,    
            text=True,    
            timeout=10    
        )    
    
        return {    
            "libs": result.stdout    
        }    
    
    except Exception as e:    
        return {"error": str(e)}
