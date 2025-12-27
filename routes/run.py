from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import subprocess, os, uuid
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

    def stream():
        try:
            process = subprocess.Popen(
                [python_path, "-u", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in process.stdout:
                yield line

        finally:
            try:
                os.remove(file_path)
            except:
                pass

    return StreamingResponse(stream(), media_type="text/plain")
    
