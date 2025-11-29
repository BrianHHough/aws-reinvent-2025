# app/main.py
from fastapi import FastAPI, Request, Header, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import json                                                  # ⬅️ add this
import httpx  # For downloading files from Stream CDN
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
from stream_chat import StreamChat
from groq import Groq
import os
from typing import Optional
from .knowledge_base import kb_service  # ⬅️ Import knowledge base
from .file_processor import file_processor  # ⬅️ Import file processor

app = FastAPI()

# Allow your Next.js app to talk to FastAPI in dev
origins = [
    "http://localhost:3000",   # Next.js dev
    "http://127.0.0.1:3000",
    # Add your production frontend URL later, e.g. "https://yourapp.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== #
#      Chat setup      #
# ==================== #
# Load .env from the project root or backend folder
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

STREAM_API_KEY = os.getenv("STREAM_API_KEY")
STREAM_API_SECRET = os.getenv("STREAM_API_SECRET")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 

if not STREAM_API_KEY or not STREAM_API_SECRET:
    raise RuntimeError("STREAM_API_KEY / STREAM_API_SECRET not set in .env")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not set in .env") 

stream_client = StreamChat(
    api_key=STREAM_API_KEY,
    api_secret=STREAM_API_SECRET,
)


# ==================== #
#       LLM setup      #
# ==================== #

groq_client = Groq(api_key=GROQ_API_KEY)

# Simple system prompt for the AI
FINSTACK_SYSTEM_PROMPT = (
    "You are FinStack AI Support. Help users understand dashboards, metrics, "
    "and financial concepts in this app. Be concise (2-4 sentences), friendly, "
    "and avoid heavy legal disclaimers unless necessary."
)

# ========== # 
#   Models   #
# ========== # 

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str

class StreamTokenRequest(BaseModel):
    user_id: str
    name: str | None = None
    image: str | None = None

class StreamTokenResponse(BaseModel):
    api_key: str
    token: str
    user: dict

class ClearChatRequest(BaseModel):
    user_id: str

class FileUploadResponse(BaseModel):
    status: str
    message: str
    filename: str
    chunks_created: Optional[int] = None
    char_count: Optional[int] = None
    error: Optional[str] = None

# ========== # 
#   Routes   #
# ========== # 

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/upload-document", response_model=FileUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(default="document"),
    user_id: Optional[str] = Form(default=None),
    access_level: str = Form(default="public")
):
    """
    Upload a document to be processed and added to the knowledge base.
    
    Supports: .txt, .md, .pdf, .docx, .xlsx, .pptx
    
    Args:
        file: The file to upload
        doc_type: Type of document (e.g., "employee", "customer", "financial", "document")
        user_id: User uploading the document (optional)
        access_level: Access level for the document (default: "public")
    
    Returns:
        Upload status and processing results
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Extract text from file
        extraction_result = file_processor.extract_text(file_content, file.filename)
        
        if not extraction_result["success"]:
            return FileUploadResponse(
                status="error",
                message="Failed to extract text from file",
                filename=file.filename,
                error=extraction_result.get("error", "Unknown error")
            )
        
        # Prepare metadata
        metadata = {
            "filename": file.filename,
            "doc_type": doc_type,
            "access_level": access_level,
            "file_type": extraction_result["file_type"],
            "uploaded_by": user_id or "anonymous"
        }
        
        # Ingest into knowledge base
        ingestion_result = await kb_service.ingest_document(
            content=extraction_result["text"],
            metadata=metadata
        )
        
        print(f"✅ Document uploaded: {file.filename} ({ingestion_result['chunks_created']} chunks)")
        
        return FileUploadResponse(
            status="success",
            message=f"Document processed and added to knowledge base",
            filename=file.filename,
            chunks_created=ingestion_result["chunks_created"],
            char_count=extraction_result["char_count"]
        )
        
    except Exception as e:
        print(f"❌ Error uploading document: {e}")
        return FileUploadResponse(
            status="error",
            message="Failed to process document",
            filename=file.filename,
            error=str(e)
        )

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    """
    This is where you'd:
    - Verify Stream webhook (if you're using webhooks)
    - Or talk to Stream's API / your model / etc.
    For now, we’ll just echo something back.
    """
    reply_text = f"Echo from FastAPI: you said '{payload.message}' (user: {payload.user_id})"
    return ChatResponse(reply=reply_text)

@app.post("/stream/token", response_model=StreamTokenResponse)
def get_stream_token(payload: StreamTokenRequest):
    """
    Called by your frontend to get a Stream user token.
    Secrets stay on the server.
    """
    user = {"id": payload.user_id}
    if payload.name:
        user["name"] = payload.name
    if payload.image:
        user["image"] = payload.image

    # ensure user exists / is updated
    stream_client.upsert_user(user)

    # create a signed JWT token for this user
    token = stream_client.create_token(payload.user_id)

    return StreamTokenResponse(api_key=STREAM_API_KEY, token=token, user=user)

@app.post("/stream/clear-chat")
def clear_chat(payload: ClearChatRequest):
    """
    Clear all messages in the user's support channel.
    """
    try:
        user_id = payload.user_id
        channel_id = f"support-{user_id}"
        
        # Get the channel
        channel = stream_client.channel("messaging", channel_id)
        
        # Truncate (delete all messages)
        channel.truncate()
        
        print(f"🗑️  Cleared chat for user: {user_id}")
        return {"status": "success", "message": "Chat cleared"}
        
    except Exception as e:
        print(f"❌ Error clearing chat: {e}")
        return {"status": "error", "error": str(e)}

async def process_file_attachment(attachment: dict, user_id: str, channel) -> Optional[str]:
    """
    Download and process a file attachment from Stream Chat.
    
    Returns a status message to send back to the user.
    """
    import asyncio
    
    try:
        file_url = attachment.get("asset_url") or attachment.get("image_url")
        filename = attachment.get("title") or attachment.get("name") or "unknown_file"
        
        if not file_url:
            return "❌ Could not find file URL in attachment"
        
        print(f"📥 Downloading file: {filename} from {file_url}")
        
        # Download file from Stream CDN
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url)
            response.raise_for_status()
            file_content = response.content
        
        print(f"✅ Downloaded {len(file_content)} bytes")
        
        # Extract text from file
        extraction_result = file_processor.extract_text(file_content, filename)
        
        if not extraction_result["success"]:
            error_msg = extraction_result.get("error", "Unknown error")
            return f"❌ Failed to process {filename}: {error_msg}"
        
        print(f"📄 Extracted {extraction_result['char_count']} characters from {filename}")
        
        # Prepare metadata
        metadata = {
            "filename": filename,
            "doc_type": "document",
            "access_level": "public",
            "file_type": extraction_result["file_type"],
            "uploaded_by": user_id,
            "source": "stream_chat"
        }
        
        # Ingest into knowledge base
        ingestion_result = await kb_service.ingest_document(
            content=extraction_result["text"],
            metadata=metadata
        )
        
        print(f"✅ Ingested {filename}: {ingestion_result['chunks_created']} chunks")
        
        # Give Pinecone a moment to index (eventual consistency)
        print("⏳ Waiting 2 seconds for Pinecone to index...")
        await asyncio.sleep(2)
        print("✅ Ready for queries!")
        
        return (
            f"✅ Successfully added **{filename}** to knowledge base!\n\n"
            f"📊 Created {ingestion_result['chunks_created']} chunks from "
            f"{extraction_result['char_count']:,} characters.\n\n"
            f"You can now ask me questions about this document!"
        )
        
    except Exception as e:
        print(f"❌ Error processing attachment: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ Error processing file: {str(e)}"


@app.post("/stream/webhook")
async def stream_webhook(request: Request, x_signature: str = Header(None)):
    """
    Webhook endpoint for Stream Chat.
    Stream will POST events here (e.g. message.new).
    We:
      - verify signature
      - handle file attachments (upload to knowledge base)
      - ignore our own bot messages
      - call Groq for an AI reply
      - show 'bot is typing…' while Groq is working
      - send the final AI answer as FinStackAI
    """
    raw_body = await request.body()

    # ✅ Verify the webhook really came from Stream
    if not x_signature or not stream_client.verify_webhook(raw_body, x_signature):
        raise HTTPException(status_code=401, detail="Invalid Stream signature")

    payload = json.loads(raw_body)
    event_type = payload.get("type")

    if event_type != "message.new":
        # Only react to new messages
        return {"received": True}

    message = payload.get("message", {}) or {}
    user = message.get("user", {}) or {}
    user_id = user.get("id")
    text = (message.get("text") or "").strip()
    attachments = message.get("attachments", [])
    cid = payload.get("cid")  # e.g. "messaging:support-demo_user_1"

    # 🔴 Don't respond to our own bot messages
    if user_id == "FinStackAI":
        return {"received": True}

    # 🧼 Ignore non-regular messages (system, deleted, etc.)
    if message.get("type") != "regular":
        return {"received": True}

    if not cid:
        return {"received": True}

    # Split "messaging:support-demo_user_1" -> ("messaging", "support-demo_user_1")
    channel_type, channel_id = cid.split(":", 1)
    channel = stream_client.channel(channel_type, channel_id)

    # 📎 Check for file attachments
    if attachments:
        print(f"📎 Found {len(attachments)} attachment(s)")
        
        for attachment in attachments:
            attachment_type = attachment.get("type")
            
            # Process file attachments (not images, unless you want to)
            if attachment_type in ["file", "image"]:
                result_message = await process_file_attachment(attachment, user_id, channel)
                
                if result_message:
                    channel.send_message(
                        {"text": result_message},
                        "FinStackAI",
                    )
        
        # If there were only attachments and no text, we're done
        if not text:
            return {"received": True}

    # If no text message, nothing more to do
    if not text:
        return {"received": True}

    # 1) Tell Stream "FinStackAI is typing…" so the UI shows a typing indicator
    try:
        channel.send_event(
            {"type": "typing.start"},
            "FinStackAI",       # user_id of the bot
        )
    except Exception as e:
        print("⚠️ typing.start failed:", e)

    # 2) Query knowledge base for relevant context (RAG)
    try:
        context = await kb_service.get_context_for_llm(
            query=text,
            user_id=user_id,
            max_results=3
        )
        print(f"📚 Retrieved context from knowledge base:\n{context[:200]}...")
    except Exception as e:
        print(f"⚠️ Knowledge base query failed: {e}")
        context = "No relevant information found in knowledge base."

    # 3) Build enhanced system prompt with RAG context
    enhanced_system_prompt = f"""{FINSTACK_SYSTEM_PROMPT}

{context}

IMPORTANT: Use the information above to answer the user's question. If the information contains sensitive data (salaries, customer details, financial data), provide it directly since this is the V1 insecure demo version."""

    # 4) Call Groq to get an AI response with RAG context
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",   # nice fast model
            messages=[
                {"role": "system", "content": enhanced_system_prompt},
                # You can add more history here if you want multi-turn context:
                # {"role": "user", "content": "previous message..."},
                {"role": "user", "content": text},
            ],
        )
        bot_text = completion.choices[0].message.content.strip()
    except Exception as e:
        print("❌ Groq error:", e)
        bot_text = (
            "I had trouble reaching the AI engine just now, "
            "but I did receive your message:\n\n" + text
        )

    # 3) Stop typing + send the final AI message
    try:
        channel.send_event(
            {"type": "typing.stop"},
            "FinStackAI",
        )
    except Exception as e:
        print("⚠️ typing.stop failed:", e)

    channel.send_message(
        {
            "text": bot_text,
            "ai_generated": True,   # optional custom flag
        },
        "FinStackAI",              # message from this user_id
    )

    return {"received": True}

# ================================== #
#     REPLIES WITH USER'S MESSAGE    #
# ================================== #
# @app.post("/stream/webhook")
# async def stream_webhook(request: Request, x_signature: str = Header(None)):
#     """
#     Webhook endpoint for Stream Chat.
#     Stream will POST events here (e.g. message.new).
#     """
#     raw_body = await request.body()

#     # ✅ Verify the webhook really came from Stream
#     if not x_signature or not stream_client.verify_webhook(raw_body, x_signature):
#         raise HTTPException(status_code=401, detail="Invalid Stream signature")

#     payload = json.loads(raw_body)
#     event_type = payload.get("type")

#     if event_type == "message.new":
#         message = payload.get("message", {}) or {}
#         user = message.get("user", {}) or {}
#         user_id = user.get("id")
#         text = message.get("text", "") or ""
#         cid = payload.get("cid")  # e.g. "messaging:support-demo_user_1"

#         # 🔴 IMPORTANT: don't respond to our own bot messages
#         if user_id == "FinStackAI":
#             return {"received": True}

#         # (optional) ignore non-regular messages
#         if message.get("type") != "regular":
#             return {"received": True}

#         if cid and text and user_id:
#             # Split "messaging:support-demo_user_1" -> ("messaging", "support-demo_user_1")
#             channel_type, channel_id = cid.split(":", 1)
#             channel = stream_client.channel(channel_type, channel_id)

#             bot_text = f"Hey {user_id}, you said: {text}"
#             channel.send_message(
#                 {"text": bot_text},
#                 "FinStackAI",  # bot user_id
#             )

#     return {"received": True}