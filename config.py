import os

BASE_DIR = os.getenv("PYCODE_BASE_DIR", "/tmp/pycode_users")
DEFAULT_EXEC_TIMEOUT = int(os.getenv("PYCODE_EXEC_TIMEOUT", "5"))
DEFAULT_INSTALL_TIMEOUT = int(os.getenv("PYCODE_INSTALL_TIMEOUT", "30"))

PROTECTED_PACKAGES = {
    "pip",
    "setuptools",
    "wheel"
}

os.makedirs(BASE_DIR, exist_ok=True)
