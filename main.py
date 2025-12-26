from fastapi import FastAPI
from pydantic import BaseModel
import subprocess, tempfile

app = FastAPI()

class CodeRequest(BaseModel):
    code: str

@app.get("/")
def root():
    return {"status": "PyCode IDE backend running"}

@app.post("/run")
def run_code(req: CodeRequest):
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        f.write(req.code.encode())
        file = f.name

    try:
        result = subprocess.run(
            ["python3", file],
            capture_output=True,
            text=True,
            timeout=5
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {"stderr": str(e)}
