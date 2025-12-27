import subprocess, time
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from models import InstallRequest
from utils import get_user_env
from config import DEFAULT_INSTALL_TIMEOUT

router = APIRouter()

@router.post("/install")
def install_package(req: InstallRequest):
    _, pip, _ = get_user_env(req.user_id)
    timeout = req.timeout or DEFAULT_INSTALL_TIMEOUT

    r = subprocess.run(
        [pip, "install", req.package],
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return {"success": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}


def pip_install_stream(user_id, package):
    _, pip, _ = get_user_env(user_id)
    p = subprocess.Popen(
        [pip, "install", package, "--progress-bar", "off"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    for line in iter(p.stdout.readline, ""):
        yield f"data: {line}\n\n"
    yield "data: __DONE__\n\n"


@router.get("/install/stream")
def install_stream(user_id: str = Query(...), package: str = Query(...)):
    return StreamingResponse(
        pip_install_stream(user_id, package),
        media_type="text/event-stream"
    )
