from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import subprocess, os, uuid
from models import RunRequest
from utils import get_user_env

router = APIRouter()

@router.post("/run")
def run_code(req: RunRequest):

    python_path, _, user_dir = get_user_env(req.user_id)

    # 🔐 SAFE input override (NO stdin, NO blocking)
    injected_code = (
        "import builtins\n"
        "def input(prompt=''):\n"
        "    if prompt:\n"
        "        print(prompt)\n"
        "    raise Exception('INPUT_REQUIRED')\n\n"
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
                if "INPUT_REQUIRED" in line:
                    yield "❗ Input required (interactive input not supported)\n"
                    return
                yield line

        finally:
            try:
                os.remove(file_path)
            except:
                pass

    return StreamingResponse(stream(), media_type="text/plain")
