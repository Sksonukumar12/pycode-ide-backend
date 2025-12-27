from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import subprocess, os, uuid, tempfile
from models import RunRequest
from utils import get_user_env
from config import DEFAULT_EXEC_TIMEOUT

router = APIRouter()

@router.post("/run")
def run_code(req: RunRequest):

    python_path, _, user_dir = get_user_env(req.user_id)
    timeout = req.timeout or DEFAULT_EXEC_TIMEOUT

    # Inject input wrapper
    injected_code = f"""
import builtins
_original_input = input

def custom_input(prompt=""):
    if prompt:
        print(prompt, flush=True)
    print("__INPUT_REQUIRED__", flush=True)
    return _original_input()

builtins.input = custom_input

{req.code}
"""

    file_path = os.path.join(user_dir, f"{uuid.uuid4()}.py")
    with open(file_path, "w") as f:
        f.write(injected_code)

    def stream():
        process = None
        try:
            process = subprocess.Popen(
                [python_path, "-u", file_path],
                stdin=subprocess.PIPE,              # ✅ IMPORTANT
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in process.stdout:
                yield line

        finally:
            if process:
                process.kill()
            try:
                os.remove(file_path)
            except:
                pass

    return StreamingResponse(stream(), media_type="text/plain")
   Injectnjectnject
