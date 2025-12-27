import os
import subprocess
from config import BASE_DIR

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
