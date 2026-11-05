
from main import ask_llm, create_system_message, model
from profile import profile
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Store conversation history for each session
conversations = {}


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.post("/chat")
def chat(chat_request: ChatRequest):

    # Step 1: Create a new conversation if session doesn't exist
    if chat_request.session_id not in conversations:
        conversations[chat_request.session_id] = [
            create_system_message(profile)
        ]

    # Step 2: Retrieve existing conversation
    messages = conversations[chat_request.session_id]

    # Step 3: Append the user's message
    messages.append({
        "role": "user",
        "content": chat_request.message
    })

    # Step 4: Get response from LLM
    answer = ask_llm(messages, model)

    # Step 5: Store assistant's response
    messages.append({
        "role": "assistant",
        "content": answer
    })

    # Step 6: Return response
    return {"answer": answer}
