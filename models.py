from pydantic import BaseModel

class RunRequest(BaseModel):
    user_id: str
    code: str
    input: str | None = None
    timeout: int | None = None


class InstallRequest(BaseModel):
    user_id: str
    package: str
    timeout: int | None = None


class UninstallRequest(BaseModel):
    user_id: str
    package: str
    timeout: int | None = None


class LibsRequest(BaseModel):
    user_id: str
