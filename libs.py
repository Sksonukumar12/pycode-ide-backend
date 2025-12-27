import subprocess
from fastapi import APIRouter
from models import LibsRequest
from utils import get_user_env

router = APIRouter()

@router.post("/libs")
def list_libs(req: LibsRequest):
    _, pip, _ = get_user_env(req.user_id)
    r = subprocess.run(
        [pip, "list", "--format=json"],
        capture_output=True,
        text=True
    )
    return {"libs": r.stdout}
