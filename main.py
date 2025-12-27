from fastapi import FastAPI
from routes import run, install, uninstall, libs

app = FastAPI()

app.include_router(run.router)
app.include_router(install.router)
app.include_router(uninstall.router)
app.include_router(libs.router)

@app.get("/")
def root():
    return {"status": "running"}
    
