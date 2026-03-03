from sqlmodel import SQLModel


# Simple message response model used across the API
class Message(SQLModel):
    message: str
