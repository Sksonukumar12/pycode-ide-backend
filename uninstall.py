import subprocess
from fastapi import APIRouter
from models import UninstallRequest
from utils import get_user_env
from config import DEFAULT_INSTALL_TIMEOUT, PROTECTED_PACKAGES

router = APIRouter()

@router.post("/uninstall")
def uninstall(req: UninstallRequest):
    pkg = req.package.lower()
    if pkg in PROTECTED_PACKAGES:
        return {"success": False, "stderr": "Protected package"}

    _, pip, _ = get_user_env(req.user_id)
    r = subprocess.run(
        [pip, "uninstall", "-y", pkg],
        capture_output=True,
        text=True,
        timeout=req.timeout or DEFAULT_INSTALL_TIMEOUT
    )
    return {"success": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}
