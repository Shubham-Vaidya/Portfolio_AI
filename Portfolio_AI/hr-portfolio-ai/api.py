
# ============================================================
# IMPORTS
# ============================================================
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException
)

from pydantic import BaseModel

from main import (
    ask_llm,
    create_system_message,
    model
)

from rag import (
    retrieve_context,
    retrieve_jd_context,
    index_job_description
)

from jd_parser import (
    extract_text,
    chunk_text
)


# ============================================================
# CONFIGURATION
# ============================================================

app = FastAPI(
    title="HR Portfolio AI Assistant",
    description="Candidate profile and job description assistant"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversations = {}

MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


# ============================================================
# REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):

    session_id: str
    message: str


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def home():

    return {
        "message": "HR Portfolio AI API is running"
    }


# ============================================================
# JOB DESCRIPTION UPLOAD
# ============================================================

@app.post("/upload-jd")
async def upload_jd(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):

    try:

        filename = file.filename or ""

        extension = Path(filename).suffix.lower()

        # Validate file extension
        if extension not in ALLOWED_EXTENSIONS:

            raise HTTPException(
                status_code=400,
                detail="Only PDF, DOCX and TXT files are supported."
            )

        # Read uploaded file
        file_bytes = await file.read()

        if len(file_bytes) > MAX_FILE_SIZE:

            raise HTTPException(
                status_code=413,
                detail="File size exceeds the 10 MB limit."
            )

        if not file_bytes:

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        # Extract text
        extracted_text = extract_text(
            file_bytes,
            filename
        )

        # Split text into chunks
        chunks = chunk_text(extracted_text)

        # Generate embeddings and store in Qdrant
        count = index_job_description(
            chunks,
            session_id
        )

        return {
            "message": "Job description uploaded successfully.",
            "filename": filename,
            "session_id": session_id,
            "characters_extracted": len(extracted_text),
            "chunks_indexed": count
        }

    except HTTPException:
        raise

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    finally:

        await file.close()


# ============================================================
# CHAT ENDPOINT
# ============================================================

@app.post("/chat")
def chat(chat_request: ChatRequest):

    session_id = chat_request.session_id

    # Create conversation if it doesn't exist
    if session_id not in conversations:

        conversations[session_id] = [
            create_system_message()
        ]

    messages = conversations[session_id]

    # Retrieve candidate profile information
    candidate_context = retrieve_context(
        chat_request.message,
        top_k=4
    )

    # Retrieve session-specific JD information
    jd_context = retrieve_jd_context(
        chat_request.message,
        session_id,
        top_k=5
    )

    if not candidate_context:

        candidate_context = (
            "No relevant candidate profile information found."
        )

    if not jd_context:

        jd_context = (
            "No job description has been uploaded "
            "for this session."
        )

   
    # Combine retrieved context with the current question
    enriched_message = f"""
    CANDIDATE PROFILE CONTEXT:
    {candidate_context}

    JOB DESCRIPTION CONTEXT:
    {jd_context}

    HR QUESTION:
    {chat_request.message}

    Answer the HR question using the retrieved information.
    Keep candidate facts separate from job requirements.
    """

    messages.append({
        "role": "user",
        "content": enriched_message
    })


    # Generate response
    answer = ask_llm(messages, model)

    # Store assistant response
    messages.append({
        "role": "assistant",
        "content": answer
    })

    return {
        "answer": answer
    }
