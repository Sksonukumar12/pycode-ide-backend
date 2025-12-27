import os, uuid, subprocess
from fastapi import APIRouter
from models import RunRequest
from utils import get_user_env
from config import DEFAULT_EXEC_TIMEOUT

router = APIRouter()

@router.post("/run")
def run_code(req: RunRequest):

    python_path, _, user_dir = get_user_env(req.user_id)
    timeout = req.timeout or DEFAULT_EXEC_TIMEOUT

    file_path = os.path.join(user_dir, f"{uuid.uuid4()}.py")
    with open(file_path, "w") as f:
        f.write(req.code)

    try:
        result = subprocess.run(
            [python_path, file_path],
            input=req.input or "",
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    finally:
        try:
            os.remove(file_path)
        except:
            pass
