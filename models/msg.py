
from pydantic import BaseModel


class MsgModel(BaseModel):
    username: str = "anon" # default username
    content: str
    timestamp: str # international timestamp
    color: str = "#11BC61" # default color