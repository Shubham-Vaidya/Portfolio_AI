from main import ask_llm
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):   
    message: str

@app.post("/chat")
def chat(chat_request: ChatRequest):
    return {"answer": ask_llm([{"role": "user", "content": chat_request.message}], model="openai/gpt-oss-120b")}


