from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import subprocess, os, uuid, sys
from models import RunRequest
from utils import get_user_env

router = APIRouter()

@router.post("/run")
def run_code(req: RunRequest):   # 🔥 IMPORTANT

    python_path, _, user_dir = get_user_env(req.user_id)

    injected_code = (
        "import sys\n"
        "def input(prompt=''):\n"
        "    if prompt:\n"
        "        print(prompt)\n"
        "    print('❗ INPUT_REQUIRED')\n"
        "    sys.exit(0)\n\n"
        + req.code
    )

    file_path = os.path.join(user_dir, f"{uuid.uuid4()}.py")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(injected_code)

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
