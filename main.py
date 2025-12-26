from fastapi import FastAPI, Query  
from fastapi.responses import StreamingResponse  
from pydantic import BaseModel  
import subprocess  
import tempfile  
import os  
import time  
  
app = FastAPI()  
  
BASE_DIR = "/tmp/pycode_users"  
os.makedirs(BASE_DIR, exist_ok=True)  
  
EXEC_TIMEOUT = 5  
INSTALL_TIMEOUT = 30  
  
  
class RunRequest(BaseModel):  
    user_id: str  
    code: str  
  
  
class InstallRequest(BaseModel):  
    user_id: str  
    package: str  
  
  
class LibsRequest(BaseModel):  
    user_id: str  
  
  
def get_user_env(user_id: str):  
    user_dir = os.path.join(BASE_DIR, user_id)  
    venv_dir = os.path.join(user_dir, "venv")  
  
    if not os.path.exists(venv_dir):  
        os.makedirs(user_dir, exist_ok=True)  
        subprocess.run(  
            ["python3", "-m", "venv", venv_dir],  
            check=True  
        )  
  
    python_path = os.path.join(venv_dir, "bin", "python")  
    pip_path = os.path.join(venv_dir, "bin", "pip")  
  
    return python_path, pip_path  
  
  
@app.get("/")  
def root():  
    return {"status": "PyCode IDE backend running"}  
  
  
# ---------------- INSTALL (NORMAL – KEEP) ----------------  
@app.post("/install")  
def install_package(req: InstallRequest):  
    _, pip_path = get_user_env(req.user_id)  
  
    try:  
        result = subprocess.run(  
            [pip_path, "install", req.package],  
            capture_output=True,  
            text=True,  
            timeout=INSTALL_TIMEOUT  
        )  
  
        output = (result.stdout or "") + (result.stderr or "")  
  
        return {  
            "success": result.returncode == 0,  
            "output": output  
        }  
  
    except subprocess.TimeoutExpired:  
        return {"success": False, "output": "Installation timed out"}  
  
    except Exception as e:  
        return {"success": False, "output": str(e)}  
  
  
# ---------------- INSTALL (LIVE STREAM – FIXED) ----------------  
def pip_install_stream(user_id: str, package: str):  
    _, pip_path = get_user_env(user_id)  
  
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
        bufsize=1,  
        universal_newlines=True  
    )  
  
    last_ping = time.time()  
  
    for line in iter(process.stdout.readline, ""):  
        yield f"data: {line}\n\n"  
  
        # keep-alive ping every 1 second (Railway fix)  
        if time.time() - last_ping > 1:  
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
  
  
# ---------------- RUN CODE ----------------  
@app.post("/run")  
def run_code(req: RunRequest):  
    python_path, _ = get_user_env(req.user_id)  
    user_dir = os.path.join(BASE_DIR, req.user_id)  
  
    with tempfile.NamedTemporaryFile(  
        suffix=".py",  
        delete=False,  
        dir=user_dir  
    ) as f:  
        f.write(req.code.encode())  
        file_path = f.name  
  
    try:  
        result = subprocess.run(  
            [python_path, file_path],  
            capture_output=True,  
            text=True,  
            timeout=EXEC_TIMEOUT  
        )  
  
        return {  
            "stdout": result.stdout,  
            "stderr": result.stderr  
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
  
  
# ---------------- INSTALLED LIBS ----------------  
@app.post("/libs")  
def list_installed_libs(req: LibsRequest):  
    _, pip_path = get_user_env(req.user_id)  
  
    try:  
        result = subprocess.run(  
            [pip_path, "list", "--format=freeze"],  
            capture_output=True,  
            text=True,  
            timeout=10  
        )  
  
        return {"output": result.stdout}  
  
    except Exception as e:  
        return {"output": str(e)}  
